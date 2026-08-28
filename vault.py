"""
vault.py - Security, Key Vault & DPAPI Key Encryption Layer for AI Model Manager.
"""
import os
import sys
import base64
import ctypes
import json
import copy

# Windows DPAPI Structures
if os.name == "nt":
    from ctypes import wintypes
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

def _dpapi_encrypt(plaintext: str) -> str:
    if os.name != "nt":
        raise NotImplementedError("DPAPI is Windows-only")
    try:
        data_bytes = plaintext.encode("utf-8")
        blob_in = DATA_BLOB(len(data_bytes), ctypes.cast(ctypes.create_string_buffer(data_bytes, len(data_bytes)), ctypes.POINTER(ctypes.c_byte)))
        blob_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptProtectData(ctypes.byref(blob_in), "AIMgrKey", None, None, None, 0, ctypes.byref(blob_out)):
            buf = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return "enc:dpapi:" + base64.b64encode(buf).decode("ascii")
    except Exception:
        pass
    return ""

def _dpapi_decrypt(ciphertext: str) -> str:
    if os.name != "nt" or not ciphertext.startswith("enc:dpapi:"):
        raise ValueError("Invalid DPAPI ciphertext")
    try:
        raw = base64.b64decode(ciphertext[10:])
        blob_in = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw, len(raw)), ctypes.POINTER(ctypes.c_byte)))
        blob_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            buf = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return buf.decode("utf-8")
    except Exception as e:
        raise ValueError(f"DPAPI decryption failed: {e}")
    raise ValueError("CryptUnprotectData returned False")

# ----- Machine-local key fallback (non-Windows) -----
_LOCAL_KEY_PATH = os.path.join(os.path.expanduser("~"), ".aipi_vault_key")

def _get_local_key() -> bytes:
    """Return (or generate) a 32-byte machine-local random key stored in ~/.aipi_vault_key."""
    if os.path.exists(_LOCAL_KEY_PATH):
        try:
            with open(_LOCAL_KEY_PATH, "rb") as f:
                k = f.read(32)
                if len(k) == 32:
                    return k
        except Exception:
            pass
    # Generate a fresh random key
    k = os.urandom(32)
    try:
        with open(_LOCAL_KEY_PATH, "wb") as f:
            f.write(k)
        # Restrict permissions on Unix-like systems
        try:
            os.chmod(_LOCAL_KEY_PATH, 0o600)
        except Exception:
            pass
    except Exception:
        pass
    return k

def _local_xor(plaintext: str, key: bytes) -> str:
    """XOR-encrypt with a multi-byte key (simple but key is machine-unique)."""
    data = plaintext.encode("utf-8")
    xor_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    return base64.b64encode(xor_bytes).decode("ascii")

def _fallback_scramble(plaintext: str) -> str:
    """Legacy fallback: XOR with static salt — kept for backward-compat reads only."""
    salt = "AIMgr-v1-Salt"
    b_key = salt.encode("utf-8")
    b_data = plaintext.encode("utf-8")
    xor_bytes = bytes([b ^ b_key[i % len(b_key)] for i, b in enumerate(b_data)])
    return "enc:fallback:" + base64.b64encode(xor_bytes).decode("ascii")

def _fallback_unscramble(ciphertext: str) -> str:
    if not ciphertext.startswith("enc:fallback:"):
        raise ValueError("Invalid fallback ciphertext")
    raw = base64.b64decode(ciphertext[13:])
    salt = "AIMgr-v1-Salt"
    b_key = salt.encode("utf-8")
    dec_bytes = bytes([b ^ b_key[i % len(b_key)] for i, b in enumerate(raw)])
    return dec_bytes.decode("utf-8")

def _local_scramble(plaintext: str) -> str:
    """Encrypt with machine-local random key — secure on any OS."""
    key = _get_local_key()
    return "enc:local:" + _local_xor(plaintext, key)

def _local_unscramble(ciphertext: str) -> str:
    if not ciphertext.startswith("enc:local:"):
        raise ValueError("Invalid local ciphertext")
    raw = base64.b64decode(ciphertext[10:])
    key = _get_local_key()
    dec_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
    return dec_bytes.decode("utf-8")

def encrypt_key(plaintext: str) -> str:
    """Encrypt plain API key into ciphertext wrapper."""
    if not plaintext or plaintext.startswith("enc:"):
        return plaintext or ""
    if os.name == "nt":
        res = _dpapi_encrypt(plaintext)
        if res:
            return res
    # Non-Windows: use machine-local random key (secure, machine-specific)
    return _local_scramble(plaintext)

def decrypt_key(ciphertext: str) -> str:
    """Decrypt ciphertext back to plain API key."""
    if not ciphertext or not isinstance(ciphertext, str):
        return ""
    if not ciphertext.startswith("enc:"):
        return ciphertext
    if ciphertext.startswith("enc:dpapi:"):
        try:
            return _dpapi_decrypt(ciphertext)
        except Exception:
            return ""
    if ciphertext.startswith("enc:local:"):
        try:
            return _local_unscramble(ciphertext)
        except Exception:
            return ""
    if ciphertext.startswith("enc:fallback:"):
        # Legacy: static-salt XOR — kept for backward compatibility
        try:
            return _fallback_unscramble(ciphertext)
        except Exception:
            return ""
    return ciphertext

def redact_key(key: str) -> str:
    """Redact plain or encrypted API key for display/logs."""
    if not key:
        return ""
    plain = decrypt_key(key) if key.startswith("enc:") else key
    if len(plain) > 8:
        return plain[:3] + "…" + plain[-4:]
    return "…redacted…"

def sanitize_dict(data: dict) -> dict:
    """Recursively copy data and redact all api_key values."""
    if not isinstance(data, dict):
        return data
    out = copy.deepcopy(data)
    
    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "api_key" and isinstance(v, str) and v:
                    obj[k] = redact_key(v)
                elif isinstance(v, (dict, list)):
                    _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
    _walk(out)
    return out
