GDriveDL-GUI (Linux only)
=========================

Graphical wrapper for GDriveDL using bash and zenity.

Installation
------------

1. Make sure "~/.local/bin` is in `$PATH`
2. Clone this repo (`git clone "https://github.com/matthuisman/gdrivedl.git" && cd gdrivedl/GDriveDL`)
3. Execute the commands below
```
install -Dm0755 GDriveDL "$HOME"/.local/bin/GDriveDL
install -Dm0755 ../gdrivedl.py "$HOME"/.local/bin/gdrivedl.py
install -Dm0644 GDriveDL.desktop "$HOME"/.local/share/applications/GDriveDL.desktop
install -Dm0644 GDriveDL.png "$HOME"/.local/share/pixmaps/GDriveDL.png
sed -i -e "s|@HOME@|$HOME|" "$HOME"/.local/share/applications/GDriveDL.desktop
```

Usage
-----

1. Start GDriveDL from the menu in your DE
2. Enter a GDrive URL
3. Wait for the download to finish
