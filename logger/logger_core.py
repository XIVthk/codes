class Logger:
    def __init__(self):
        self._indent = 0
        self.logs = []
    
    def log(self, level, message):
        mapping = {
            "+": "[+]",  # successed/okay
            "-": "[-]",  # failed/refused
            "*": "[*]",  # info
            "#": "[#]",  # fatal
            "^": "[^]",  # warning
            "!": "[!]",  # error
            ";": "[;]",  # debug
            "?": "[?]",  # question
            ">": "[>]",  # heartbeat
            "_": "[_]",  # unclassified
            "=": "[=]",  # command
            "\n": "",
        }
        level = mapping.get(level.lower(), "[_]") if level not in mapping.values() else level
        line = "    " * self._indent + f"{level} {message}"
        self.logs.append(line)
        print(line)

    def indent(self):
        self._indent += 1
    
    def dedent(self):
        self._indent -= 1
    
    def save_logs(self, filename="log.txt"):
        with open(filename, "w") as f:
            f.write("\n".join(self.logs))
