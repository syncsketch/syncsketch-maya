import tempfile
import zipfile
import tarfile
import os
import urllib2
import shutil
import json
import logging

logger = logging.getLogger('syncsketchGUI_install')


def move_file_to_directory(file_path, directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)
    shutil.copy(file_path, directory)


def download_from_url_to_destionation(url, destination):
    response = get_response_from_url(url)
    with open(destination, 'wb') as f:
        f.write(response.read())
    logger.info("Downloading from {} to {}"
                .format(url, destination))


def extract_tar_file(file_path):
    extract_destination = os.path.dirname(file_path)
    tar = tarfile.open(file_path, "r:gz")
    tar.extractall(path=extract_destination)
    tar.close()

    extracted_path = file_path[:-7]
    logger.info("Extracted file {} to {}".format(
        file_path, extracted_path))
    return extracted_path


def extract_zip_file(zip_file):
    file_name_without_ext = os.path.splitext(zip_file)[0]
    extract_destination = file_name_without_ext + "_extracted"
    extract_zip_file_to_destination(zip_file, extract_destination)
    return extract_destination


def extract_zip_file_to_destination(zip_file, destination):
    print('Unzip from {} to {}'.format(zip_file, destination))
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(destination)
    zip_ref.close()


def make_temp_path(name):
    tmpdir = tempfile.mkdtemp()
    return os.path.join(tmpdir, name)


def get_json_response_from_url(url):
    logger.debug("Get Json Response From {}".format(url))
    response = get_response_from_url(url)
    json_dict = json.load(response)
    return json_dict


def get_response_from_url(url):
    req = urllib2.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    response = urllib2.urlopen(req)
    return response


def move_directory_content_to_destination(directory, destination):
    # FIXME Overwrite existing files
    logger.info("Move content of {} to {}".format(
        directory, destination
    ))
    if not os.path.isdir(destination):
        os.makedirs(destination)
    file_names = os.listdir(directory)
    for file_name in file_names:
        shutil.move(os.path.join(directory, file_name), destination)


def get_file_name_from_url(url):
    return os.path.split(url)[1]


def get_text_from_file(file_path):
    with open(file_path, 'r') as reader:
        content = reader.read()
    return content


def get_this_package_directory():
    return os.path.dirname(os.path.abspath(__file__))
