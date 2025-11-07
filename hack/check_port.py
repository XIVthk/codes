import socket
from typing import Iterable
from concurrent.futures import ThreadPoolExecutor
import re


class IPError(Exception): pass


class ScanError(Exception): pass


class IPV4:
    # IPV4: 0.0.0.0 ~ 255.255.255.255
    def __init__(self, ip: str | Iterable[int | str]):
        """
        Convert any IPV4s to type IPV4, and give some methods to deal with it.
        
        Setup:
            >>> my_host = "127.0.0.1"
            >>> wrong_hosts = ["256.0.0.0", 42, "abc", (6, 3)]
            >>> allowed_hosts = ["0.0.0.0", (10, 20, 30, 40), [3, 3, 3, 3]]
        
        Examples:
            >>> print(IPV4(my_host))
            127.0.0.1

            >>> for host in wrong_hosts:
            ...     try:
            ...         print(IPV4(host))
            ...     except Exception as err:
            ...         print(f"Error: {repr(err)}")
            Error: IPError('All given nums must >= 0 and <= 255')
            Error: TypeError("Expected str | Iterable[int | str], got <class 'int'>")
            Error: IPError('Expected a hostname or an IPV4, got "abc", error: [Errno 11001] getaddrinfo failed')
            Error: IPError('IPV4 must be x.x.x.x or a hostname')

            >>> for host in allowed_hosts:
            ...     print(IPV4(host), end="\t")
            ...     print(repr(IPV4(host)))
            0.0.0.0       IPV4 0.0.0.0
            10.20.30.40       IPV4 10.20.30.40
            3.3.3.3       IPV4 3.3.3.3

        :param ip: An IPV4 address, str, Iterable[int | str] allowed.
        :raise IPError: 
                1. Excepted a hostname or an IPV4, but given string is not.
                2. More than 4 parts given like "0.0.0.0.0".
                3. Any numbers greater than 255 or lower than 0.
        :raise TypeError:
                Expected str | Iterable[int | str], got other types.

        """
        if isinstance(ip, str):
            if not re.match(r"\d+\.\d+\.\d+\.\d", ip):
                try:
                    self._ip = socket.gethostbyname(ip)
                except socket.gaierror as err:
                    raise IPError(f"Expected a hostname or an IPV4, got \"{ip}\", error: {err}")
            else:
                self._ip = ip
            ips = self._ip.split(".")
            self._ip = [int(dt) for dt in ips]
        
        elif isinstance(ip, Iterable):
            self._ip = [int(dt) for dt in list(ip)]
        
        else:
            raise TypeError(f"Expected str | Iterable[int | str], got {type(ip)}")
        
        if len(self._ip) != 4:
            raise IPError("IPV4 must be x.x.x.x or a hostname")
        if any(map(lambda x: 0 if 0 <= x <= 255 else 1, self._ip)):
            raise IPError("All given nums must >= 0 and <= 255")
    
    def __repr__(self):
        """
        :return: A better-reading string like "IPV4 x.x.x.x"
        """
        return "IPV4 " + self.__str__()
    
    def __str__(self):
        """
        :return: A string like "x.x.x.x"
        """
        return ".".join([str(dt) for dt in self._ip])
    
    def get_ip(self):
        """
        :return: A list like [x, x, x, x]
        """
        return self._ip



def check_port(ip: str | Iterable[str | int] | IPV4,
               ports: int | Iterable[int], max_workers: int = 50, timeout: int | float = 1) -> dict[int, bool] | bool:
    """
    Check a port's is_open status, return bool.
    
    Setup:
        >>> my_ip = IP("127.0.0.1")
        >>> ports = list(range(1, 10001))
        >>> max_workers = 2000
    
    Example:
        >>> # print([p for p, pb in check_port(my_ip, ports, max_workers=max_workers).items() if pb])
        [example output] [1, 2, 3, ...]

    :param ip: IP will be checked.
    :param ports: Ports that want to check. (int for 1 port to check, Iterable for more ports to check.)
    :param max_workers: Max threading that would be in checking, default=50.
    :param timeout: socket.socket.settimeout, every 1 port will take timeout-sec to check.
    :return: A dict with {port: is_open}, like {1: True, 2: True, 30: False};
            or a boolean, when param ports is a port.
    :rtype: dict[int, bool] | bool
    """
    if not isinstance(ip, IPV4):
        ip = IPV4(ip)
    
    def _scan_port(port: int):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            result = s.connect_ex((str(ip), port))
        except socket.error as err:
            raise ScanError(f"Scanning {port}, an error: {err}")
        finally:
            s.close()
        return result == 0
    
    if not isinstance(ports, int):
        with ThreadPoolExecutor(max_workers=max_workers) as executors:
            results = executors.map(_scan_port, ports)
        return {port: is_open for port, is_open in zip(ports, results)}
    else:
        return _scan_port(ports)
