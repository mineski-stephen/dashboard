import os
import sys
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

def load_key():
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    key_b64 = config.get("debugKey", "")
    if not key_b64:
        print("ERROR: No debugKey found in config.json")
        sys.exit(1)
    try:
        key = base64.b64decode(key_b64).decode("utf-8")
    except Exception:
        key = key_b64  # Fallback to raw value if not valid Base64
    return key

def derive_key(password, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(password.encode("utf-8"))

def encrypt_file(csv_path):
    with open(csv_path, "r", encoding="utf-8") as f:
        plaintext = f.read()

    password = load_key()
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

    # Format: [16 salt][12 iv][ciphertext]
    output = salt + iv + ciphertext

    out_path = os.path.splitext(csv_path)[0] + ".enc"
    with open(out_path, "wb") as f:
        f.write(output)

    print(f"Encrypted: {os.path.basename(csv_path)} -> {os.path.basename(out_path)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python encrypt.py <file.csv> [file2.csv ...]")
        sys.exit(1)

    for path in sys.argv[1:]:
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            continue
        encrypt_file(path)
