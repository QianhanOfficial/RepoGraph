"""Quick API test"""
import os, sys
os.environ['OPENAI_API_KEY'] = 'sk-0bf8bee2fddb4e62aac3dd52366f564e'
os.environ['OPENAI_BASE_URL'] = 'https://api.deepseek.com'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'agentless'))

from agentless.util.api_requests import create_chatgpt_config, request_chatgpt_engine

print("Testing deepseek-v4-pro with max_tokens=50...")
config = create_chatgpt_config(
    "What is 2+2? Reply with just the number.",
    max_tokens=50, temperature=0, model='deepseek-v4-pro'
)
ret = request_chatgpt_engine(config)
content = ret.choices[0].message.content
print(f"Content: {repr(content)}")
print(f"Usage: {ret.usage}")
print("API OK!" if content else "FAIL: empty content")
