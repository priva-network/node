import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import urlsafe_b64encode, urlsafe_b64decode

def encrypt_private_key(private_key, passphrase) -> dict:
    # Generate a random salt
    salt = os.urandom(16)

    # Derive the encryption key from the passphrase
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(passphrase.encode())

    # Encrypt the private key using AES
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_private_key = encryptor.update(private_key.encode()) + encryptor.finalize()

    # Prepare data for JSON output
    data_to_save = {
        "encrypted_private_key": urlsafe_b64encode(encrypted_private_key).decode(),
        "salt": urlsafe_b64encode(salt).decode(),
        "iv": urlsafe_b64encode(iv).decode(),
    }

    return data_to_save

def decrypt_private_key(data, passphrase) -> str:
    encrypted_private_key = urlsafe_b64decode(data["encrypted_private_key"])
    salt = urlsafe_b64decode(data["salt"])
    iv = urlsafe_b64decode(data["iv"])

    # Derive the decryption key from the passphrase
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(passphrase.encode())

    # Decrypt the private key
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_private_key = decryptor.update(encrypted_private_key) + decryptor.finalize()

    return decrypted_private_key.decode()
