def dget(data: dict, path: str, default=None, sep: str = "."):
    index = path.find(sep)
    if index == -1: return data.get(path, default)
    if path[:index] not in data: return default
    return dget(data=data[path[:index]], path=path[index+1:], default=default, sep=sep)

def dset(data: dict, path: str, value, sep: str = "."):
    index = path.find(sep)
    if index == -1: data[path] = value; return data
    key = path[:index]
    if key not in data: data[key] = {}
    dset(data[key], path[index+len(sep):], value, sep)
    return data

def ddel(data: dict, path: str, sep: str = "."):
    index = path.find(sep)
    if index == -1: del data[path]; return data
    key = path[:index]
    if key not in data: return data
    ddel(data[key], path[index+len(sep):], sep)
    return data

