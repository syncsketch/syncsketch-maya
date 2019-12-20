import pkg_resources
import syncsketchGUI
import os
import urllib2
import sys

import logging
logger = logging.getLogger("syncsketchGUI")

from syncsketchGUI.installScripts import installGui
from syncsketchGUI.lib import user as user

class InstallerLiterals(object):
    versionTag = os.getenv("SS_DEV") or "release"
    setupPyPath = 'https://raw.githubusercontent.com/syncsketch/syncsketch-maya/{}/setup.py'.format(versionTag)
    installerPyGuiPath = 'https://raw.githubusercontent.com/syncsketch/syncsketch-maya/{}/syncsketchGUI/installScripts/installGui.py'.format(versionTag)

def getLatestSetupPyFileFromRepo():
    """Parses latest setup.py's version number"""
    response = urllib2.urlopen(InstallerLiterals.setupPyPath)
    html = response.read()
    return html.split("version = '")[1].split("',")[0]


def getLatestSetupPyFileFromLocal():
    """Checks locally installed packages version number"""
    import pkg_resources
    #reload module to make sure we have loaded the latest live install
    reload(pkg_resources)
    local = pkg_resources.get_distribution(
        "syncSketchGUI").version
    return local


def getVersionDifference():
    """Returns the difference between local Package and latest Remote"""
    remote = int(getLatestSetupPyFileFromRepo().replace(".", ""))
    local = int(getLatestSetupPyFileFromLocal().replace(".", ""))
    logger.info("Local Version : {} Remote Version {}".format(local, remote))
    if remote > local:
        return remote-local
    else:
         pass

def overwriteLatestInstallerFile():
    import urllib2
    logger.info("Attempting to replace installGui.py with release {}".format(InstallerLiterals.installerPyGuiPath))
    """Parses latest setup.py's version number"""
    response = urllib2.urlopen(InstallerLiterals.installerPyGuiPath)
    data = response.read()

    #Let's get the path of the installer
    installerPath = installGui.__file__[:-1]


    #Replace the module
    with open(installerPath, "w") as file:
        file.write(data)


def handleUpgrade():
    """[summary]

    Returns:
        [SyncSketchInstaller] -- [Instance of the Upgrade UI]
    """
    # * Check for Updates and load Upgrade UI if Needed
    if getVersionDifference():
        logger.info("YOU ARE {} VERSIONS BEHIND".format(getVersionDifference()))
        if os.getenv("SS_DISABLE_UPGRADE"):
            logger.warning("Upgrades disabled as environment Variable SS_DISABLE_UPGRADE is set, skipping")
            return
        #Let's first make sure to replace the installerGui with the latest.
        # * we might restore old file if not continued from here
        # ! Caution here, this is replacing infile your local files
        # ! Always make sure to remove this line when debugging, 
        # ! It will pull from release github and override changes
        overwriteLatestInstallerFile()


        logger.info("installGui.InstallOptions.upgrade {}".format(installGui.InstallOptions.upgrade))
        #Make sure we only show this window once per Session
        if not installGui.InstallOptions.upgrade == 1:
            reload(installGui)
            #If this is set to 1, it means upgrade was already installed
            installGui.InstallOptions.upgrade = 1

            #Preserve Credentials
            current_user = user.SyncSketchUser()

            if current_user.is_logged_in():
                installGui.InstallOptions.tokenData['username'] = current_user.get_name()
                installGui.InstallOptions.tokenData['token'] = current_user.get_token()
                installGui.InstallOptions.tokenData['api_key'] = current_user.get_api_key()
                logger.info("This is tokenData: {}".format(installGui.InstallOptions.tokenData))
            logger.info("Showing installer")
            Installer = installGui.SyncSketchInstaller()
            Installer.showit()

            return Installer
        else:
            logger.info("Installer Dismissed, will be activated in the next maya session again")

    else:
        logger.info("You are using the latest release of this package")