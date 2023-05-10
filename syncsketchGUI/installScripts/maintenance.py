import logging
import os
import re
import sys
import uuid

from maya import OpenMayaUI as omui

try:
    # python3
    from urllib.request import urlopen
except ImportError:
    # python2
    from urllib2 import urlopen

try:
    # python3
    from importlib import reload
except ImportError:
    pass

from syncsketchGUI.vendor.Qt import QtWidgets
from syncsketchGUI.vendor.Qt import QtCompat

from syncsketchGUI.installScripts import installGui
from syncsketchGUI.lib import user as user

logger = logging.getLogger("syncsketchGUI")


class InstallerLiterals(object):
    version_tag = os.getenv("SS_DEV") or "release"
    if os.environ.get("SYNCSKETCH_GUI_SOURCE_PATH"):
        setup_py_path = 'file:///{}/syncsketchGUI/version.py'.format(os.environ.get("SYNCSKETCH_GUI_SOURCE_PATH"))
        installer_py_gui_path = "file:///{}/syncsketchGUI/installScripts/installGui.py".format(
            os.environ.get("SYNCSKETCH_GUI_SOURCE_PATH"))
    else:
        setup_py_path = 'https://raw.githubusercontent.com/syncsketch/syncsketch-maya/{}/syncsketchGUI/version.py'.format(
            version_tag)
        installer_py_gui_path = 'https://raw.githubusercontent.com/syncsketch/syncsketch-maya/{}/syncsketchGUI/installScripts/installGui.py'.format(
            version_tag)


def _parse_version_py_content(version_py_content):
    try:
        version = re.match(r'.*__version__ = \"(.*?)\"', version_py_content, re.DOTALL).group(1)
    except Exception as error:
        print("Error: {}".format(error))
        version = "1.0.0"

    return version


def get_latest_setup_py_file_from_repo():
    """Parses latest setup.py's version number"""
    response = urlopen(InstallerLiterals.setup_py_path).read()
    if response:
        html = response.decode()
        return _parse_version_py_content(html)
    else:
        logger.warning("Could not find latest setup.py file from repo")
        return -1


def get_latest_setup_py_file_from_local():
    """Checks locally installed packages version number"""
    import syncsketchGUI
    return syncsketchGUI.__version__


def get_version_difference():
    """Returns the difference between local Package and latest Remote"""
    remote = int(get_latest_setup_py_file_from_repo().replace(".", ""))
    local = int(get_latest_setup_py_file_from_local().replace(".", ""))
    logger.info("Local Version : {} Remote Version {}".format(local, remote))
    if remote > local:
        return remote - local
    else:
        pass


def download_latest_installer():
    import tempfile

    logger.info("Downloading latest installGui.py from release {}".format(InstallerLiterals.installer_py_gui_path))

    response = urlopen(InstallerLiterals.installer_py_gui_path)
    data = response.read().decode('utf-8')

    temp_install_file = os.path.join(tempfile.gettempdir(), "installGui_{}.py".format(uuid.uuid4().hex[:8]))
    # write to temp file
    with open(temp_install_file, "w") as file:
        file.write(data)

    return temp_install_file


def get_maya_ui_parent():
    return QtCompat.wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)


def handle_upgrade():
    """[summary]

    Returns:
        [SyncSketchInstaller] -- [Instance of the Upgrade UI]
    """
    # * Check for Updates and load Upgrade UI if Needed
    version_difference = get_version_difference()
    logger.debug("version_difference {}".format(version_difference))
    if version_difference:
        logger.info("You are {} versions behind".format(version_difference))
        if os.getenv("SS_DISABLE_UPGRADE"):
            logger.warning("Upgrades disabled as environment Variable SS_DISABLE_UPGRADE is set, skipping")
            return

        logger.info("installGui.InstallOptions.upgrade {}".format(installGui.InstallOptions.upgrade))
        # Make sure we only show this window once per Session
        if not installGui.InstallOptions.upgrade == 1:
            temp_install_file = download_latest_installer()

            if sys.version_info.major == 3:
                import importlib.util
                spec = importlib.util.spec_from_file_location("installGui", temp_install_file)
                installGui_latest = importlib.util.module_from_spec(spec)
                # sys.modules["installGui-1.2.1"] = foo
                spec.loader.exec_module(installGui_latest)
            elif sys.version_info.major == 2:
                import imp
                installGui_latest = imp.load_source("installGui", temp_install_file)

            # If this is set to 1, it means upgrade was already installed
            installGui_latest.InstallOptions.upgrade = 1

            # Preserve Credentials
            current_user = user.SyncSketchUser()

            if current_user.is_logged_in():
                installGui_latest.InstallOptions.tokenData['username'] = current_user.get_name()
                installGui_latest.InstallOptions.tokenData['token'] = current_user.get_token()
                installGui_latest.InstallOptions.tokenData['api_key'] = current_user.get_api_key()

            logger.info("Showing installer")
            installer = installGui_latest.InstallerUI(get_maya_ui_parent())
            installer.show()

            return installer
        else:
            logger.info("Installer Dismissed, will be activated in the next maya session again")

    else:
        logger.info("You are using the latest release of this package")
