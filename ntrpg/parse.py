import enum
import random
import re


def _b(s: str, times: int) -> str:
    if not s or times >= len(s):
        return ""
    sl = list(s)
    for _ in range(times):
        sl.pop()
    return "".join(sl)


def check_deco(func):
    def wrapper(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except:
            result = None
        return result
    return wrapper


class SFStat(enum.Enum):
    BigSuccess = "大成功"
    HarderSuccess = "极难成功"
    HardSuccess = "困难成功"
    Success = "成功"
    Fail = "失败"
    BigFail = "大失败"


class Mode(enum.Enum):
    Normal = 1
    CoC = 2
    WoD = 3
    Others = 4


def parse_rc(rolled_value: int, target: int) -> SFStat:
    if 1 <= rolled_value <= 5 and rolled_value <= target:
        return SFStat.BigSuccess
    elif rolled_value <= target // 5:
        return SFStat.HarderSuccess
    elif rolled_value <= target // 2:
        return SFStat.HardSuccess
    elif rolled_value <= target:
        return SFStat.Success
    elif 96 <= rolled_value <= 100 and rolled_value >= target:
        return SFStat.BigFail
    else:
        return SFStat.Fail


def roll(dnum: int, dfce: int) -> tuple[int, str]:
    """
    :param dnum: 骰子数量。
    :param dfce: 骰子面数
    :return: 骰子结果, 格式化字符串 -> (int, str)
    """
    if dnum == 0: return 0, "🎲 0"
    rsum = 0
    lr = []
    strr = ""
    for _ in range(int(dnum)):
        rolled = random.randint(1, int(dfce))
        rsum += rolled
        lr.append(rolled)
    strr += " + ".join([str(num)for num in lr])
    if len(strr) >= 100:
        return rsum, f"🎲 {dnum}d{dfce} = ... = {rsum}"
    return rsum, f"🎲 {dnum}d{dfce} = {strr} = {rsum}"


@check_deco
def parse_cmd(s: str, user: str="System", mode: Mode = Mode.Normal) -> str | None | tuple[int, str]:
    """
    :param s: 需要解析的字符串。
    :param user: 用户名，默认为System。
    :param mode: 游戏模式，默认为Mode.Normal。
    :return:
        当输入.help时，返回帮助字符串 -> str;
        当输入.r时，返回掷骰结果字符串 -> str;
        当输入.rc时，返回判定结果字符串 -> str;
        当输入.sc时，返回扣除的san值和提示字符串构成的元组 -> (int, str)
        劣势、优势骰子判定时，返回结果和提示字符串构成的元组 -> (int, str)
    """
    if s == ".help":
        rtn =  """
            ================ 跑团助手命令单 ================
            .r <expr>: 掷骰命令, e.g. .r1d3; .r d6; .rd100
                       复杂命令, e.g. .r1d3+2d5+3; .rd6+1/2/3d3+1
            .rc <ski>/<val>[cor]: 判定命令, e.g. .rc 力量/60;
                                                .rc 敏捷/70+10-5
            .radv/.ra/.adv/.a <expr>[cor]: 优势掷骰, e.g. .ra 1d10;
                                                .radvd3; .adv d100; .a d5
            .rdis/.rd/.dis/.d <expr>[cor]: 劣势掷骰, e.g. .rd 1d10;
                                                .rdisd3; .dis d100; .d d5
            .rr [val] <expr>: 多次掷骰, e.g. .rr d10; .rr 3 3d3; .rr 5 2d10
            .help: 显示此帮助，使用.help <cmd>来查看对应命令详解。
        """
        if mode == Mode.CoC:
            rtn += """
            ================= CoC 专属命令单 =================
            .sc [val] <suc>/<fail>: SanCheck,
                e.g. .sc 80 1/1d3; .sc 1d3+1/2d4+2
            """
        return rtn
    elif re.match(r"^\.help .*$", s):
        # .help rc -> [".help", "rc"]
        _help, cmd = s.split(" ")
        if cmd in ["r", ".r"]:
            return """
                ======== .r 命令详解 ========
                抛掷一枚/多枚骰子，接受修正值。
                基本语法：.r <expression>
                .rd3 -> 1d3
                .r 1d3 -> 1d3
                .r1d3+3d6+1d100+5 -> 1d3 + 3d6 + 1d100 修正 +5
            """
        if cmd in ["rc", ".rc"]:
            return """
                ======== .rc 命令详解 ========
                进行掷骰检定，接受修正值。
                基本语法：.rc <skill>/<value>[correct]
                .rc 力量/80 -> 检定力量，骰出1d100，若值小于等于80，则成功。
                .rc 侦查/70+10 -> 检定侦查，骰出1d100，若值小于等于70(+10)，则成功。
            """
        if cmd in ["sc", ".sc"]:
            return """
                ======== .sc 命令详解 ========
                进行SanCheck。
                基本语法：.sc [value] <success>/<fail>
                .sc 80 1/1d3 -> 有80%的概率SanCheck成功，扣除1San，否则扣除1d3San
                .sc d3+3/2d5 -> 成功失败概率都是50%
            """
        if cmd in [".radv", ".adv", ".a", ".ra", "radv", "adv", "a", "ra"]:
            return """
                ======== .radv/.adv 命令详解 ========
                进行优势掷骰。
                基本语法：.radv <expression>[correct]
                         .adv <expression>[...]
                         .ra <expression>[...]
                         .a <expression>[...]
                .radv 3d10 -> 投掷2次3d10，取更好的结果。
                .ra5d5+5 -> 投掷2次5d5，取更好的结果，并修正结果+5。
                .ad10+10-8 -> 投掷2次1d10，取更好的结果，并修正结果+2。
            """
        if cmd in [".rdis", ".dis", ".rd", ".d", "rdis", "dis", "rd", "d"]:
            return """
                ======== .rdis/.dis 命令详解 ========
                进行劣势掷骰。
                基本语法：.rdis <expression>[correct]
                         .dis <expression>[...]
                         .rd <expression>[...]
                         .d <expression>[...]
                .rdis 3d10 -> 投掷2次3d10，取更差的结果。
                .rd5d5+5 -> 投掷2次5d5，取更差的结果，并修正结果+5。
                .dd10+10-8 -> 投掷2次1d10，取更差的结果，并修正结果+2。
            """
        if cmd in ["rr", ".rr"]:
            return """
                ======== .rr 命令详解 ========
                进行多次掷骰。
                基本语法：.rr [value] <expression>
                .rr 3 1d10 -> 投掷3次1d10。
                .rr d5 -> 默认投掷2次。
            """
    elif re.match(r"^\.r( )?(\d+)?d\d+$", s):
        # .r1d6 -> [".r", "1d6"]
        dp = s.split(".r")[1]  # "1d6"
        dnum, dfce = dp.split("d")
        while dnum.startswith(' '): dnum = dnum[1:]
        if not dnum:
            dnum = 1
        return user + " " + roll(int(dnum), int(dfce))[1]
    elif re.match(r"^\.r( )?((\d+/)*?((\d+)?d)*?(\d+)?(d)?(\d+)?\+)*(\d+/)*?((\d+)?d)*?(\d+)?(d)?(\d+)?$", s):
        # .r1/2d5+3d3 -> [".r", "1/2d5", "3d3"]
        strr = f'{user} 🎲 '
        rsum = 0
        dps = s.split(".r")[1].strip()  # "1/2d5+3d3"
        dp = dps.split("+")  # ["1/2d5", "3d3"]
        for dice in dp:  # idx1, dice: "1/2d5"
            strr += dice
            if not "d" in dice:
                strr += " + "
                rsum += int(dice)
                continue
            dnum, dfce = dice.split("d")  # "1/2", "5"
            if "/" in dnum:
                dnum = random.choice(dnum.split("/"))  # choice["1", "2"]
            if not dnum:
                dnum = 1
            rolled, _strr = roll(int(dnum), int(dfce))
            _strr = _strr[1:]
            strr += "(=" + _strr + ") + "
            rsum += rolled
        strr = _b(strr, 2)
        strr += f"= {rsum}"
        return strr
    elif re.match(r"^\.rc( )?.*?/\d+(([+-]?)\d+)*?$", s):
        # .rc STR/80+10-5 -> [".rc", "STR/80+10-5"]
        rcpart = s.split(".rc")[1]
        if rcpart.startswith(" "):
            rcpart = rcpart[1:]  # Delete Space
        # Accept syntax like .rcSTR/80+10-5
        # Now, rcpart is like: "STR/80+10-5"
        skill, value_wc = rcpart.split("/")
        # Although eval() can solve this, but security first
        skill_value = int(re.findall(r"^\d+", value_wc)[0])
        matches = re.findall(r"[+-]\d+", value_wc)
        for op in matches:
            if op.startswith("+"):
                op = op.split("+")[1]
                skill_value += int(op)
            else:
                op = op.split("-")[1]
                skill_value -= int(op)
        rst = roll(1, 100)[0]
        rcr = parse_rc(rst, skill_value)
        strr = f"{user} 🎲 {skill}判定: {rst}/{skill_value} -> {rcr.value}"
        return strr
    # ======== CoC Command ========
    elif re.match(r"^\.sc (\d+ )?(((\d+)?d)?\d+\+)*?((\d+)?d)?\d+/(((\d+)?d)?\d+\+)*?((\d+)?d)?\d+$", s):
        # SanCheck: .sc 80 1d3+2d5/1d3+3d10 -> [".sc", "80", "1d3+2d5/1d3+3d10"]
        _sc, *scpart = s.split(" ")  # ["80", "1d3+2d5/1d3+3d10"]
        def _san_check(obj: str, hint: str) -> tuple[int, str]:
            if not obj.isdigit():
                if "+" in obj:
                    _sum = 0
                    _s = ""
                    dices = obj.split("+")
                    for _dice in dices:
                        if not _dice.isdigit():
                            _dnum, _dfce = _dice.split("d")
                            if not _dnum: _dnum = 1
                            rtn = roll(int(_dnum), int(_dfce))
                            _sum += rtn[0]
                            _s += f"{_dnum}d{_dfce}({rtn[1][2:]}) + "
                        else:
                            _sum += int(_dice)
                            _s += _dice + " + "
                    _s = _b(_s, 2)
                    _s += f"= {_sum}"
                    return _sum, f"{user} 🎲 SanCheck {hint}，扣除 {_s} 点san值"
                else:
                    _dnum, _dfce = obj.split("d")
                    if not _dnum: _dnum = 1
                    rtn = roll(int(_dnum), int(_dfce))
                    return rtn[0], f"{user} 🎲 SanCheck {hint}，扣除 {rtn[1][2:]} 点san值"
            else:
                return int(obj), f"{user} 🎲 SanCheck {hint}，扣除 {obj} 点san值"
        if len(scpart) == 2:
            suc, fail = scpart[1].split("/")
            if random.randint(1, 100) <= int(scpart[0]):
                return _san_check(suc, "成功")
            else:
                return _san_check(fail, "失败")
        else:
            suc, fail = scpart[0].split("/")
            if random.randint(1, 100) <= 50:
                return _san_check(suc, "成功")
            else:
                return _san_check(fail, "失败")
    elif re.match(r"^\.(r)?(adv|dis|a|d)( )?(\d+)?d\d+([+-]\d+)*?$", s):
        # .r adv3d6+10 -> if adv/a? -> else -> ...
        def _handle_adv_dis(obj: str, _mode: str) -> tuple[int, str]:
            d = s.split(obj)[1]
            crt = 0
            if "+" in d or "-" in d:
                dps = re.findall(r"[+-]\d+", d)
                for dp in dps:
                    if "+" in dp: crt += int(dp[1:])
                    else: crt -= int(dp[1:])
                d = d.split("+")[0]
                d = d.split("-")[0]
            if d.startswith(" "): d = d[1:]
            dnum, dfce = d.split("d")
            if not dnum: dnum = 1
            rtn1 = roll(int(dnum), int(dfce))
            rtn2 = roll(int(dnum), int(dfce))
            if _mode == ("dis" if mode == Mode.CoC else "adv"):
                rn = max(rtn1[0], rtn2[0])
            else:
                rn = min(rtn1[0], rtn2[0])
            return rn + crt, (
        f"{user} 🎲 {'优势' if _mode == 'adv' else '劣势'} 掷骰：\n"
        f"    R1: {rtn1[1][2:]}{f' ({"+ " if crt >= 0 else ""}{crt})' if crt else ''}\n"
        f"    R2: {rtn2[1][2:]}{f' ({"+ " if crt >= 0 else ""}{crt})' if crt else ''}\n"
        f"取较{"好" if _mode == "adv" else "差"}值：{rn}{f' ({"+ " if crt >= 0 else ""}{crt} = {rn + crt})' if crt else ''}"
            )
        
        if "adv" in (o := re.match(r"^(\.(r)?(adv|dis|a|d))", s)[0]):
            return _handle_adv_dis(o, "adv")
        elif "a" in o:
            return _handle_adv_dis(o, "adv")
        else:
            return _handle_adv_dis(o, "dis")
    elif re.match(r"^\.rr (\d+ )?(((\d+)?d)?\d+\+)*?((\d+)?d)?\d+$", s):
        # .rr 5 d3+3+5d5+1 -> [".rr", "5", "d3+3+5d5+1"]
        cmdps = s.split(" ")
        if len(cmdps) == 3: _rr, times, dices = cmdps
        else: _rr, dices = cmdps; times = 2
        dpts = dices.split("+")
        strr = f"{user} 重复掷 {times} 次 {dices}：\n"
        for idx in range(1, int(times) + 1):
            strr += f"第 {idx} 次 🎲 "
            rsum = 0
            for dice in dpts:
                if not dice.isdigit():
                    dnum, dfce = dice.split("d")
                    if not dnum: dnum = 1
                    rtn = f"{dice}({(r := roll(int(dnum), int(dfce)))[1][len(dice) + 3:]}) + "
                    rsum += r[0]
                else:
                    rtn = dice + " + "
                    rsum += int(dice)
                strr += rtn
            strr = _b(strr, 2)
            strr += f"= {rsum}\n"
        return strr
    
    return None

if __name__ == '__main__':
    while (ui := input(">>> ")) not in ["quit", "exit"]:
        print(parse_cmd(ui) if parse_cmd(ui) else ui)
