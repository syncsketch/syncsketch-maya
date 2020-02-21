from setuptools import setup, find_packages

setup(
    name = 'SyncsketchGUI',
    version = '1.1.6',
    url = 'https://github.com/syncsketch/syncsketch-maya.git',
    author = 'Syncsketch',
    author_email = "dev@syncsketch.com",
    description = "Syncsketch GUI for Autodesk Maya",
    packages = find_packages(),
    include_package_data = True,
    package_data = {'syncsketchGUI.config': ['*.yaml']},
    install_requires = [],
)