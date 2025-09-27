import os
import sys
import re
import json
import time
from socket import *
from prompt_toolkit.history import *
from threading import Thread
from datetime import datetime

class Server:
    def __init__(self, HOST, PORT):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((HOST, PORT))
        self.socket.listen(5)
        self.clients = []
        self.hist = InMemoryHistory()
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
            match = re.match(r"/exit\s*(\d*)", inp)

            if match and match.group(1) and match.group(1).strip().isdigit():
                self.shutdown(int(match.group(1)))
            elif match:
                self.shutdown(5)
            else:
                print("Not valid exit command")

    def shutdown(self, shut_time):
        curr_time = f" [{datetime.now().strftime('%H:%M')}]"
        print(f"Server shutdown in {shut_time} seconds")
        self.broadcast_all(f"\033[31mServer will be shutting down in {shut_time} seconds [{curr_time}]")
        time.sleep(shut_time)

        for client in self.clients[:]:
            client["socket"].close()
        
        self.clients.clear()
        self.socket.shutdown(SHUT_RDWR)
        self.socket.close()
        os._exit(0)

    def broadcast_all(self, message):
        disconnected = []
        for client in self.clients[:]:  
            sock: socket = client["socket"]
            try:
                sock.send(message.encode())
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            if client in self.clients:
                name = client["name"]
                time = f"[{datetime.now().strftime('%H:%M')}]"
                self.broadcast(client, f"\033[31m{name} has left the chat! [{time}]")
                self.clients.remove(client)
            
    def handle_new_client(self, client, addr):
        sock: socket = client["socket"]

        while True:
            name = client["name"]

            try:
                message = sock.recv(1024).decode()
                time = f"[{datetime.now().strftime('%H:%M')}]"
                match = re.match(r"(/leave|/users|/name|/history|/msg)\s*(.*)", message)

                if match:
                    self.command(match, client, addr, time)
                else:
                    self.hist.append_string(message)
                    self.broadcast(client, message)
            except Exception:
                if client in self.clients:
                    self.broadcast(client, f"\033[31m{name} has left the chat! [{time}]")
                    self.clients.remove(client)
                sock.close()
                break

    def command(self, match: re.Match, client, addr, time):
        command = match.group(1)

        match command:
            case "/leave":
                self.leave(client, addr, time)
            case "/users":
                self.users(client)
            case "/name":
                self.name(match.group(2), client, time)
            case "/history":
                self.history(client, match)
            case "/msg":
                self.msg(client, match.group(2), time)

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
                name = client["name"]
                time = f"[{datetime.now().strftime('%H:%M')}]"
                self.broadcast(client, f"\033[31m{name} has left the chat! [{time}]")
                self.clients.remove(client)

    def leave(self, client, addr, time):
        name = client["name"]
        sock: socket = client["socket"]

        self.broadcast(client, f"\033[31m{name} has left the chat! [{time}]")
        print("Disconnection from: " + str(addr))
        self.clients.remove(client)
        sock.close()

    def users(self, client):
        sock: socket = client["socket"]

        names = [c["name"] for c in self.clients]
        users = "/".join(names)
        sock.send(f"/users {users}".encode()) 

    def name(self, new_name, client, time):
        self.broadcast_all(f"\033[31m{client['name']} has changed their name to {new_name} [{time}]")
        client["name"] = new_name

    def history(self, client, match: re.Match):
        hist_list = self.hist.get_strings()
        sock: socket = client["socket"]

        m: str = match.group(2)
        if m:
            if not m.strip().isdigit():
                time = f"[{datetime.now().strftime('%H:%M')}]"
                sock.send(f"\033[31mNot a valid history command [{time}]")
                return

            maxStrings = int(match.group(2))
            start = max(0, len(hist_list) - maxStrings)
            hist_list = hist_list[start:]

        history = json.dumps(hist_list)
        sock: socket = client["socket"]
        sock.send(f"/history {history}".encode())

    def find_client_by_name(self, name):
        for client in self.clients:
            if client["name"] == name:
                return client
        return None
    
    def is_valid_recipient(self, sender, recipient):
        time = f"[{datetime.now().strftime('%H:%M')}]"
        sock: socket = sender["socket"]

        if sender["name"] == recipient:
            sock.send(f"\033[31mYou can't send private messages to yourself [{time}]".encode())
            return False
        
        exists = self.find_client_by_name(recipient)
        if not exists:
            sock.send(f"\033[31mUser '{recipient}' not found [{time}]".encode())
            return False
    
        return True

    def msg(self, sender, args: str, time):
        recipient_name = args.split()[0]
        message = " ".join(args.split()[1:])

        if not self.is_valid_recipient(sender, recipient_name):
            return
        
        recipient_sock: socket = self.find_client_by_name(recipient_name)["socket"]
        sock: socket = sender["socket"]
    
        try:
            formatted_msg = f"\033[33m[From {sender['name']}]: {message} [{time}]"
            recipient_sock.send(formatted_msg.encode())
      
            confirm = f"\033[33m[To {recipient_name}]: {message} [{time}]"
            sock.send(confirm.encode())
        except Exception:
            sock.send(f"\033[31mFailed to send message to {recipient_name} [{time}]".encode())

PORT = int(sys.argv[1])

if __name__ == "__main__":
    server = Server("localhost", PORT)
    server.listen()