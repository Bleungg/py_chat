import os
import sys
from socket import *
from threading import Thread
import time
from datetime import datetime

class Server:
    def __init__(self, HOST, PORT):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.clients = []
        self.socket.listen(5)
        Thread(target=self.server_close, daemon=True).start()
        print("Server waiting for connection")

    def listen(self):
        while True:
            client_socket, addr = self.socket.accept()
            print("Connection from: " + str(addr))

            name = client_socket.recv(1024).decode()
            client = {"name": name, "socket": client_socket}

            time = f"[{datetime.now().strftime('%H:%M')}]"
            self.broadcast(client, f"\033[31m{name} has joined the chat! [{time}]")
            client_socket.send(f"Welcome, {name}! [{time}]".encode())

            self.clients.append(client)
            Thread(target=self.handle_new_client, args=(client, addr), daemon=True).start()

    def server_close(self):
        while True:
            inp = input("")
            split = inp.split()

            if len(split) == 2 and split[0] == "/exit":
                self.shutdown(int(split[1]))
            elif input("") == "/exit":
                self.shutdown(5)

    def shutdown(self, shut_time):
        curr_time = f" [{datetime.now().strftime('%H:%M')}]"
        print(f"Server shutdown in {shut_time} seconds")
        self.broadcast_all(f"\033[31mServer will be shutting down in {shut_time} seconds [{curr_time}]")
        time.sleep(shut_time)

        for client in self.clients[:]:
            client["socket"].close()
            self.clients.remove(client)

        self.socket.shutdown(SHUT_RDWR)
        self.socket.close()
        os._exit(0)

    def broadcast_all(self, message):
        disconnected = []
        for client in self.clients[:]:  
            try:
                client["socket"].send(message.encode())
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)
            
    def handle_new_client(self, client, addr):
        name = client["name"]
        sock: socket = client["socket"]

        while True:
            try:
                message = sock.recv(1024).decode()
                time = f"[{datetime.now().strftime('%H:%M')}]"
                if message.strip() == "/leave":
                    self.broadcast(client, f"\033[31m{name} has left the chat! [{time}]")
                    print("Disconnection from: " + str(addr))
                    self.clients.remove(client)
                    sock.close()
                    break
                elif message.strip() == "/users":
                    names = [c["name"] for c in self.clients]
                    users = "///".join(names)
                    sock.send(f"/users///{users}".encode()) 
                else:
                    self.broadcast(client, message)
            except Exception:
                self.broadcast(client, f"\033[31m{name} has left the chat! [{time}]")
                if client in self.clients:
                    self.clients.remove(client)
                sock.close()
                break

    def broadcast(self, sender, message):
        disconnected = []
        for client in self.clients[:]:  
            if client["name"] != sender["name"]:
                try:
                    sock : socket = client["socket"]
                    sock.send(message.encode())
                except Exception:
                    disconnected.append(client)

        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)

PORT = int(sys.argv[1])

if __name__ == "__main__":
    server = Server("localhost", PORT)
    server.listen()