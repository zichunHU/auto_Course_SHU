# encrypt.py
"""
encrypt.py
~~~~~~~~~~
封装密码加密逻辑：使用学校公钥做 RSA，加密后返回 Base64 字符串。
"""

import base64
import rsa
from loguru import logger

# ------------------------------------------------------------------ #
# 公钥常量：如官方变更，只需在此处替换
# ------------------------------------------------------------------ #
PUB_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDl/aCgRl9f/4ON9MewoVnV58OL
OU2ALBi2FKc5yIsfSpivKxe7A6FitJjHva3WpM7gvVOinMehp6if2UNIkbaN+plW
f5IwqEVxsNZpeixc4GsbY9dXEk3WtRjwGSyDLySzEESH/kpJVoxO7ijRYqU+2oSR
wTBNePOk1H+LRQokgQIDAQAB
-----END PUBLIC KEY-----"""

def _load_pubkey(pem: str) -> rsa.PublicKey:
    """
    将 PEM 格式公钥字符串加载为 rsa.PublicKey 对象。
    :param pem: PEM 格式公钥文本
    :return: rsa.PublicKey
    """
    return rsa.PublicKey.load_pkcs1_openssl_pem(pem.encode())

def encrypt(plain_pwd: str) -> str:
    """
    加密明文密码，返回 Base64 编码后的密文字符串。
    :param plain_pwd: 用户输入的明文密码
    :return: Base64 编码的 RSA 密文
    """
    # 1. 加载公钥
    key = _load_pubkey(PUB_KEY_PEM)
    # 2. 使用公钥加密密码，结果为二进制
    cipher = rsa.encrypt(plain_pwd.encode(), key)
    # 3. 将二进制密文进行 Base64 编码并返回
    encoded = base64.b64encode(cipher).decode()
    logger.debug("密码加密完成 (前 20 位)：{}", encoded[:20])
    return encoded