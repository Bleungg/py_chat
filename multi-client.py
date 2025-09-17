import sys
import os
from socket import *
from threading import Thread

class Client:
    def __init__(self, HOST, PORT):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((HOST,PORT))
        self.name = input("Enter your name: ")

        self.talk()

    def talk(self):
        self.socket.send(self.name.encode())
        Thread(target=self.receive_message, daemon=True).start()
        self.send_message()

    def send_message(self):
        while True:
            usr_input = input("You: ")

            if usr_input.strip()[0] == "/":
                self.command(usr_input)
            else:
                message = self.name + ": " + usr_input
                self.socket.send(message.encode())

    def command(self, input):
        """
            /msg username message
            /msgOpen username
            /msgClose username
            /users
            /name newname
            timestamps
            /help
            emojis or text formatting
            connection limits
        """

        split = input.split('/')
        command = split[0]

        # if len(split) == 3:
            
        # elif len(split) == 2:
        #     if command == "msgOpen":

        #     elif command == "msgClose":

        #     elif command == "name":
        # else:
        #     if command == "leave":
        #         self.socket.send(input.encode())
        #         self.socket.close()
        #         sys.exit(0)
        #     elif command == "help":

        #     elif command == "users":

    def receive_message(self):
        while True:
            message = self.socket.recv(1024).decode()

            if not message.strip():
                print("Server has now shutdown")
                self.socket.close()
                os._exit(0)

            print(f"\r{message}")
            print("You: ", end="", flush=True)

PORT = int(sys.argv[1])

if __name__ == "__main__":
    Client("localhost", PORT)