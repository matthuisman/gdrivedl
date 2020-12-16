# GDriveDL

Google Drive Download Script

-   Python 2 / 3 Compatible
-   Supports all operating systems
-   No external dependencies
-   Works with shared files or folders
-   Works with large files
-   Files / Folders must have been shared via link

## Usage

```bash
python gdrivedl.py <URL>
```
-   URL is Shared Goolge Drive URL containing ID

### Options
Options derive from `wget` conventions where possible.

- `-P` `--directory-prefix` <DIRECTORY>` Download to a different directory
  (default to the current directory)
- `-O` `--output-document` Download to a particular filename (defaults to the
  server filename). Not valid for folder downloads.
- `-q` `--quiet` Don't print progress bar
- `-v` `--verbose` Additional messages

### Example Linux Usage

```bash
sudo curl https://raw.githubusercontent.com/matthuisman/gdrivedl/master/gdrivedl.py --output GDriveDL

sudo chmod +x GDriveDL

./GDriveDL https://drive.google.com/open?id=1yXsJq7TTMgUVXbOnCalyupESFN-tm2nc -P ./some_folder
```

