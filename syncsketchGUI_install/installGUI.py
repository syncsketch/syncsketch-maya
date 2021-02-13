import sys
import subprocess
import platform
import re
import os 
import urllib2
import tempfile
import zipfile
import shutil
import json 
import glob

import logging

logger = logging.getLogger('syncsketchGUI_install')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s]', "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)


GET_PIP_URL = "https://bootstrap.pypa.io/2.7/get-pip.py"
FFMPEG_API_ENDPOINT = 'https://ffbinaries.com/api/v1/version/4.2'


class Environment():
    python_path = None
    pip_path    = None

    def __new__(cls): 
        os_name = platform.system()
        if  os_name == "Windows":
            return WindowsEnvironment()
        elif os_name == "Linux":
            return LinuxEnvironment()
        elif os_name == "Darwin":
            return OSXEnvironment()
        else:
            raise Exception("No Environment available for {}".format(os_name))

class LinuxEnvironment():
    python_path = '/usr/bin/python'
    pip_path    = os.path.join(_get_user_path(), '.local', 'bin', 'pip2.7')

class OSXEnvironment():
    python_path = '/usr/bin/python'
    pip_path    = os.path.join(_get_user_path(), 'Library', 'Python', '2.7', 'bin', 'pip2.7')

class WindowsEnvironment():
    python_path = os.path.join(os.getenv('MAYA_LOCATION'), 'bin', 'mayapy.exe')
    pip_path    = os.path.join(os.getenv('APPDATA'), 'Python', 'Scripts', 'pip2.7.exe')


environment = Environment()


class Pip():
    @staticmethod
    def install():
        pip_installer_path = _make_temp_path("get-pip.py")
        _download_from_url_to_destionation(GET_PIP_URL, pip_installer_path)

    @staticmethod
    def is_installed():
        return os.path.exists(environment.pip_path)


class FFMPEG:
    binaries = ["ffmpeg", "ffprobe"]

    @staticmethod
    def install(install_dir):
        for binary in FFMPEG.binaries:
            FFMPEG._install_binary(binary, install_dir)

    @staticmethod
    def _install_binary(binary_name, install_dir):
        donwloaded_file = FFMPEG._download_binary(binary_name)
        extract_directory = _extract_zip_file(donwloaded_file)
        downloaded_binary_file = _find_binary_in_dir(binary_name, extract_directory)
        _set_executable_permission(downloaded_binary_file)
        _move_file_to_directory(downloaded_binary_file, install_dir)
    
    @staticmethod
    def _download_binary(binary_name):
        download_url = FFMPEG._get_os_specific_download_url_for(binary_name)
        download_destination = _make_temp_path(binary_name + ".zip")
        _download_from_url_to_destionation(download_url, download_destination)
        return download_destination

    @staticmethod
    def _get_os_specific_download_url_for(binary_name):
        platform_mapping = {
            'Windows': 'windows-64',
            'Darwin' : 'osx-64',
            'Linux'  : 'linux-64'
                    }   

        platform_id = platform_mapping[platform.system()]
        ffmpeg_resp = _get_json_response_from_url(FFMPEG_API_ENDPOINT)
        return ffmpeg_resp['bin'][platform_id][binary_name]
    



def _get_user_path():
    return os.path.expanduser('~')

def _get_json_response_from_url(url):
    logger.debug("Get Json Response From {}".format(url))
    response = _get_response_from_url(url)
    json_dict = json.load(response)
    return json_dict

def _set_executable_permission(file_path):
    os.chmod(file_path, 0o755)

def _move_file_to_directory(file_path, directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)
    shutil.copy(file_path, directory)

def _extract_zip_file(zip_file):
    file_name_without_ext = os.path.splitext(zip_file)[0]
    extract_destination = file_name_without_ext + "_extracted"
    _extract_zip_file_to_destination(zip_file, extract_destination)
    return extract_destination

def _extract_zip_file_to_destination(zip_file, destination):
    print('Unzip from {} to {}'.format(zip_file, destination))
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(destination)
    zip_ref.close()  

def _make_temp_path(name):
    tmpdir = tempfile.mkdtemp()
    return os.path.join(tmpdir, name)

def _download_from_url_to_destionation(url, destination):
    response = _get_response_from_url(url)
    with open(destination, 'wb') as f:
        f.write(response.read())
    logger.info("Downloading from {} to {}"
        .format(url, destination))

def _get_response_from_url(url):
    req = urllib2.Request(url, headers = {"User-Agent": "Mozilla/5.0"})
    response = urllib2.urlopen(req)
    return response

def _find_binary_in_dir(binary_name, directory):
    bin_path = glob.glob(os.path.join(directory, '{}*'.format(binary_name)))[0]
    print('Found binary {} at {}'.format(binary_name, bin_path))
    return bin_path