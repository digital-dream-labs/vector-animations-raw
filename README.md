# vector-animations-raw  
Maya rigs, scenes, and other resources for the Vector Robot!  

Sincere thanks to [Randall Maas](https://github.com/randym32) for his generous contributions to the OSKR project and to the Vector community!  

Building new animations requires a license to Autodesk Maya 2018-2020. Once you have installed Maya, you will need to install the AnkiMenu plugin (see the installation guide below). Once that is done, please see the [documentation](https://github.com/digital-dream-labs/vector-animations-raw/tree/main/documentation) folder for build guidelines.

# AnkiMenu Installation:

## macOS:

Install Maya 2018 or 2019

Open and close it

Install git and git-lfs with [brew](https://brew.sh/):

`brew install git-lfs`

Clone this git in your home directory: 

`cd ~`

`git clone https://github.com/digital-dream-labs/vector-animations-raw.git`

Install pip for python2:

`curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py`

`sudo python2 get-pip.py`

Install the Python packages:

`python2.7 -m pip install CharDet httplib2 idna python-ldap oauth2 Pillow requests pySerial sortedcontainers tlslite urllib3 nose tornado`

Copy the Maya.env:

`cp ~/vector-animations-raw/tools/other/Maya.env ~/Library/Preferences/Autodesk/maya/2018/`

Open Maya!

## Windows 10:

Install Maya 2018 or 2019

Fully open it and close it once

Install [Git Bash for Windows](https://git-scm.com/downloads)

[Install Python 2.7.18](https://www.python.org/downloads/release/python-2718/)

[Install this VC redistributable](https://web.archive.org/web/20200709160228/https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi)

Go to the start menu, type `cmd`, then open it

Run these commands:

`curl -o python_ldap-2.5.2-cp27-cp27m-win_amd64.whl https://download.lfd.uci.edu/pythonlibs/q4trcu4l/cp27/python_ldap-2.5.2-cp27-cp27m-win_amd64.whl`

`C:\Python27\python.exe -m pip install python_ldap-2.5.2-cp27-cp27m-win_amd64.whl`

`C:\Python27\python.exe -m pip install CharDet httplib2 idna oauth2 Pillow requests pySerial sortedcontainers tlslite urllib3 nose tornado`

Open Git Bash from the start menu search

Run:

`cd Documents`

`git clone https://github.com/digital-dream-labs/vector-animations-raw`

`cp vector-animations-raw/assets/tools/other/windowsMaya.env maya/2018/Maya.env` (If you installed 2019, replace 2018 with 2019)

`cp /c/Python27/Lib/site-packages/* vector-animations-raw/assets/tools/pylibs/downloaded/`

Open Maya!

## Linux:

Install Maya 2018 or 2019

Open and close it

Install the `git-lfs` package with your distro's package manager

Clone this git in your home directory: 

`cd ~`

`git clone https://github.com/digital-dream-labs/vector-animations-raw.git`

Install pip for python2:

`curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py`

`sudo python2 get-pip.py`

Install the Python packages:

`python2.7 -m pip install CharDet httplib2 idna python-ldap oauth2 Pillow requests pySerial sortedcontainers tlslite urllib3 nose tornado`

Copy the Maya.env:

`cp ~/vector-animations-raw/tools/other/linuxMaya.env ~/maya/2018/`

Open up ~/vector-animations-raw/assets/tools/pylibs/ankimaya/game_exporter.py in a text editor and replace `GAME_EXPORTER_PLUGIN = "gameFbxExporter"` with `GAME_EXPORTER_PLUGIN = "fbxmaya.so"`

Open Maya!
