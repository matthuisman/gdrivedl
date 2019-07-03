import sys
import re
import json
import os

import urllib.request

ITEM_URL        = 'https://drive.google.com/open?id={id}'
FILE_URL        = 'https://docs.google.com/uc?export=download&id={id}&confirm={confirm}'
FOLDER_URL      = 'https://drive.google.com/drive/folders/{id}'

ID_PATTERNS     = [
    re.compile('/file/d/([0-9A-Za-z_-]{33,})(?:/|$)', re.IGNORECASE), 
    re.compile('id=([0-9A-Za-z_-]{33,})(?:&|$)', re.IGNORECASE), 
    re.compile('([0-9A-Za-z_-]{33,})', re.IGNORECASE)
]
FILE_PATTERN    = re.compile("itemJson: (\[.*?);</script>", re.DOTALL|re.IGNORECASE)
FOLDER_PATTERN  = re.compile("window\['_DRIVE_ivd'\] = '(.*?)';", re.DOTALL|re.IGNORECASE)
CONFIRM_PATTERN = re.compile("download_warning[0-9A-Za-z_-]+=([0-9A-Za-z_-]+);", re.IGNORECASE)

def process_item(id, directory):
    url = ITEM_URL.format(id=id)
    
    r    = urllib.request.urlopen(url)
    url  = r.geturl()
    text = r.read().decode('utf-8')

    if '/file/' in url:
        match = FILE_PATTERN.search(text)
        data  = match.group(1).replace('\/', '/').rstrip('}').strip()
        data  = data.encode().decode('unicode_escape')
        data  = json.loads(data)
        
        file_name = data[1]
        file_size = int(data[25][2])
        file_path = os.path.join(directory, file_name)

        process_file(id, file_path, file_size)

    elif '/folders/' in url:
        process_folder(id, directory, html=text)

def process_folder(id, directory, html=None):    
    if not html:
        url  = FOLDER_URL.format(id=id)
        html = urllib.request.urlopen(url).read().decode('utf-8')

    match = FOLDER_PATTERN.search(html)
    data = match.group(1).replace('\/', '/')
    data = data.encode().decode('unicode_escape')
    data = json.loads(data)

    if not data[0]:
        #empty folder
        return

    if not os.path.exists(directory):
        os.mkdir(directory)

    for item in data[0]:
        item_id   = item[0]
        item_name = item[2]
        item_type = item[3]
        item_size = item[13]
        item_path = os.path.join(directory, item_name)
        
        if item_type == 'application/vnd.google-apps.folder':
            process_folder(item_id, item_path)
        else:
            process_file(item_id, item_path, int(item_size))
            sys.stdout.write('\n')

def process_file(id, file_path, file_size, confirm='', cookies=''):
    url = FILE_URL.format(id=id, confirm=confirm)

    req      = urllib.request.Request(url, headers={'Cookie': cookies})
    response = urllib.request.urlopen(req)
    cookies  = response.headers.get('Set-Cookie') or ''

    if not confirm and 'download_warning' in cookies:
        confirm = CONFIRM_PATTERN.search(cookies)
        return process_file(id, file_path, file_size, confirm.group(1), cookies)

    sys.stdout.write(file_path+'\n')

    try:
        with open(file_path, 'wb') as f:
            dl = 0
            for chunk in iter(lambda: response.read(4096), ''):
                if not chunk:
                    break

                dl += len(chunk)
                f.write(chunk)
                done = int(50 * dl / file_size)
                sys.stdout.write("\r[{}{}] {:.2f}MB/{:.2f}MB".format('=' * done, ' ' * (50-done), dl/1024/1024, file_size/1024/1024))
                sys.stdout.flush()
    except:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

def get_arg(pos, default=None):
    try:
        return sys.argv[pos]
    except IndexError:
        return default

if __name__ == '__main__':
    url         = get_arg(1)
    directory   = get_arg(2, '.')

    if not url:
        sys.stderr.write('A URL or ID is required first argument')
        sys.exit(1)

    if not os.path.isdir(directory):
        sys.stderr.write("Directory {} doesn't exist".format(directory))
        sys.exit(1)

    id = None
    for pattern in ID_PATTERNS:
        match = pattern.search(url)
        if match:
            id = match.group(1)
            break

    if not id:
        sys.stderr.write('Unable to match ID from {}'.format(url))
        sys.exit(1)

    process_item(id, directory)