import sys
import subprocess
import platform
import re
import os

import syncsketchGUI_install.util

GET_PIP_URL = "https://bootstrap.pypa.io/2.7/get-pip.py"


def _get_user_path():
    return os.path.expanduser('~')


class Environment():
    python_path = None
    pip_path = None

    def __new__(cls):
        os_name = platform.system()
        if os_name == "Windows":
            return WindowsEnvironment()
        elif os_name == "Linux":
            return LinuxEnvironment()
        elif os_name == "Darwin":
            return OSXEnvironment()
        else:
            raise Exception("No Environment available for {}".format(os_name))


class LinuxEnvironment(Environment):
    python_path = '/usr/bin/python'
    pip_path = os.path.join(_get_user_path(), '.local', 'bin', 'pip2.7')


class OSXEnvironment(OSXEnvironment):
    python_path = '/usr/bin/python'
    pip_path = os.path.join(_get_user_path(), 'Library', 'Python', '2.7', 'bin', 'pip2.7')


class WindowsEnvironment(WindowsEnvironment):
    python_path = os.path.join(os.getenv('MAYA_LOCATION'), 'bin', 'mayapy.exe')
    pip_path = os.path.join(os.getenv('APPDATA'), 'Python', 'Scripts', 'pip2.7.exe')


environment = Environment()


def get_pip_version():
    cmd_output = subprocess.check_output(
        [environment.python_path, '-m', 'pip', '--version'])

    verson_regex = re.compile(r"^pip (?P<version>.*) from")
    version_match = verson_regex.match(cmd_output)
    version_string = version_match.groupdict()["version"]
    return _get_version_tuple_from_string(version_string)


def install_pip():
    pip_installer_path = syncsketchGUI_install.util.make_temp_path("get-pip.py")
    syncsketchGUI_install.util.download_from_url_to_destionation(GET_PIP_URL, pip_installer_path)

    subprocess.call(
        [environment.python_path, pip_installer_path, "--user"])


def is_pip_installed():
    return os.path.exists(environment.pip_path)


def _get_version_tuple_from_string(version_string):
    return tuple(version_string.split("."))


if __name__ == "__main__":
    print(is_pip_installed())
    # print get_pip_version()
    print(install_pip())
    pass
