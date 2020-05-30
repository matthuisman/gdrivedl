# GDriveDL

Google Drive Download Script

-   Python 3 Support (Python 2 obsolete)
-   Supports all operating systems
-   No external dependencies
-   Works with shared files or folders
-   Works with large files
-   Files / Folders must have been shared via link

### How to run the script

Has two arguments:

-   URL containing ID (Shared URL link)
-   DIRECTORY (Optional, defaults to `./`)

Eg:

```bash
sudo curl https://raw.githubusercontent.com/vibhavagarwal5/GDriveDL/master/GDriveDL.py --output GDriveDL

sudo chmod +x GDriveDL
```

```
./GDriveDL <URL> <DIRECTORY>

OR

./GDriveDL https://drive.google.com/open?id=1yXsJq7TTMgUVXbOnCalyupESFN-tm2nc ./some_folder
```
