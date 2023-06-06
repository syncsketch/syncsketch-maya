![maya2020](https://img.shields.io/badge/Maya2020-tested-brightgreen.svg)
![maya2022](https://img.shields.io/badge/Maya2022-tested-brightgreen.svg)
![maya2023](https://img.shields.io/badge/Maya2023-tested-brightgreen.svg)
![maya2024](https://img.shields.io/badge/Maya2024-tested-brightgreen.svg)

The syncsketch-maya plugin which will allow you to 
- upload videos and playblasts to syncsketch in seconds, skipping any conversion process
- download notes and image annotations from syncsketch back to maya, adjust parameters such like frame offset etc
- manage your viewport presets for recording

See a quick Intro Video for this plugin here: https://vimeo.com/syncsketch/integrationmaya

See a good use case, demonstrated by Zeina Masri on how to animate from reference: https://vimeo.com/359388029

# Installation

### Drag & Drop

The easiest way to install this application is to ...
1. Click this File Link > [installGui.py](https://github.com/syncsketch/syncsketch-maya/releases/latest/download/installGui.py) < to download the installation Python file.
2. Drag drop it from the browser into a maya-viewport. 
This will automatically install all the dependencies without requiring admin privileges into the current version of Maya's modules folder.
3. Hit 'Install' and on Allow this process to run python (hit 'Allow' in the popup)
4. Start SyncSketch UI
5. Log-In with your SyncSketch Credentials.

![redux_maya_install](https://user-images.githubusercontent.com/10859650/72236028-0bec0e80-358a-11ea-92da-9fdc698e50e7.gif)

#### Installing an experimental dev release:


1) Set environment variable `SS_DEV` to `dev` in your environment or Maya Script Editor

```
import os
os.environ['SS_DEV'] = 'dev'
```

2) Download [installGui.py](https://github.com/syncsketch/syncsketch-maya/releases/download/dev/installGui.py) and drag it into your maya-viewport.

### Manual (Experienced user)


If you are familiar with python and pip, you can go for a manual installation and follow these steps:

1. Install the Syncsketch-API + extras
``` 
pip install --upgrade --user  "syncsketch>1,<2.0" "requests>2,<2.28.0" "pyyaml>5,<6.0"`
```

2. Install the Syncsketch-GUI

Use pip to install the latest release of the Maya Syncsketch plugin from Github. Update the target path to the Maya script folder for the current version of Maya you are using.
```
pip install --upgrade --target=C:\Users\USERNAME\Documents\maya\2018\scripts https://github.com/syncsketch/syncsketchGUI/archive/release.zip
```

3. Open Maya & Install the maya Shelf from the script editor:
```python
import syncsketchGUI
syncsketchGUI.install_shelf()
```


__Note__: Manual installation expects you to have `ffmpeg` and `pip` already installed and set-up correctly.

# Environment variables
`SS_DISABLE_UPGRADE` - If this environment variable is set, the plugin will not check for updates on startup.

`SS_DEV` - If this environment variable is set to `dev`, the plugin will install the latest dev release instead of the latest stable release.

# Contributing

### Fork and send pull request
If you want to contribute to this project, your help is very welcome. We are trying to give a minimal version of a Publish workflow, which you can either adapt or get inspired by. 


### Long: How to make a clean pull request

- Create a personal fork of our Github.
- Clone the fork on your local machine. Your remote repo on Github is called `origin`.
- Add the original repository as a remote called `upstream`.
- If you created your fork a while ago be sure to pull upstream changes into your local repository.
- Create a new branch to work on! Branch from `master`.
- Implement/fix your feature, comment your code.
- Add or change the documentation as needed.
- Squash your commits into a single commit with git's [interactive rebase](https://help.github.com/articles/interactive-rebase). Create a new branch if necessary.
- Push your branch to your fork on Github, the remote `origin`.
- From your fork open a pull request in the to the master branch
- Once the pull request is approved and merged you can pull the changes from `upstream` to your local repo and delete
your extra branch(es).

And last but not least: Always write your commit messages in the present tense. Your commit message should describe what the commit, when applied, does to the code – not what you did to the code.
