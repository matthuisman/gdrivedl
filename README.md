# gdrivedl
Google Drive Download Script

* Python 2 / 3 Compatible
* No external dependencies
* Works with shared files or folders
* Works with large files

### Argument 1 ###
URL containing ID or ID

### Argument 2 (optional) ### 
Directory to download to (must already exist)<br/>
*Defaults to current directory*

### Example Usage ###
```bash
sudo curl https://raw.githubusercontent.com/matthuisman/gdrivedl/master/gdrivedl.py --output /usr/bin/gdrivedl
sudo chmod +x /usr/bin/gdrivedl

cd ~
gdrivedl https://drive.google.com/open?id=1yXsJq7TTMgUVXbOnCalyupESFN-tm2nc
gdrivedl 1yXsJq7TTMgUVXbOnCalyupESFN-tm2nc /tmp
```
