from enum import Enum
import requests


ERROR_KEYWORDS = ['sql', 'mysql', 'postgresql', 'oracle', 'database', 
                 'syntax', 'error', 'warning', 'exception', 'stack trace']

class HTTPError(Exception):
    pass


class HTTPStatus(Enum):
    OK = 200
    NotFound = 404
    InternalError = 500
    Forbidden = 403

class SQLTestStatus(Enum):
    OK = 0
    MayBugFound = 1
    BugFound = 2
    Error = 3


def _error_found(text: str) -> bool:
    tl = text.lower()
    return any(keyword in tl for keyword in ERROR_KEYWORDS)


def sql_test(url: str, params: list[str], method: str, *payloads) -> list[tuple[SQLTestStatus, dict[str, str | int]]]:
    """
    General SQL Injection Testing Function
    
    Setup:
    >>> url = "http://testphp.vulnweb.com/artists.php"
    >>> params = ["artist"]
    >>> payloads = ["' or 1='1", "'"]

    Example:
    >>> sql_test(url, params, 'GET', *payloads)
    [(<SQLTestStatus.BugFound: 2>, {'artist': "' or 1='1"}), (<SQLTestStatus.BugFound: 2>, {'artist': "'"})]
    >>> sql_test(url, params, 'POST', *payloads)
    [(<SQLTestStatus.OK: 0>, {'artist': "' or 1='1"}), (<SQLTestStatus.OK: 0>, {'artist': "'"})]

    :param url: Target URL
    :param params: Parameter list
    :param method: Request method, 'GET' or 'POST'
    :param payloads: Payload list
    :return: List of (SQLTestStatus, {parameter: value})
    """
    if len(params) == 0 or len(payloads) == 0:
        raise ValueError("No parameter or no payload provided.")
    if method not in ['GET', 'POST']:
        raise ValueError("Method must be 'GET' or 'POST'")
        
    rtn = []
    for param in params:
        try:
            if method == 'GET':
                base_url = f"{url}?{param}=1"
                base_response = requests.get(base_url)
            else:  # POST
                base_data = {param: "1"}
                base_response = requests.post(url, data=base_data)
        except requests.exceptions.ConnectionError:
            raise HTTPError("Connection timeout")
            
        if base_response.status_code != HTTPStatus.OK.value:
            raise HTTPError(f"HTTP Error: {base_response.status_code}, reason: {base_response.reason}")
        
        for payload in payloads:
            try:
                if method == 'GET':
                    test_url = f"{url}?{param}={payload}"
                    response = requests.get(test_url)
                else:  # POST
                    test_data = {param: payload}
                    response = requests.post(url, data=test_data)
            except requests.exceptions.ConnectionError:
                raise HTTPError("Connection timeout")
                
            if response.status_code != HTTPStatus.OK.value:
                rtn.append((SQLTestStatus.Error, {param: payload, "errorcode": response.status_code}))
                continue
                
            if base_response.text != response.text:
                if _error_found(response.text):
                    rtn.append((SQLTestStatus.BugFound, {param: payload}))
                else:
                    rtn.append((SQLTestStatus.MayBugFound, {param: payload}))
                continue
                
            rtn.append((SQLTestStatus.OK, {param: payload}))
        
    return rtn


def readable_sqltest_report(url: str, params: list[str], *payloads) -> str:
    """
    Generate a readable report of SQL injection testing result.

    Setup:
        >>> url = "http://testphp.vulnweb.com/artists.php"
        >>> params = ["artist"]
        >>> payloads = ["' or 1='1"]
    
    Example:
        >>> print(readable_sqltest_report(url, params, *payloads))
        ============= GET =============
        [-] Param "artist":
            Payload "' or 1='1" causes bug found.
                -> http://testphp.vulnweb.com/artists.php?artist=' or 1='1

        Param "artist":
            Safe: 0 - 0%
            MayBug: 0 - 0%
            Bug: 1 - 100%
            Error: 0 - 0%

        ============= POST =============
        [+] Param "artist":
            Payload "' or 1='1" is safe.
                -> POST to http://testphp.vulnweb.com/artists.php with data {'artist': '' or 1='1'}

        Param "artist":
            Safe: 1 - 100%
            MayBug: 0 - 0%
            Bug: 0 - 0%
            Error: 0 - 0%
    
    :param url: Target URL
    :param params: Parameter list
    :param payloads: Payload list
    :return: Readable report string, str
    """
    rtn = ""
    def _wrapper(func: callable, method: str) -> str:
        nonlocal rtn
        rtn = ""
        number_listing = {}
        for result in func(url, params, method, *payloads):
            status, payload = result
            param = list(payload).pop()
            plv = payload[param]
            if method == "GET":
                urlstr = f"\t-> {url}?{param}={plv}\n"
            else:
                urlstr = f"\t-> POST to {url} with data {{\"{param}\": \"{plv}\"}}\n"

            if param not in number_listing:
                number_listing[param] = {"safe": 0, "maybug": 0, "bug": 0, "error": 0}
            match status:
                case SQLTestStatus.OK:
                    rtn += (f"[+] Param \"{param}\":\n"
                            f"    Payload \"{plv}\" is safe.\n" +
                            urlstr)
                    number_listing[param]["safe"] += 1
                case SQLTestStatus.MayBugFound:
                    rtn += (f"[?] Param \"{param}\":\n"
                            f"    Payload \"{plv}\" may cause bug found.\n" +
                            urlstr)
                    number_listing[param]["maybug"] += 1
                case SQLTestStatus.BugFound:
                    rtn += (f"[-] Param \"{param}\":\n"
                            f"    Payload \"{plv}\" causes bug found.\n" +
                            urlstr)
                    number_listing[param]["bug"] += 1
                case SQLTestStatus.Error:
                    rtn += (f"[x] Param \"{param}\":\n"
                            f"    Payload \"{plv}\" caused error.\n" +
                            urlstr +
                            f"\t   Code {payload['errorcode']}\n")
                    number_listing[param]["error"] += 1

        for param, number in number_listing.items():
                all_tests = sum(number.values())
                rtn += (f"\nParam \"{param}\":\n"
                        f"    Safe: {number['safe']} - {round(number['safe'] / all_tests * 100)}%\n"
                        f"    MayBug: {number['maybug']} - {round(number['maybug'] / all_tests * 100)}%\n"
                        f"    Bug: {number['bug']} - {round(number['bug'] / all_tests * 100)}%\n"
                        f"    Error: {number['error']} - {round(number['error'] / all_tests * 100)}%\n")
                rtn += "\n"
        return rtn
    
    # GET test
    rtn += "============= GET =============\n"
    rtn += _wrapper(sql_test, method="GET")
    rtn += "\n"
    
    # POST test
    rtn += "============= POST =============\n"
    rtn += _wrapper(sql_test, method="POST")
    return rtn
