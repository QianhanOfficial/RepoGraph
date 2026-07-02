#!/usr/bin/env python3
"""Quick single-instance test for RepoGraph + Agentless"""
import os
import sys

# SSL fix must be FIRST
import ssl, certifi
_orig_create_default_context = ssl.create_default_context
def _patched_create_default_context(*args, **kwargs):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(certifi.where())
    return ctx
ssl._create_default_https_context = _patched_create_default_context
ssl.create_default_context = _patched_create_default_context

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'agentless'))

# API config
os.environ.setdefault('OPENAI_API_KEY', 'your-api-key')
os.environ.setdefault('OPENAI_BASE_URL', 'https://api.deepseek.com')

# Quick API test
from agentless.util.api_requests import create_chatgpt_config, request_chatgpt_engine
print("Testing DeepSeek API...")
config = create_chatgpt_config("Say hello in one word", max_tokens=10, temperature=0, model='deepseek-v4-pro')
ret = request_chatgpt_engine(config)
print(f"API OK: {ret.choices[0].message.content}")

print("\nAll systems ready! Run:")
print("  bash run_repograph_agentless.sh")
