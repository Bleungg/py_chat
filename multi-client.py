import sys
import os
import re
import json
from socket import *
from prompt_toolkit import *
from prompt_toolkit.patch_stdout import patch_stdout
from threading import Thread
from datetime import datetime

class Client:
    def __init__(self, HOST, PORT):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((HOST,PORT))
        self.name = self.get_name()
        self.session = PromptSession()

        self.talk()

    def talk(self):
        self.socket.send(self.name.encode())
        Thread(target=self.receive_message, daemon=True).start()
        self.send_message()

    def send_message(self):
        usr_input: str
        
        while True:
            with patch_stdout():
                usr_input = self.session.prompt("You: ")

            if not usr_input.strip():
                continue

            time = f"[{datetime.now().strftime('%H:%M')}]"
            match = re.match(r"[/]", usr_input)

            if match:
                print(f"\033[AYou: {usr_input} {time}")
                self.command(usr_input)
            else:
                message = f"{self.name}: {usr_input} {time}"
                self.socket.send(message.encode())
                print(f"\033[AYou: {usr_input} {time}")

    def command(self, input: str):
        match = re.match(r"(/\w+)\s*(.*)", input)

        if not match:
            self.not_valid_command()
            return

        command = match.group(1)
        args = match.group(2) if match.group(2) != "" else None

        match command:
            case "/msg":
                if not args:
                    self.not_valid_command()
                else:
                    self.socket.send(input.encode())
            case "/name":
                self.change_name(args, input)
            case "/leave":
                if args:
                    self.not_valid_command()
                else:
                    self.leave(input)
            case "/help":
                if args:
                    self.not_valid_command()
                else:
                    self.help()
            case "/users":
                if args:
                    self.not_valid_command()
                else:
                    self.socket.send(input.encode())
            case "/history":
                self.socket.send(input.encode())
            case "/clear":
                if args:
                    self.not_valid_command()
                else:
                    os.system("clear")
            case _:
                self.not_valid_command()

    def not_valid_command(self):
        print_formatted_text(ANSI("\033[31mThis is not a valid command"))
    
    def receive_message(self):
        while True:
            message = self.socket.recv(1024).decode()
            match = re.match(r"(/users|/history) (.*)", message)

            if match and match.group(1) == "/users":
                self.users(match.group(2))
            elif match and match.group(1) == "/history":
                self.history(match.group(2))
            elif not message.strip():
                print_formatted_text(ANSI("\033[31mServer has now shutdown"))
                os.system("stty sane")
                self.socket.close()
                os._exit(0)
            else:
                print_formatted_text(ANSI(message))
                
    def get_name(self):
        valid = False
        
        while not valid:
            name = prompt("Enter your name: ")

            valid = self.valid_name(name)

        return name
    
    def valid_name(self, name):
        pattern = r"[a-zA-Z0-9_]+"

        if not name or not name.strip():
            print_formatted_text(ANSI("\033[31mName must not be empty"))
            return False
        elif name == "You":
            print_formatted_text(ANSI("\033[31mThis is not a permitted name"))
            return False
        elif not re.fullmatch(pattern, name):
            print_formatted_text(ANSI("\033[31mName must only contain letters, numbers, or underscore"))
            return False
        else:
            return True

    def leave(self, input):
        self.socket.send(input.encode())
        self.socket.close()
        print_formatted_text(ANSI("\033[31mYou have left"))
        os._exit(0)

    def help(self):
        print(
            "\033[34m/msg {username} {message}: Send a private message to a user\n"
            "\033[34m/name {new_name}: Change your name to new_name\n"
            "\033[34m/leave: Leave the chat\n"
            "\033[34m/users: Display a list of users\n"
            "\033[34m/history {lines}: Display a history of all chat messages, optionally up to lines amount. "
            "\033[34mIf lines is not specified then displays all history\n"
            "\033[34m /clear: Clears the chat of all messages and notifications"
        )

    def change_name(self, args, input):
        if self.valid_name(args):
            self.socket.send(input.encode())
            self.name = args.strip()

    def users(self, input: str):
        users = input.split("/")

        print_formatted_text(ANSI("\033[34mUSERS START: \n"))

        for user in users:
            print_formatted_text(ANSI(f"\033[34m{user}"))
        
        print_formatted_text(ANSI("\n \033[34mUSERS END \n"))

    def history(self, history_json):
        try:
            history = json.loads(history_json)
        except json.JSONDecodeError:
            print_formatted_text(ANSI("\033[31mError: Could not parse history"))
            return

        print_formatted_text(ANSI("\033[34mHISTORY START: \n"))

        for line in history:
            print_formatted_text(ANSI(f"\033[34m{line}"))

        print_formatted_text(ANSI("\n\033[34mHISTORY END \n"))


PORT = int(sys.argv[1])

if __name__ == "__main__":
    Client("localhost", PORT)