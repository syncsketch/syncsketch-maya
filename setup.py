from setuptools import setup, find_packages

setup(
    name = 'SyncsketchGUI',
    version = '1.0.0',
    url = 'https://github.com/Schizo/ssmaya.git',
    author = 'Syncsketch',
    author_email = "dev@syncsketch.com",
    description = "Syncsketch GUI for Autodesk Maya",
    packages = find_packages(),
    #todo: Refactor this to use manifest file
    package_data = {'syncsketchGUI.config': ['*.yaml']},
    install_requires = [],
)