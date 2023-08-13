#!/usr/bin/env python
from __future__ import unicode_literals
import os
import re
import sys
import unicodedata
import argparse
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor


try:
    # Python3
    from urllib.request import Request, build_opener, HTTPCookieProcessor
    from html.parser import HTMLParser
    from http.cookiejar import CookieJar
except ImportError:
    # Python2
    from HTMLParser import HTMLParser
    from urllib2 import Request, build_opener, HTTPCookieProcessor
    from cookielib import CookieJar

try:
    from html import unescape
except ImportError:
    html = HTMLParser()
    unescape = html.unescape

ITEM_URL = "https://drive.google.com/open?id={id}"
FILE_URL = "https://docs.google.com/uc?export=download&id={id}&confirm={confirm}"
FOLDER_URL = "https://drive.google.com/embeddedfolderview?id={id}#list"
CHUNKSIZE = 64 * 1024
USER_AGENT = "Mozilla/5.0"

ID_PATTERNS = [
    re.compile("/file/d/([0-9A-Za-z_-]{10,})(?:/|$)", re.IGNORECASE),
    re.compile("/folders/([0-9A-Za-z_-]{10,})(?:/|$)", re.IGNORECASE),
    re.compile("id=([0-9A-Za-z_-]{10,})(?:&|$)", re.IGNORECASE),
    re.compile("([0-9A-Za-z_-]{10,})", re.IGNORECASE),
]
FOLDER_PATTERN = re.compile(
    '<a href="(https://drive.google.com/.*?)".*?<div class="flip-entry-title">(.*?)</div>.*?<div class="flip-entry-last-modified"><div>(.*?)</div>',
    re.DOTALL | re.IGNORECASE,
)
CONFIRM_PATTERN = re.compile(
    b"confirm=([0-9A-Za-z_-]+)", re.IGNORECASE
)
FILENAME_PATTERN = re.compile('filename="(.*?)"', re.IGNORECASE)


def output(text):
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.write(text.encode("utf8"))


# Big thanks to leo_wallentin for below sanitize function (modified slightly for this script)
# https://gitlab.com/jplusplus/sanitize-filename/-/blob/master/sanitize_filename/sanitize_filename.py
def sanitize(filename):
    blacklist = ["\\", "/", ":", "*", "?", '"', "<", ">", "|", "\0"]
    reserved = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]

    filename = unescape(filename).encode("utf8").decode("utf8")
    filename = unicodedata.normalize("NFKD", filename)

    filename = "".join(c for c in filename if c not in blacklist)
    filename = "".join(c for c in filename if 31 < ord(c))
    filename = filename.rstrip(". ")
    filename = filename.strip()

    if all([x == "." for x in filename]):
        filename = "_" + filename
    if filename in reserved:
        filename = "_" + filename
    if len(filename) == 0:
        filename = "_"
    if len(filename) > 255:
        parts = re.split(r"/|\\", filename)[-1].split(".")
        if len(parts) > 1:
            ext = "." + parts.pop()
            filename = filename[: -len(ext)]
        else:
            ext = ""
        if filename == "":
            filename = "_"
        if len(ext) > 254:
            ext = ext[254:]
        maxl = 255 - len(ext)
        filename = filename[:maxl]
        filename = filename + ext
        filename = filename.rstrip(". ")
        if len(filename) == 0:
            filename = "_"

    return filename


def url_to_id(url):
    for pattern in ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)

    logging.error("Unable to get ID from {}".format(url))
    sys.exit(1)


class GDriveDL(object):
    def __init__(self, quiet=False, overwrite=False, mtimes=False):
        self._quiet = quiet
        self._overwrite = overwrite
        self._mtimes = mtimes
        self._create_empty_dirs = True
        self._opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self._processed = []

    @contextmanager
    def _request(self, url):
        logging.debug("Requesting: {}".format(url))
        req = Request(url, headers={"User-Agent": USER_AGENT})

        f = self._opener.open(req)
        try:
            yield f
        finally:
            f.close()

    def process_url(self, url, directory, filename=None):
        id = url_to_id(url)
        url = url.lower()

        if "://" not in url:
            with self._request(ITEM_URL.format(id=id)) as resp:
                url = resp.geturl()

        if "/file/" in url or "/uc?" in url:
            self.process_file(id, directory, filename=filename)
        elif "/folders/" in url:
            if filename:
                logging.warning("Ignoring --output-document option for folder download")
            self.process_folder(id, directory)
        else:
            logging.error("That id {} returned an unknown url {}".format(id, url))
            sys.exit(1)

    def process_folder(self, id, directory):
        if id in self._processed:
            logging.debug('Skipping already processed folder: {}'.format(id))
            return

        self._processed.append(id)
        with self._request(FOLDER_URL.format(id=id)) as resp:
            html = resp.read().decode("utf-8")

        matches = re.findall(FOLDER_PATTERN, html)

        if not matches and "ServiceLogin" in html:
            logging.error("Folder: {} does not have link sharing enabled".format(id))
            sys.exit(1)

        with ThreadPoolExecutor() as executor:
            for match in matches:
                url, item_name, modified = match
                id = url_to_id(url)

                if "/file/" in url.lower():
                    executor.submit(
                        self.process_file,
                        id,
                        directory,
                        filename=sanitize(item_name),
                        modified=modified
                    )
                elif "/folders/" in url.lower():
                    executor.submit(
                        self.process_folder,
                        id,
                        os.path.join(directory, sanitize(item_name))
                    )

        if self._create_empty_dirs and not os.path.exists(directory):
            os.makedirs(directory)
            logging.info("Directory: {directory} [Created]".format(directory=directory))

    def _get_modified(self, modified):
        if not modified or not self._mtimes:
            return None

        try:
            if ":" in modified:
                hour, minute = modified.lower().split(":")
                if "pm" in minute:
                    hour = int(hour) + 12
                hour = int(hour)+7  # modified is UTC-7 so +7 to utc time
                minute = minute.split(" ")[0]
                now = datetime.utcnow().replace(hour=0, minute=int(minute), second=0, microsecond=0)
                modified = now + timedelta(hours=hour)
            elif "/" in modified:
                modified = datetime.strptime(modified, "%m/%d/%y")
            else:
                now = datetime.utcnow()
                modified = datetime.strptime(modified, "%b %d")
                modified = modified.replace(year=now.year)
        except:
            logging.debug("Failed to convert mtime: {}".format(modified))
            return None

        return int((modified - datetime(1970, 1, 1)).total_seconds())

    def _set_modified(self, file_path, timestamp):
        if not timestamp:
            return

        try:
            os.utime(file_path, (timestamp, timestamp))
        except:
            logging.debug("Failed to set mtime")

    def _exists(self, file_path, modified):
        if self._overwrite or not os.path.exists(file_path):
            return False

        if modified:
            try:
                return int(os.path.getmtime(file_path)) == modified
            except:
                logging.debug("Failed to get mtime")

        return True

    def process_file(self, id, directory, filename=None, modified=None, confirm=""):
        file_path = None
        modified_ts = self._get_modified(modified)

        if filename:
            file_path = (
                filename
                if os.path.isabs(filename)
                else os.path.join(directory, filename)
            )
            if self._exists(file_path, modified_ts):
                logging.info("{file_path} [Exists]".format(file_path=file_path))
                return

        with self._request(FILE_URL.format(id=id, confirm=confirm)) as resp:
            if "ServiceLogin" in resp.url:
                logging.error("File: {} does not have link sharing enabled".format(id))
                sys.exit(1)

            content_disposition = resp.headers.get("content-disposition")
            if not content_disposition:
                if confirm:
                    logging.error("content-disposition not found and confirm={} did not work".format(confirm))
                    sys.exit(1)

                page = resp.read(CHUNKSIZE)
                confirm = CONFIRM_PATTERN.search(page)
                if confirm:
                    return self.process_file(
                        id, directory, filename=filename, modified=modified, confirm=confirm.group(1)
                    )
                elif b"Google Drive - Quota exceeded" in page:
                    logging.error("Quota exceeded for this file")
                else:
                    # Try confirm=t
                    return self.process_file(
                        id, directory, filename=filename, modified=modified, confirm='t'
                    )

            if not file_path:
                filename = FILENAME_PATTERN.search(content_disposition).group(1)
                file_path = os.path.join(directory, sanitize(filename))
                if self._exists(file_path, modified_ts):
                    logging.info("{file_path} [Exists]".format(file_path=file_path))
                    return

            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                logging.info(
                    "Directory: {directory} [Created]".format(directory=directory)
                )

            try:
                with open(file_path, "wb") as f:
                    dl = 0
                    last_out = 0
                    while True:
                        chunk = resp.read(CHUNKSIZE)
                        if not chunk:
                            break

                        if (
                            b"Too many users have viewed or downloaded this file recently"
                            in chunk
                        ):
                            logging.error("Quota exceeded for this file")
                            sys.exit(1)

                        dl += len(chunk)
                        f.write(chunk)
                        if not self._quiet and (
                            not last_out or dl - last_out > 1048576
                        ):
                            output(
                                "\r{} {:.2f}MB".format(
                                    file_path,
                                    dl / 1024 / 1024,
                                )
                            )
                            last_out = dl
                            sys.stdout.flush()
            except:
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise
            else:
                self._set_modified(file_path, modified_ts)

        if not self._quiet:
            output("\n")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Download Google Drive files & folders"
    )
    parser.add_argument("url", help="Shared Google Drive URL(s)", nargs="*")
    parser.add_argument(
        "-P",
        "--directory-prefix",
        default=".",
        help="Output directory (default is current directory)",
    )
    parser.add_argument(
        "-O",
        "--output-document",
        help="Output filename. Defaults to the GDrive filename. Only valid when downloading a single file.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="Disable console output",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--mtimes",
        help="Try use modified times to check for changed files",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Debug level logging",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--urlfile",
        help="Text file containing Google Drive URLS to download (one per line)",
    )
    args = parser.parse_args(args)

    if args.debug:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.WARN
    else:
        level = logging.INFO

    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)

    if args.output_document and len(args.url) > 1:
        logging.warning("Ignoring --output-document option for multiple url download")
        args.output_document = None

    gdrive = GDriveDL(
        quiet=args.quiet, overwrite=args.output_document is not None, mtimes=args.mtimes
    )

    if args.urlfile:
        with open(args.urlfile, 'r') as f:
            args.url.extend(f.readlines())

    args.url = [x.strip() for x in args.url if x.strip()]
    if len(args.url) > 1:
        logging.info('Processing {} urls'.format(len(args.url)))

    for url in args.url:
        gdrive.process_url(
            url, directory=args.directory_prefix, filename=args.output_document
        )

if __name__ == "__main__":
    main()
