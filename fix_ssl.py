"""
修复 Python 3.9 Windows SSL 证书问题的 monkeypatch。
在导入 datasets 之前 import 此模块。
"""
import ssl

_orig_create_default_context = ssl.create_default_context

def _patched_create_default_context(*args, **kwargs):
    """绕过 Windows 证书存储加载问题"""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return ctx

ssl.create_default_context = _patched_create_default_context
