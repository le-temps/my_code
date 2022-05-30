import ipaddress

def valid_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.version
    except:
        return 0