# syncsketchGUI

##  Drag & Drop Install:

The easiest way to install this application is to download the [installCrossPlatform.mel](https://github.com/syncsketch/syncsketchGUI/releases/download/v1.0.4/installCrossPlatform.mel#install) file and drag it into a maya-viewport (2018 tested only. It will automatically install all the dependencies without requiring admin priviliges into your user-directory.


## Install it manually:

If you are familiar with python and pip, you can go for a manual installation  and follow these steps:

1) Install the Syncsketch-API + extras

`pip2.7.exe install --ignore-installed --user https://github.com/syncsketch/python-api/archive/v1.0.1.zip pyyaml requests[security]`

2) Install the Syncsketch-GUI

`pip2.7.exe install --ignore-installed --target=C:\Users\USERNAME\Documents\maya\2018\scripts https://github.com/syncsketch/syncsketchGUI/archive/v1.0.4.zip`

__Note__: Manual install expects you to have `ffmpeg` and `pip` already installed and set-up correctly.


Contributing
============
If you want to contribute to this project, your help is very welcome. We are trying to give a minimal version of a Publish workflow, which you can either adapt or get inspired by. 


##  Quick: Just fork this repo and start a pull request:

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
