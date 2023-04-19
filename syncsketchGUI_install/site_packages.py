import urllib2
import json
import os
import logging
import inspect

from syncsketchGUI_install import util

logger = logging.getLogger('syncsketchGUI_install')


class VersionNotFoundError(Exception):
    pass


class PackageNotFoundError(Exception):
    pass


class NoSourceDistributionError(Exception):
    pass


def install(destination=None):
    packages = _get_packages_from_requriements()
    for package in packages:
        _install_package(package, destination)


def _install_package(package, destination=None):
    file_path = _download_package(package)
    extracted_package_path = util.extract_tar_file(file_path)
    package_source_path = os.path.join(extracted_package_path, package["name"])
    install_path = _make_install_path(package["name"], destination=destination)
    util.move_directory_content_to_destination(package_source_path, install_path)


def _download_package(package, path=None):
    url = _get_package_tarball_download_url(package["name"], package["version"])
    file_name = util.get_file_name_from_url(url)
    if path:
        file_path = os.path.join(path, file_name)
    else:
        file_path = util.make_temp_path(file_name)
    util.download_from_url_to_destionation(url, file_path)
    return file_path


def _get_packages_from_requriements():
    requirements_file_path = _find_requirements_file_path()
    requirements_text = util.get_text_from_file(requirements_file_path)
    packages = _get_packages_from_text(requirements_text)
    return packages


def _get_packages_from_text(text):
    packages = list()
    for line in text.splitlines():
        package = _get_package_from_line(line)
        packages.append(package)
    return packages


def _get_package_from_line(line):
    package = dict()
    package["name"], package["version"] = line.split("==")
    return package


def _make_install_path(name, destination=None):
    if not destination:
        destination = os.path.join(util.get_this_package_directory(), "site-packages")

    if not os.path.exists(destination):
        os.makedirs(destination)

    install_path = os.path.join(destination, name)
    return install_path


def _find_requirements_file_path():
    search_dirs = [
        util.get_this_package_directory(),
    ]
    requirements_file_path = _find_requirements_file_path_in_dirs(search_dirs)
    if not requirements_file_path:
        raise IOError(
            "Requirements file cannot be found in directories {}".format(search_dirs))
    logger.debug("Found requirements file at {}".format(requirements_file_path))
    return requirements_file_path


def _find_requirements_file_path_in_dirs(directories):
    for directory in directories:
        requirements_file_path = _find_requirements_file_path_in_dir(directory)
        if requirements_file_path:
            return requirements_file_path
    return None


def _find_requirements_file_path_in_dir(directory):
    requirments_file_name = "requirements.txt"
    potential_file_path = os.path.join(directory, requirments_file_name)
    if os.path.exists(potential_file_path):
        return potential_file_path
    else:
        return None


def _get_package_tarball_download_url(package_name, version):
    pypi_package_url = _generate_pypi_package_url(package_name)

    try:
        pypi_json_response = util.get_json_response_from_url(pypi_package_url)
    except urllib2.HTTPError:
        raise PackageNotFoundError(
            "Package [{}] not found at {}."
            .format(package_name, pypi_package_url))

    version_info = _extract_info_from_json_for_version(
        pypi_json_response, version)

    tarball_url = _extract_tarball_url_from_version_info(version_info)
    if not tarball_url:
        raise NoSourceDistributionError(
            "Could not find tarball url for {} {}"
            .format(package_name, version))

    return tarball_url


def _generate_pypi_package_url(package_name):
    return "https://pypi.org/pypi/{}/json".format(package_name)


def _extract_info_from_json_for_version(json_dict, version):
    try:
        package_version_info = json_dict["releases"][version]
    except KeyError:
        raise VersionNotFoundError(
            "Could find version {} for package {}"
            .format(version, json_dict["info"]["name"]))
    return package_version_info


def _extract_tarball_url_from_version_info(version_info):
    for distribution in version_info:
        if distribution["packagetype"] == "sdist":
            return distribution["url"]
    return None
