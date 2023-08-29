# GDriveDL-Parellel

Google Drive Download Script

-   No API keys / credentials required
-   Supports all operating systems
-   No external dependencies
-   Works with shared files or folders
-   Works with large files
-   Files / folders must have been shared via link
-   Processes downloads concurrently 

## Install
This package is available on [PyPi](https://pypi.org/project/gdrivedl-parallel/). 
```pip install gdrivedl-parallel```

## Usage

```bash
python gdrivedl-parallel.py <URL>
```
-   URL is a shared Google Drive URL

Multiple urls can be used by seperating them with a space. eg. ```python gdrivedl-parallel.py <URL1> <URL2> <URL3>```<br>
On some systems you may need to enclose the url within quotes. eg ```python gdrivedl-parallel.py "<URL>"```

### Options
- `-P` `--directory-prefix` Output directory (default is current directory)
- `-O` `--output-document` Download to a particular filename (defaults to the
  GDrive filename). Only valid when downloading a single file.
- `-q` `--quiet` Disable console output
- `-d` `--debug` Show more vebose debug console output
- `-m` `--mtimes` Try use modified times to check for changed files
- `-f` `--urlfile` Text file containing Google Drive URLS to download (one per line)
