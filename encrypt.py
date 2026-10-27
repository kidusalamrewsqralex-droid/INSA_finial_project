import os
from cryptography.fernet import Fernet

def generate_key():
    key = Fernet.generate_key()
    return key

def encrypt_files_in(path):
    path = rf"{path}"
    path = os.path.abspath(path)
    key = generate_key()
    files = []
    encrypted_files=[]
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            files.append(os.path.join(path, file))
    for file in files:
        with open(file, "rb") as thefile:
            contents = thefile.read()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(contents)
        with open(file, "wb") as thefile:
            thefile.write(encrypted)
        encrypted_files.append(file)
    return f"Encrypted: {', '.join(encrypted_files)}, Key: {key}"

