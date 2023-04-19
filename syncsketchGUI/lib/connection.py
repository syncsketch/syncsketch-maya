import socket

REMOTE_SERVER = "www.syncsketch.com"


def is_connected():
    try:
        # see if we can resolve the host name -- tells us if there is a DNS listening
        host = socket.gethostbyname(REMOTE_SERVER)
        # connect to the host -- tells us if the host is actually reachable
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        pass
    return False


def open_url(self):
    webbrowser.open(url)
