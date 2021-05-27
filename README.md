# vector-animations-raw  
Maya rigs, scenes, and other resources for the Vector Robot!  

Sincere thanks to [Randall Maas](https://github.com/randym32) for his generous contributions to the OSKR project and to the Vector community!  

Building new animations requires a license to [Autodesk Maya](https://www.autodesk.com/products/maya/overview?term=1-YEAR). Once you have installed Maya, you will need to install the AnkiMenu plugin (see the [AnkiMenu readme](https://github.com/digital-dream-labs/vector-animations-raw/blob/main/assets/tools/plugins/readme.txt)). Once that is done, please see the [documentation](https://github.com/digital-dream-labs/vector-animations-raw/tree/main/documentation) folder for build guidelines.  

## Installation:

### macOS:

Install Maya 2018 or 2019 (later versions won't work currently)

Install git and git-lfs with [brew](https://brew.sh/):

`brew install git`

`brew install git-lfs`

Clone this git: 

`git clone https://github.com/digital-dream-labs/vector-animations-raw.git`

Make a workspace folder and make victor-animation:

`mkdir ~/workspace`

`mv vector-animations-raw/assets ~/workspace/victor-animation`

Install pip for python2:

`curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py`

`sudo python2 get-pip.py`

Install the Python packages:

`python2.7 ~/Library/Python/2.7/bin/pip install CharDet httplib2 idna python-ldap oauth2 Pillow requests pySerial sortedcontainers tlslite urllib3 nose tornado`

If you have installed Maya 2019, make symlinks:

`sudo ln -s /Applications/Autodesk/maya2019 /Applications/Autodesk/maya2018`

`ln -s ~/Library/Preferences/Autodesk/maya/2019 ~/Library/Preferences/Autodesk/maya/2018`

Copy the Maya.env:

`cp ~/workspace/victor-animation/tools/other/Maya.env ~/Library/Preferences/Autodesk/maya/2018/`

Open Maya!

### Windows: N/A (soon)

### Linux: N/A (soon)