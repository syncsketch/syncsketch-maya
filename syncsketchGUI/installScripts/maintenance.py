import pkg_resources
import syncsketchGUI
import os
import urllib2
import sys


def getLatestSetupPyFileFromRepo():
    """Parses latest setup.py's version number"""
    response = urllib2.urlopen(
        'https://raw.githubusercontent.com/syncsketch/syncsketch-maya/release/setup.py')
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
    if remote > local:
        return remote-local
    else:
         pass
