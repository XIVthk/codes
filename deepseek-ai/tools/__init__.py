import requests
from bs4 import BeautifulSoup

def search_web(query):
    """联网搜索（使用DuckDuckGo）"""
    try:
        # 使用 DuckDuckGo 的免费搜索API
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.select('.result')[:5]:
            title_elem = result.select_one('.result__a')
            snippet_elem = result.select_one('.result__snippet')
            if title_elem:
                title = title_elem.get_text()
                link = title_elem.get('href')
                snippet = snippet_elem.get_text() if snippet_elem else ''
                results.append(f"• {title}\n  {snippet}\n  {link}")
        
        if results:
            return "搜索结果：\n\n" + "\n\n".join(results)
        return f"未找到关于「{query}」的搜索结果"
    except Exception as e:
        return f"搜索失败：{str(e)}"

def read_link(url):
    """读取网页内容"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # 获取文本内容
        text = soup.get_text()
        # 清理多余空白
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # 限制长度
        if len(text) > 3000:
            text = text[:3000] + "...(内容已截断)"
        
        return f"网页内容：\n\n{text}"
    except Exception as e:
        return f"读取失败：{str(e)}"

def calculator(expression):
    """简单计算器"""
    try:
        # 安全计算
        allowed_names = {"abs": abs, "round": round}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"

# 工具注册表
tool_registry = {
    "search_web": search_web,
    "read_link": read_link,
    "calculator": calculator
}

def execute_tool(tool_name, arguments):
    """执行工具并返回结果"""
    if tool_name in tool_registry:
        return tool_registry[tool_name](**arguments)
    return f"未知工具：{tool_name}"