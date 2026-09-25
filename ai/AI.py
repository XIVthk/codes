"""
AI模块
"""
from openai import OpenAI
from functools import wraps


def handle_api_error(func: callable) -> callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            error = str(e)
            if "429" in error or "overload" in error.lower():
                return "服务器暂时过载，请稍后再试。"
            elif "401" in error or "auth" in error.lower():
                return "API密钥错误，请检查配置。"
            elif "quota" in error.lower() or "balance" in error.lower():
                return "API额度已用完，请充值或联系管理员。"
            elif "content_filter" in error.lower():
                return "内容被过滤，请尝试其他问题。"
            else:
                return f"处理请求时出错: {error}"
    return wrapper
    

class AI:
    def __init__(self, system_prompt: str, api_key: str, base_url: str,
                 model: str = "deepseek-ai/DeepSeek-V3",
                 max_tokens: int = 1024, temperature: float = 0.7):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.system_prompt = system_prompt
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.history = [{"role": "system", "content": self.system_prompt}]
    
    @handle_api_error
    def ask(self, question: str) -> str:
        self._add_history("user", question)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        assistant_response = response.choices[0].message.content
        self._add_history("assistant", assistant_response)
        return assistant_response
    
    def _add_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
    
    def clear_history(self):
        self.history = [{"role": "system", "content": self.system_prompt}]
    
    def system(self, content: str):
        self.history[0] = {"role": "system", "content": content}
        self.system_prompt = content
    
    def revert(self, rounds: int = 1):
        if rounds <= 0 or len(self.history) <= 1:
            return
        
        keep_count = max(1, len(self.history) - rounds * 2)
        self.history = self.history[:keep_count]
    
    def reask(self, round_index: int = -1) -> str:
        if len(self.history) <= 1:
            return "没有历史对话可以重新提问"
        
        user_messages = []
        for i, msg in enumerate(self.history):
            if msg["role"] == "user":
                user_messages.append((i, msg["content"]))
        
        if not user_messages:
            return "没有找到用户消息"
        
        if round_index < 0:
            round_index = len(user_messages) + round_index
        
        if round_index < 0 or round_index >= len(user_messages):
            return f"轮次索引超出范围: 0-{len(user_messages)-1}"
        
        msg_index, question = user_messages[round_index]
        
        self.history = self.history[:msg_index]
        
        return self.ask(question)
    
    def get_conversation_stats(self):
        user_count = sum(1 for msg in self.history if msg["role"] == "user")
        assistant_count = sum(1 for msg in self.history if msg["role"] == "assistant")
        system_count = sum(1 for msg in self.history if msg["role"] == "system")
        
        return {
            "total_messages": len(self.history),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "system_messages": system_count,
            "conversation_rounds": min(user_count, assistant_count)
        }
    
    def __len__(self):
        user_count = sum(1 for msg in self.history if msg["role"] == "user")
        assistant_count = sum(1 for msg in self.history if msg["role"] == "assistant")
        return min(user_count, assistant_count)
    
    def __getitem__(self, index: int):
        if index < 0 or index >= len(self):
            raise IndexError("对话轮数索引超出范围")
        
        user_found = 0
        for i, msg in enumerate(self.history):
            if msg["role"] == "user":
                if user_found == index:
                    return [msg, self.history[i+1]] if i+1 < len(self.history) else [msg]
                user_found += 1
        return []


if __name__ == "__main__":
    ai = AI(
        system_prompt="你是一个智能助手",
        api_key="sk-bsgrenbiomfmezwyiijfurpnbwssedezvobnxdyhqbiakiud",
        base_url="https://api.siliconflow.cn/v1"
    )
    
    print("可用命令:")
    print("  'exit' - 退出")
    print("  'clear' - 清空历史")
    print("  'revert N' - 回退N轮对话")
    print("  'reask N' - 重新询问第N轮问题 (N从0开始，-1表示最后一轮)")
    print("  'stats' - 查看对话统计")
    print("  其他 - 正常对话")
    
    while True:
        question = input("\n用户: ").strip()
        if not question:
            continue
            
        if question == "exit":
            break
        elif question == "clear":
            ai.clear_history()
            print("历史已清空")
            continue
        elif question == "stats":
            stats = ai.get_conversation_stats()
            print(f"对话统计: {stats}")
            continue
        elif question.startswith("revert"):
            try:
                parts = question.split()
                rounds = int(parts[1]) if len(parts) > 1 else 1
                ai.revert(rounds)
                print(f"已回退 {rounds} 轮对话")
            except ValueError:
                print("请提供有效的数字")
            continue
        elif question.startswith("reask"):
            try:
                parts = question.split()
                round_index = int(parts[1]) if len(parts) > 1 else -1
                response = ai.reask(round_index)
                print(f"助手: {response}")
            except ValueError:
                print("请提供有效的数字")
            continue
        else:
            response = ai.ask(question)
            print(f"助手: {response}")