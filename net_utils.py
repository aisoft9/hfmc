import socket
import re

def is_ip(address):
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    return bool(re.match(pattern, address))

def is_valid_host(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False

def is_ip_or_host(string):
    if is_ip(string):
        return "IP"
    elif is_valid_host(string):
        return "Host"
    else:
        return "Invalid"