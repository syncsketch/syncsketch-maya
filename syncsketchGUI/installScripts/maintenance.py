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
    return int(html.split("version = '")[1].split("',")[0].replace(".", ""))


def getLatestSetupPyFileFromLocal():
    """Checks locally installed packages version number"""
    import pkg_resources
    local = int(pkg_resources.get_distribution(
        "syncSketchGUI").version.replace(".", ""))
    return local


def getVersionDifference():
    """Returns the difference between local Package and latest Remote"""
    remote = getLatestSetupPyFileFromRepo()
    local = getLatestSetupPyFileFromLocal()
    print remote, local
    if remote > local:
        print "You are {} Version's behind ".format(remote-local)
        return remote-local
    else:
         pass


