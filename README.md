# GDriveDL

Google Drive Download Script

-   Python 2 / 3 Compatible
-   No API keys / credentials required
-   Supports all operating systems
-   No external dependencies
-   Works with shared files or folders
-   Works with large files
-   Files / Folders must have been shared via link

## Usage

```bash
python gdrivedl.py <URL> <URL> <URL>
```
-   URL is a shared Google Drive URL

### Options
- `-P` `--directory-prefix` Output directory (default is current directory)
- `-O` `--output-document` Download to a particular filename (defaults to the
  GDrive filename). Only valid when downloading a single file.
- `-q` `--quiet` Disable console output
