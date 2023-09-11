import os
import re

from setuptools import setup, find_packages

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(ROOT_PATH, 'syncsketchGUI', 'version.py')) as _version_file:
    VERSION = re.match(r'.*__version__ = \"(.*?)\"', _version_file.read(), re.DOTALL).group(1)

setup(
    name='SyncsketchGUI',
    version=VERSION,
    url='https://github.com/syncsketch/syncsketch-maya.git',
    author='Syncsketch',
    author_email="dev@syncsketch.com",
    description="Syncsketch GUI for Autodesk Maya",
    packages=find_packages(),
    include_package_data=True,
    package_data={'syncsketchGUI.config': ['*.yaml']},
    install_requires=[
        "requests>2,<2.28.0",
        "syncsketch>1,<2.0",
        "pyyaml>5,<6.0"
    ],
)

# This to be backward compatible with older versions (<1.3.0) of the plugin. They will fail on launch if this is
# not found. The specific version does not matter in this case, it just has be larger than 1.2.1. That will trigger
# and upgrade to the latest version.
# version = '1.3.0',
