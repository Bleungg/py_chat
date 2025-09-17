import os
import sys
from socket import *
from threading import Thread
import time

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

            self.broadcast(client, name + " has joined the chat!")
            client_socket.send(f"Welcome, {name}!".encode())

            self.clients.append(client)
            Thread(target=self.handle_new_client, args=(client, addr), daemon=True).start()

    def server_close(self):
        while True:
            if input("") == "/exit":
                print("Server shutdown in 10 seconds")
                self.broadcast_all("Server will be shutting down in 10 seconds")
                time.sleep(10)

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
        socket = client["socket"]

        while True:
            try:
                message = socket.recv(1024).decode()
                if message.strip() == "/leave":
                    self.broadcast(client, name + " has left the chat!")
                    print("Disconnection from: " + str(addr))
                    self.clients.remove(client)
                    socket.close()
                    break
                else:
                    self.broadcast(client, message)
            except Exception:
                self.broadcast(client, name + " has left the chat!")
                if client in self.clients:
                    self.clients.remove(client)
                socket.close()
                break

    def broadcast(self, sender, message):
        disconnected = []
        for client in self.clients[:]:  
            if client["name"] != sender["name"]:
                try:
                    client["socket"].send(message.encode())
                except Exception:
                    disconnected.append(client)

        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)

PORT = int(sys.argv[1])

if __name__ == "__main__":
    server = Server("0.0.0.0", PORT)
    server.listen()