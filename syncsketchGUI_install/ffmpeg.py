import platform
import os
import glob
import logging

from syncsketchGUI_install import util

logger = logging.getLogger('syncsketchGUI_install')


FFMPEG_API_ENDPOINT = 'https://ffbinaries.com/api/v1/version/4.2'

FFMPEG_BINARIES = ["ffmpeg", "ffprobe"]
    
platform_mapping = {
        'Windows': 'windows-64',
        'Darwin' : 'osx-64',
        'Linux'  : 'linux-64'
                }       

def install():
    for binary in FFMPEG_BINARIES:
        _install_ffbinary(binary)


def _install_ffbinary(binary_name):

    donwloaded_file = _download_ffbinary(binary_name)
    extract_directory = util.extract_zip_file(donwloaded_file)
    downloaded_binary_file = _find_binary_in_dir(binary_name, extract_directory)
    _set_permission(downloaded_binary_file)
    install_directory = _make_install_path("ffmpeg")
    util.move_file_to_directory(downloaded_binary_file, install_directory)


def _make_install_path(name, destination=None):
    if not destination:
        destination = util.get_this_package_directory()
    
    if not os.path.exists(destination):
        os.makedirs(destination)
    
    install_path = os.path.join(destination, name)
    return install_path

def _download_ffbinary(binary_name):
    download_url = _get_os_specific_download_url_for(binary_name)
    download_destination = util.make_temp_path(binary_name + ".zip")
    util.download_from_url_to_destionation(download_url, download_destination)
    return download_destination


def _find_binary_in_dir(binary_name, directory):
    bin_path = glob.glob(os.path.join(directory, '{}*'.format(binary_name)))[0]
    print('Found binary {} at {}'.format(binary_name, bin_path))
    return bin_path

def _set_permission(file_path):
    os.chmod(file_path, 0o755)

def _get_os_specific_download_url_for(binary_name):
    platform_id = platform_mapping[platform.system()]
    ffmpeg_resp = util.get_json_response_from_url(FFMPEG_API_ENDPOINT)
    return ffmpeg_resp['bin'][platform_id][binary_name]
