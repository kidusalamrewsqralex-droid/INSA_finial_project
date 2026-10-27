import socket
import threading
import json


SERVER_HOST = '0.0.0.0'
PORT = 1234
ADDR = (SERVER_HOST, PORT)

shutdown_flag = threading.Event()
clients = []
def shutdown_server():
    
    while not shutdown_flag.is_set():
        if len(clients) == 0:
                print("**No clients connected.**")
        cmd = input("$>> ")
        try:
            type, msg = cmd.split("|",1)
        except Exception as e:
            print(f"Invalid command format. Use 'type|message'. Error: {e}")
            continue
        message = json.dumps({"Sender": f"{SERVER_HOST}:{PORT}", "type": type, "content": msg})
        try:
            if type.lower() == 'shutdown':
                for client in clients:
                    client.send(f"exit|".encode()) 
                shutdown_flag.set()              
                print("Shutdown signal received.")
            else:
                # Broadcast message to all connected clients
                for client in clients:
                    try:
                        client.send(f"{message}".encode())
                    except:
                        pass
        except Exception as e:
            print(f"Error occured during message handling: {e}")
            continue

def handle_client(client_socket, addr):
    with client_socket:
        print(f"Connected to {addr}")
        while not shutdown_flag.is_set():
            try:
                response = client_socket.recv(4096).decode()
                with open(f"response_from_{addr[0]}_{addr[1]}.txt", "a") as f:
                    f.write(response + "\n")
                if not response:
                    break
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    print(f"Received non-JSON response from {addr}: {response}")
                    continue
                for key, value in response.items():
                    print(f"Response from {addr}: \n {key}: {value}")   
            
            except Exception as e:
                print(f"Error occurred while handling response from {addr}: {e}")
                continue    
            except ConnectionResetError:
                break
    clients.remove(client_socket)
    print(f"Connection closed for {addr}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(ADDR)
        server_socket.listen()
        print(f"Server listening on {SERVER_HOST}:{PORT}")

        threading.Thread(target=shutdown_server, daemon=True).start()

        while not shutdown_flag.is_set():
            try:
                server_socket.settimeout(1)
                client_socket, addr = server_socket.accept()
                clients.append(client_socket)
                threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
            except socket.timeout:
                continue

if __name__ == "__main__":
    main()
