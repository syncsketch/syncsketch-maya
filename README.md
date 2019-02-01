# syncsketchGUI

##  Drag & Drop Install:

The easiest way to install it is to download the [installCrossPlatform.mel](https://github.com/syncsketch/syncsketchGUI/releases/download/v1.0.4/installCrossPlatform.mel#install) file and drag it into a maya-viewport (2018 tested only) file and drop it into your maya scene, it will install all the dependencies without requiring admin priviliges into your user-directory.


## Install it manually:

To install it yourself, you only need run the following pip commands

1)  Install the Syncsketch-API and additional packages pyyamls and requests with the security  extras(to support old OpenSSL Versions)

`pip2.7.exe install --ignore-installed --user https://github.com/syncsketch/python-api/archive/v1.0.1.zip pyyaml requests[security]`

2) Install the Syncsketch-GUI

`pip2.7.exe install --ignore-installed --target=C:\Users\chavez\Documents\maya\2018\scripts https://github.com/syncsketch/syncsketchGUI/archive/v1.0.4.zip`

__Note__: Manual install expects you to have `ffmpeg` and `pip` already installed and set-up correctly
