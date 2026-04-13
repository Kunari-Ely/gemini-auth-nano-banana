#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
Edge 浏览器 Gemini/Google Cookie 解密提取工具
==============================================================================

功能描述:
    从本地 Microsoft Edge 浏览器的 Cookie 数据库中提取并解密 Gemini/Google
    相关的登录 Cookie，导出为 JSON 文件。

技术背景:
    Edge (Chromium 127+) 使用 v20 "App-Bound Encryption" 加密 Cookie。
    这是一种双层 DPAPI 加密机制，密钥绑定到浏览器应用本身:
      - 第一层: SYSTEM 级别的 DPAPI 加密 (需要 NT AUTHORITY\\SYSTEM 权限)
      - 第二层: 用户级别的 DPAPI 加密 (当前用户即可)
    解密后再通过 AES-256-GCM 解密具体的 Cookie 值。

运行环境要求:
    - 操作系统: Windows 10/11
    - Python: 3.8+
    - 权限: 必须以 Administrator 身份运行 (需要 SeDebugPrivilege)
    - Edge 状态: Edge 可以是打开或关闭状态
        - Edge 关闭时: 直接读取 Cookie 数据库
        - Edge 运行时: 使用 copy/robocopy 复制数据库副本绕过文件锁

依赖安装:
    pip install pywin32 cryptography

使用方法:
    python extract_gemini_cookies.py

输出:
    1. 控制台打印所有解密后的关键 Cookie
    2. 在脚本同目录下生成 gemini_cookies.json 文件

输出 JSON 格式:
    {
      "login_cookies": {
        "__Secure-1PSID": "...",
        "__Secure-1PSIDTS": "...",
        "SID": "...",
        ...
      },
      "gemini_cookies": {
        "_ga": "...",
        ...
      }
    }

注意事项:
    1. __Secure-1PSIDTS 等 TS 类 Cookie 会定期轮换 (约每几分钟),
       如果用于 API 认证, 应在使用前重新提取
    2. 脚本通过 winlogon.exe 进程获取 SYSTEM token, 需要 SeDebugPrivilege,
       因此必须以 Administrator 权限运行
    3. 如果提取失败, 常见原因:
       - 未以管理员权限运行
       - Edge 从未登录过 Google 账号
       - Edge 版本过旧 (不支持 v20 加密)
       - 杀毒软件阻止了进程 token 操作
    4. Cookie 数据库路径默认为 Default Profile, 如使用其他 Profile
       需修改 COOKIE_DB_PATH 中的 "Default" 为对应 Profile 名称
    5. 本工具仅用于本机合法用途，请勿用于未授权访问

作者: AI Assistant
日期: 2026-04-13
==============================================================================
"""

import os
import sys
import io
import json
import base64
import sqlite3
import shutil
import tempfile
import ctypes
import subprocess
from ctypes import wintypes

# ============================================================================
# 修复 Windows 控制台 GBK 编码问题，确保 emoji 和中文正常输出
# ============================================================================
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# 第三方依赖
# ============================================================================
import win32crypt          # pywin32: Windows DPAPI 加解密
import win32api            # pywin32: Windows API 封装
import win32con            # pywin32: Windows 常量定义
import win32security       # pywin32: 安全相关 API
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # AES-GCM 解密
from datetime import datetime, timedelta

# ============================================================================
# Windows API 常量
# ============================================================================
TOKEN_ALL_ACCESS = 0xF01FF              # Token 完全访问权限
TOKEN_DUPLICATE = 0x0002                # 允许复制 Token
TOKEN_QUERY = 0x0008                    # 允许查询 Token
PROCESS_QUERY_INFORMATION = 0x0400      # 允许查询进程信息
SecurityImpersonation = 2               # 模拟安全级别
TokenPrimary = 1                        # 主 Token 类型

# ============================================================================
# 路径配置 (可按需修改)
# ============================================================================
# Edge 用户数据根目录
EDGE_USER_DATA = os.path.join(
    os.environ['LOCALAPPDATA'],
    'Microsoft', 'Edge', 'User Data'
)
# Local State 文件 (包含加密密钥)
LOCAL_STATE_PATH = os.path.join(EDGE_USER_DATA, 'Local State')
# Cookie 数据库路径 (Default Profile, 如用其他 Profile 请修改 "Default")
COOKIE_DB_PATH = os.path.join(EDGE_USER_DATA, 'Default', 'Network', 'Cookies')


def get_v20_key():
    """
    获取 v20 App-Bound Encryption 的 AES-256 解密密钥。

    解密流程:
        1. 启用 SeDebugPrivilege (需要 Administrator)
        2. 从 winlogon.exe 进程获取 SYSTEM token
        3. 从 Local State 读取 Base64 编码的 app_bound_encrypted_key
        4. 去掉 "APPB" 前缀 (4 bytes), 剩余部分是 DPAPI blob
        5. 以 SYSTEM 身份执行第一层 DPAPI 解密
        6. 以当前用户身份执行第二层 DPAPI 解密
        7. 从解密结果的最后 32 字节提取 AES-256 密钥

    解密结果结构 (72 bytes):
        [0:4]   - 长度头 (0x20000000 = 32)
        [4:5]   - 标志位
        [5:40]  - Edge 安装路径字符串 + padding
        [40:72] - 32 字节 AES-256 密钥

    Returns:
        bytes: 32 字节的 AES-256 密钥, 失败返回 None
    """
    # === 步骤 1: 启用 SeDebugPrivilege ===
    # 这是打开 winlogon.exe 进程的前提条件
    priv_id = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
    hToken = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
    )
    win32security.AdjustTokenPrivileges(
        hToken, False, [(priv_id, win32security.SE_PRIVILEGE_ENABLED)]
    )
    print("✅ 已启用 SeDebugPrivilege")

    # === 步骤 2: 从 winlogon.exe 获取 SYSTEM token ===
    # winlogon.exe 始终以 SYSTEM 身份运行, 从它复制 token 来模拟 SYSTEM
    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32

    result = subprocess.run(
        ['tasklist', '/FI', 'IMAGENAME eq winlogon.exe', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True
    )

    system_token = None
    for line in result.stdout.strip().split('\n'):
        if 'winlogon' in line.lower():
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 2:
                pid = int(parts[1].strip('"'))

                # 打开 winlogon 进程
                hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
                if not hProcess:
                    continue

                # 打开进程 token
                hToken2 = wintypes.HANDLE()
                advapi32.OpenProcessToken(
                    hProcess, TOKEN_DUPLICATE | TOKEN_QUERY, ctypes.byref(hToken2)
                )

                # 复制 token (Impersonation -> Primary)
                hDup = wintypes.HANDLE()
                advapi32.DuplicateTokenEx(
                    hToken2, TOKEN_ALL_ACCESS, None,
                    SecurityImpersonation, TokenPrimary, ctypes.byref(hDup)
                )

                kernel32.CloseHandle(hToken2)
                kernel32.CloseHandle(hProcess)
                system_token = hDup
                print(f"✅ 获取 SYSTEM token (winlogon PID: {pid})")
                break

    if not system_token:
        print("❌ 无法获取 SYSTEM token (请确认以 Administrator 身份运行)")
        return None

    # === 步骤 3: 读取 app_bound_encrypted_key ===
    with open(LOCAL_STATE_PATH, 'r', encoding='utf-8') as f:
        local_state = json.load(f)

    app_key_b64 = local_state['os_crypt'].get('app_bound_encrypted_key')
    if not app_key_b64:
        print("❌ 未找到 app_bound_encrypted_key (Edge 版本可能过旧)")
        return None

    app_key_raw = base64.b64decode(app_key_b64)

    # 验证 "APPB" 前缀
    if app_key_raw[:4] != b'APPB':
        print("❌ 密钥格式不正确 (缺少 APPB 前缀)")
        return None

    # 去掉 4 字节 "APPB" 前缀，剩余是 DPAPI blob
    dpapi_blob = app_key_raw[4:]

    # === 步骤 4: 第一层 DPAPI 解密 (SYSTEM 权限) ===
    # 模拟 SYSTEM 用户身份来调用 CryptUnprotectData
    advapi32.ImpersonateLoggedOnUser(system_token)
    try:
        first_decrypt = win32crypt.CryptUnprotectData(dpapi_blob, None, None, None, 0)[1]
    finally:
        advapi32.RevertToSelf()  # 恢复原始用户身份
    print("✅ SYSTEM DPAPI 解密成功")

    # === 步骤 5: 第二层 DPAPI 解密 (用户权限) ===
    # 第一层解密的结果是另一个 DPAPI blob, 用当前用户身份解密
    second_decrypt = win32crypt.CryptUnprotectData(first_decrypt, None, None, None, 0)[1]
    print("✅ User DPAPI 解密成功")

    # === 步骤 6: 提取 AES-256 密钥 ===
    # 解密结果为 72 字节, 最后 32 字节是 AES-256 密钥
    key = second_decrypt[-32:]
    print(f"✅ AES 密钥提取完成 ({len(key)} bytes)")

    return key


def decrypt_cookie(encrypted_value, v20_key):
    """
    解密单个 Cookie 值。

    支持三种加密格式:
        - v20: App-Bound Encryption (Chromium 127+, 当前 Edge 主要使用)
        - v10: 旧版 AES-GCM (使用 Local State 中的 encrypted_key)
        - 无前缀: 更早期的纯 DPAPI 加密

    Cookie 加密值结构 (v10/v20):
        [0:3]   - 版本前缀 ("v10" 或 "v20")
        [3:15]  - 12 字节 AES-GCM nonce/IV
        [15:]   - AES-GCM 密文 + 16 字节 auth tag

    v20 解密后数据结构:
        [0:32]  - 32 字节校验前缀 (丢弃)
        [32:]   - 实际 Cookie 明文值

    Args:
        encrypted_value: bytes, 数据库中的加密 Cookie 值
        v20_key: bytes, 32 字节 AES-256 密钥

    Returns:
        str: 解密后的 Cookie 明文值
    """
    if not encrypted_value or len(encrypted_value) < 4:
        return ""

    prefix = encrypted_value[:3]

    if prefix == b'v20':
        # === v20: App-Bound Encryption ===
        nonce = encrypted_value[3:15]       # 12 字节 nonce
        ciphertext = encrypted_value[15:]   # 密文 + auth tag
        try:
            aesgcm = AESGCM(v20_key)
            plain = aesgcm.decrypt(nonce, ciphertext, None)
            # 跳过前 32 字节的校验前缀, 取实际值
            return plain[32:].decode('utf-8', errors='replace')
        except Exception as e:
            return f"[v20解密失败: {e}]"

    elif prefix == b'v10':
        # === v10: 旧版 AES-GCM (使用 encrypted_key) ===
        try:
            with open(LOCAL_STATE_PATH, 'r', encoding='utf-8') as f:
                ls = json.load(f)
            # encrypted_key 格式: "DPAPI" (5 bytes) + DPAPI blob
            v10_key_raw = base64.b64decode(ls['os_crypt']['encrypted_key'])[5:]
            v10_key = win32crypt.CryptUnprotectData(v10_key_raw, None, None, None, 0)[1]
            nonce = encrypted_value[3:15]
            ciphertext = encrypted_value[15:]
            aesgcm = AESGCM(v10_key)
            return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8', errors='replace')
        except Exception as e:
            return f"[v10解密失败: {e}]"

    else:
        # === 旧版: 纯 DPAPI 加密 (无版本前缀) ===
        try:
            return win32crypt.CryptUnprotectData(
                encrypted_value, None, None, None, 0
            )[1].decode('utf-8', errors='replace')
        except:
            return "[DPAPI解密失败]"


def chrome_ts(ts):
    """
    将 Chromium 时间戳转为可读格式。
    Chromium 使用 1601-01-01 UTC 为起点的微秒时间戳。
    """
    if ts == 0:
        return "永不过期"
    try:
        return (datetime(1601, 1, 1) + timedelta(microseconds=ts)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)


def main():
    """
    主函数: 提取并导出 Gemini/Google 登录 Cookie。

    执行流程:
        1. 调用 get_v20_key() 获取 AES 解密密钥
        2. 复制 Cookie 数据库到临时目录 (避免文件锁)
        3. 查询并解密所有 Google 域下的关键 Cookie
        4. 查询并解密 gemini.google.com 域下的所有 Cookie
        5. 导出结果到 gemini_cookies.json
    """
    print("=" * 60)
    print("  Edge Gemini Cookie 提取工具")
    print("=" * 60)
    print()

    # === 获取解密密钥 ===
    v20_key = get_v20_key()
    if not v20_key:
        return

    # === 复制 Cookie 数据库 ===
    # Edge 运行时数据库被锁, 需要复制一份来读取
    # 方法1: Windows copy 命令
    # 方法2: robocopy (更强的复制能力)
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, 'Cookies')
    ret = os.system(f'copy /Y "{COOKIE_DB_PATH}" "{temp_db}" >nul 2>&1')
    if ret != 0:
        src_dir = os.path.dirname(COOKIE_DB_PATH)
        os.system(f'robocopy "{src_dir}" "{temp_dir}" "Cookies" /R:1 /W:0 >nul 2>&1')

    if not os.path.exists(temp_db):
        print("❌ 无法复制 Cookie 数据库 (请尝试关闭 Edge 后重试)")
        return

    try:
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()

        # 关键登录 Cookie 名称列表
        # 这些是 Google 认证体系中最重要的 Cookie
        important_names = [
            '__Secure-1PSID',       # 主要的认证会话 ID (最常用)
            '__Secure-3PSID',       # 第三方上下文的会话 ID
            '__Secure-1PSIDTS',     # 会话时间戳 (频繁轮换, 约几分钟一次)
            '__Secure-3PSIDTS',     # 第三方会话时间戳
            '__Secure-1PSIDCC',     # 会话一致性校验
            '__Secure-3PSIDCC',     # 第三方会话一致性校验
            'SID',                  # 传统会话 ID
            'HSID',                 # HTTP 安全会话 ID
            'SSID',                 # 安全会话 ID
            'APISID',              # API 会话 ID
            'SAPISID',             # 安全 API 会话 ID
            '__Secure-1PAPISID',   # 安全 API 会话 ID (第一方)
            '__Secure-3PAPISID',   # 安全 API 会话 ID (第三方)
            'NID',                  # Google 偏好设置 Cookie
            '__Secure-ENID',       # 加密 NID
        ]

        # === 查询 Google 域下的所有 Cookie ===
        cur.execute("""
            SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly
            FROM cookies
            WHERE host_key LIKE '%.google.com%'
            ORDER BY host_key, name
        """)
        all_rows = cur.fetchall()

        # 按 (域名, Cookie名) 去重
        seen = set()
        unique = []
        for r in all_rows:
            k = (r[0], r[1])
            if k not in seen:
                seen.add(k)
                unique.append(r)

        print("\n" + "=" * 80)
        print("🔑 Gemini/Google 关键登录 Cookie")
        print("=" * 80)

        found_important = []
        found_names = set()
        export_data = {}

        for host, name, enc_val, path, expires, secure, httponly in unique:
            if name in important_names:
                value = decrypt_cookie(enc_val, v20_key)
                found_important.append((host, name, value, path, expires))
                found_names.add(name)
                export_data[name] = value

                print(f"\n📌 {name}")
                print(f"   域名: {host}")
                print(f"   路径: {path}")
                print(f"   过期: {chrome_ts(expires)}")
                print(f"   Secure: {bool(secure)} | HttpOnly: {bool(httponly)}")
                if len(value) > 100:
                    print(f"   值: {value[:100]}...")
                else:
                    print(f"   值: {value}")

        if not found_important:
            print("\n⚠️ 未找到关键登录 Cookie (请确认已在 Edge 中登录 Google)")

        missing = [n for n in important_names if n not in found_names]
        if missing:
            print(f"\n⚠️ 缺失: {', '.join(missing)}")

        # === 查询 gemini.google.com 域下的 Cookie ===
        cur.execute("""
            SELECT host_key, name, encrypted_value, path, expires_utc
            FROM cookies
            WHERE host_key LIKE '%gemini%'
            ORDER BY name
        """)
        gemini_rows = cur.fetchall()

        print("\n" + "=" * 80)
        print("🌐 gemini.google.com 域 Cookie")
        print("=" * 80)

        gemini_export = {}
        for host, name, enc_val, path, expires in gemini_rows:
            value = decrypt_cookie(enc_val, v20_key)
            gemini_export[name] = value
            print(f"\n  {name}")
            print(f"   域名: {host}")
            if len(value) > 100:
                print(f"   值: {value[:100]}...")
            else:
                print(f"   值: {value}")

        if not gemini_rows:
            print("\n  (无)")

        # === 导出为 JSON ===
        output = {
            "login_cookies": export_data,
            "gemini_cookies": gemini_export,
        }
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gemini_cookies.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 80)
        print(f"📁 已导出到: {json_path}")
        print(f"📊 共 {len(found_important)} 个关键 Cookie, {len(gemini_rows)} 个 Gemini Cookie")
        print("=" * 80)

        conn.close()
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
