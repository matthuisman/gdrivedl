# GDriveDL

Google Drive Download Script

-   Python 2 / 3 Compatible
-   Supports all operating systems
-   No external dependencies
-   Works with shared files or folders
-   Works with large files
-   Files / Folders must have been shared via link

### How to run the script

```bash
./GDriveDL <URL> <DIRECTORY>
```

Has two arguments:

-   URL is Shared Goolge Drive URL containing ID
-   DIRECTORY (Optional, defaults to current directory `./`)

Eg:

```bash
sudo curl https://raw.githubusercontent.com/matthuisman/gdrivedl/master/gdrivedl.py --output GDriveDL

sudo chmod +x GDriveDL

./GDriveDL https://drive.google.com/open?id=1yXsJq7TTMgUVXbOnCalyupESFN-tm2nc ./some_folder
```