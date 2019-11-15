import email
import os
import logging
logger = logging.getLogger("syncsketchGUI")

# ======================================================================
# Web Paths
api_host_url = "https://www.syncsketch.com"
home_url = api_host_url
project_url = api_host_url + '/pro/#project/'
contact_url = api_host_url + '/contact/'
signup_url = api_host_url + '/register/'
support_url = 'https://support.syncsketch.com/article/62-maya-syncsketch-integration'
terms_url = api_host_url + '/terms/'

# ======================================================================
# Module Functions

def join(*components):
    '''
    Join the given path components and return a clean path
    '''
    raw_path = str()
    for component in components:
        raw_path = os.path.join(raw_path, component)

    clean_path = sanitize(raw_path)
    return clean_path

def sanitize(raw_path):
    '''
    Replace the back slashes with forward slashes
    '''
    clean_path = raw_path.replace('\\', '/')
    return clean_path

def make_windows_style(raw_path):
    '''
    Replace the forward slashes with back slashes
    '''
    windows_style = raw_path.replace('/', '\\')
    return windows_style

def make_safe(raw_path):
    norm_path = os.path.normpath(raw_path)
    path_components = norm_path.split(os.sep)
    for i, path_component in enumerate(path_components):
        if  ' ' in path_component and \
            not path_component.endswith('"') and \
            not path_component.startswith('"'):
            path_components[i] = '"{}"'.format(path_component)

    quoted_path = '/'.join(path_components)
    safe_path = os.path.normpath(quoted_path)
    return safe_path

def make_url_offlineMode(url):
    '''
    Add's offline Mode key to a given url
    '''
     #https://www.syncsketch.com/sketch/b280d3a7cb30/#1127001
     #https://www.syncsketch.com/sketch/b280d3a7cb30/#1127001
     #converts to: https://www.syncsketch.com/sketch/b280d3a7cb30/?offlineMode=1#/1127001
     #https://syncsketch.com/sketch/806b718865d3#1127977
     #https://syncsketch.com/sketch/806b718865d3?offlineMode=1#


    offlineUrl = url.replace("/#", "?offlineMode=1#")
    if offlineUrl == url:
        offlineUrl = url.replace("#", "?offlineMode=1#")
    return offlineUrl

def validate_email_address(email_address):
    '''
    Check to make sure if the given email address if valid
    '''
    if isinstance(email_address, str):
        return email.utils.parseaddr(email_address)[-1]

# ======================================================================
# Local Paths

def get_root_folder():
    '''
    Get the top folder of the maya syncsketch tool
    '''
    core_folder = os.path.dirname(__file__)
    package_folder = os.path.dirname(core_folder)
    root_folder = os.path.dirname(package_folder)
    root_folder = sanitize(root_folder)
    return root_folder


def get_config_folder():
    '''
    Get the full path of the config folder
    '''
    root_folder = get_root_folder()
    config_folder = os.path.join(root_folder, 'syncsketchGUI', 'config')
    config_folder = sanitize(config_folder)
    return config_folder

def get_config_yaml(yaml_file):
    '''
    Take the yaml file name and construct the full path
    '''
    config_folder = get_config_folder()
    config_yaml = os.path.join(config_folder, yaml_file)
    config_yaml = sanitize(config_yaml)
    return config_yaml

def get_image_folder():
    '''
    Get the full path of the image folder
    '''
    root_folder = get_root_folder()
    image_folder = os.path.join(root_folder, 'syncsketchGUI', 'ressources', 'image')
    image_folder = sanitize(image_folder)
    return image_folder

def get_icon(icon_name):
    '''
    Get logo path and return the fullname
    '''
    image_folder = get_image_folder()
    icon_fullname = os.path.join(image_folder, icon_name)
    icon_fullname = sanitize(icon_fullname)
    return icon_fullname

def get_ffmpeg_folder():
    '''
    Get the full path of the ffmpeg tool folder
    '''
    root_folder = get_root_folder()
    ffmpeg_folder = os.path.join(root_folder, 'ffmpeg')
    ffmpeg_folder = sanitize(ffmpeg_folder)
    return ffmpeg_folder

def get_ffmpeg_bin():
    '''
    Get the bin folder of the ffmpeg tool folder
    '''
    ffmpeg_folder = get_ffmpeg_folder()
    ffmpeg_bin = os.path.join(ffmpeg_folder, 'bin')
    ffmpeg_bin = make_windows_style(ffmpeg_bin)
    return ffmpeg_bin

def get_default_playblast_folder():
    '''
    Get the default playblast directory, a folder named playblasts on user's desktop
    '''
    directory = os.path.expanduser('~/Desktop/playblasts')
    filepath = os.path.join(directory, 'playblasts')
    filepath = sanitize(filepath)
    return filepath