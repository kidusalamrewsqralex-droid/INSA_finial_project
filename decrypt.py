
import os
from cryptography.fernet import Fernet

def decrypt_files_in(path, key):
    path = rf"{path}"
    path = os.path.abspath(path)
    decrypted_files = []
    fernet = Fernet(key)

    # Files to decrypt

    for file in os.listdir(path):
        
        if os.path.isfile(os.path.join(path, file)):
            try:
                # Read encrypted data
                with open(os.path.join(path, file), "rb") as thefile:
                    encrypted = thefile.read()

                # Decrypt
                decrypted = fernet.decrypt(encrypted)

                # Restore original contents
                with open(os.path.join(path, file), "wb") as thefile:
                    thefile.write(decrypted)

                decrypted_files.append(file)

            except Exception as e:
                return f"Skipped {file}: {e}"
    return f"Decrypted: {', '.join(decrypted_files)}"
