# GDriveDL

Google Drive Download Script

-   Python 2 / 3 compatible
-   No API keys / credentials required
-   Supports all operating systems
-   No external dependencies
-   Works with shared files or folders
-   Works with large files
-   Files / folders must have been shared via link

## Usage

```bash
python gdrivedl.py <URL>
```
-   URL is a shared Google Drive URL

Multiple urls can be used by seperating them with a space. eg. ```python gdrivedl.py <URL1> <URL2> <URL3>```<br>
On some systems you may need to enclose the url within quotes. eg ```python gdrivedl.py "<URL>"```

### Options
- `-P` `--directory-prefix` Output directory (default is current directory)
- `-O` `--output-document` Download to a particular filename (defaults to the
  GDrive filename). Only valid when downloading a single file.
- `-q` `--quiet` Disable console output
- `-m` `--mtimes` Try use modified times to check for changed files