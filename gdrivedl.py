#!/usr/bin/env python
from __future__ import unicode_literals
import json
import os
import re
import sys
import unicodedata
import argparse
import logging

try:
    #Python3
    from urllib.request import Request, urlopen
except ImportError:
    #Python2
    from urllib2 import Request, urlopen

ITEM_URL = 'https://drive.google.com/open?id={id}'
FILE_URL = 'https://docs.google.com/uc?export=download&id={id}&confirm={confirm}'
FOLDER_URL = 'https://drive.google.com/drive/folders/{id}'

ID_PATTERNS = [
    re.compile('/file/d/([0-9A-Za-z_-]{10,})(?:/|$)', re.IGNORECASE),
    re.compile('id=([0-9A-Za-z_-]{10,})(?:&|$)', re.IGNORECASE),
    re.compile('([0-9A-Za-z_-]{10,})', re.IGNORECASE)
]
FILE_PATTERN = re.compile("itemJson: (\[.*?)};</script>",
                          re.DOTALL | re.IGNORECASE)
FOLDER_PATTERN = re.compile("window\['_DRIVE_ivd'\] = '(.*?)';",
                            re.DOTALL | re.IGNORECASE)
CONFIRM_PATTERN = re.compile("download_warning[0-9A-Za-z_-]+=([0-9A-Za-z_-]+);",
                             re.IGNORECASE)
FOLDER_TYPE = 'application/vnd.google-apps.folder'

def output(text):
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.write(text.encode('utf8'))

# Big thanks to leo_wallentin for below sanitize function (modified slightly for this script)
# https://gitlab.com/jplusplus/sanitize-filename/-/blob/master/sanitize_filename/sanitize_filename.py
def sanitize(filename):
    blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
    reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ]

    filename = "".join(c for c in filename if c not in blacklist)
    filename = "".join(c for c in filename if 31 < ord(c))
    filename = unicodedata.normalize("NFKD", filename)
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
            filename = filename[:-len(ext)]
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

class GDriveDL(object):
    def __init__(self, quiet=False, overwrite=False):
        self._quiet = quiet
        self._overwrite = overwrite

    def process_item(self, id, directory, filename=None):
        url = ITEM_URL.format(id=id)
        resp = urlopen(url)
        url = resp.geturl()
        html = resp.read().decode('utf-8')

        if '/file/' in url:
            match = FILE_PATTERN.search(html)
            data = match.group(1).replace('\/', '/')
            data = data.replace(r'\x5b', '[').replace(r'\x22', '"').replace(r'\x5d', ']').replace(r'\n','')
            data = json.loads(data)

            file_size = int(data[25][2])
            if filename is None:
                file_path = os.path.join(directory, sanitize(data[1]))
            else:
                file_path = filename if os.path.isabs(filename) else os.path.join(directory, filename)
                self._overwrite = True

            if not os.path.exists(directory):
                os.mkdir(directory)
                logging.info('Directory: {directory} [Created]'.format(directory=directory))

            self.process_file(id, file_path, file_size)
        elif '/folders/' in url:
            if filename:
                logging.warn("Ignoring --output-document option for folder download")
            self.process_folder(id, directory, html=html)
        elif 'ServiceLogin' in url:
            logging.error('Id {} does not have link sharing enabled'.format(id))
            sys.exit(1)
        else:
            logging.error('That id {} returned an unknown url'.format(id))
            sys.exit(1)


    def process_folder(self, id, directory, html=None):
        if not html:
            url = FOLDER_URL.format(id=id)
            html = urlopen(url).read().decode('utf-8')

        match = FOLDER_PATTERN.search(html)
        data = match.group(1).replace('\/', '/')
        data = data.replace(r'\x5b', '[').replace(r'\x22', '"').replace(r'\x5d', ']').replace(r'\n','')
        data = json.loads(data)

        if not os.path.exists(directory):
            os.mkdir(directory)
            logging.info('Directory: {directory} [Created]'.format(directory=directory))

        if not data[0]:
            return

        for item in sorted(data[0], key=lambda i: i[3] == FOLDER_TYPE):
            item_id = item[0]
            item_name = sanitize(item[2])
            item_type = item[3]
            item_size = item[13]
            item_path = os.path.join(directory, item_name)

            if item_type == FOLDER_TYPE:
                self.process_folder(item_id, item_path)
            else:
                self.process_file(item_id, item_path, int(item_size))


    def process_file(self, id, file_path, file_size, confirm='', cookies=''):
        if not self._overwrite and (os.path.exists(file_path) and os.path.getsize(file_path) == file_size):
            logging.info('{file_path} [Exists]'.format(file_path=file_path))
            return

        url = FILE_URL.format(id=id, confirm=confirm)
        req = Request(url, headers={'Cookie': cookies,
                                    'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req)
        cookies = resp.headers.get('Set-Cookie') or ''

        if not confirm and 'download_warning' in cookies:
            confirm = CONFIRM_PATTERN.search(cookies)
            return self.process_file(id, file_path, file_size, confirm.group(1), cookies)

        if not self._quiet:
            output(file_path + '\n')

        try:
            with open(file_path, 'wb') as f:
                dl = 0
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break

                    if b'Too many users have viewed or downloaded this file recently' in chunk:
                        logging.error('Quota exceeded for this file')
                        sys.exit(1)

                    dl += len(chunk)
                    f.write(chunk)
                    if not self._quiet:
                        done = int(50 * dl / file_size)
                        output("\r[{}{}] {:.2f}MB/{:.2f}MB".format(
                            '=' * done,
                            ' ' *
                            (50 - done),
                            dl / 1024 / 1024,
                            file_size / 1024 / 1024
                        ))
                        sys.stdout.flush()
        except:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

        if not self._quiet:
            output('\n')


def main(args=None):
    parser = argparse.ArgumentParser(description='Download Google Drive files & folders')
    parser.add_argument("url", help="Shared Google Drive URL")
    parser.add_argument("-P", "--directory-prefix", default='.', help="Output directory (default is current directory)")
    parser.add_argument("-O", "--output-document", help="Output filename. Defaults to the GDrive filename. Not valid when downloading folders")
    parser.add_argument("-q", "--quiet", help="Disable console output",
        default=False, action="store_true")
    args = parser.parse_args(args)

    if args.quiet:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARN)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    url = args.url
    id = ''

    for pattern in ID_PATTERNS:
        match = pattern.search(url)
        if match:
            id = match.group(1)
            break

    if not id:
        logging.error('Unable to get ID from {}'.format(url))
        sys.exit(1)

    gdrive = GDriveDL(quiet=args.quiet)
    gdrive.process_item(id, directory=args.directory_prefix, filename=args.output_document)


if __name__ == "__main__":
    main()

