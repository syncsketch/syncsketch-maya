import socket

from syncsketchGUI.lib.path import get_syncsketch_url


def is_connected():
    try:
        syncsketch_url = get_syncsketch_url()
        remote_server = syncsketch_url.replace("https://", "").replace("http://", "").split("/")[0]
        if ":" in remote_server:
            remote_server, remote_port = remote_server.rsplit(":", 1)
        else:
            remote_port = 80

        # see if we can resolve the host name -- tells us if there is a DNS listening
        host = socket.gethostbyname(remote_server)
        # connect to the host -- tells us if the host is actually reachable
        s = socket.create_connection((host, remote_port), 2)
        return True
    except:
        pass

    return False
