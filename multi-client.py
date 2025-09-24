import sys
import os
from prompt_toolkit import *
from prompt_toolkit.history import *
from prompt_toolkit.patch_stdout import patch_stdout
from socket import *
from threading import Thread
from datetime import datetime

class Client:
    def __init__(self, HOST, PORT):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((HOST,PORT))
        self.name = self.get_name()
        self.hist = InMemoryHistory()
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

            if usr_input.strip()[0] == "/":
                print(f"\033[AYou: {usr_input} {time}")
                self.command(usr_input)
            else:
                message = f"{self.name}: {usr_input} {time}"
                self.hist.append_string(message)
                self.socket.send(message.encode())
                print(f"\033[AYou: {usr_input} {time}")

    def command(self, input: str):
        """
            /msg username message
            /msgOpen username
            /msgClose username
            /name newname
            /help
        """

        split = input.split()
        command = split[0]

        match command:
            case "/msg":
                self.msg(input)
            case "/msgOpen":
                self.msgOpen(input)
            case "/msgClose":
                self.msgClose(input)
            case "/name":
                self.change_name(input)
            case "/leave":
                self.socket.send(input.encode())
                self.socket.close()
                print_formatted_text(ANSI("\033[31mYou have left"))
                os._exit(0)
            case "/help":
                self.help(input)
            case "/users":
                self.socket.send(input.encode())
            case "/history":
                self.history()
            case "/clear":
                os.system("clear")
            case _:
                print_formatted_text(ANSI("\033[31mThis is not a valid command"))

    def receive_message(self):
        while True:
            message = self.socket.recv(1024).decode()

            if message.split("///")[0] == "/users":
                self.users(message)
                continue
            elif not message.strip():
                print_formatted_text(ANSI("\033[31mServer has now shutdown"))
                self.socket.close()
                os._exit(0)
            
            print_formatted_text(ANSI(message))
                
    def get_name(self):
        name = ""
        
        while not name.strip():
            name = prompt("Enter your name: ")

            if name == "You":
                print_formatted_text(ANSI("\033[31mThis is not a valid name"))
                name = ""

        return name

    # def change_name(self, input):
    

    # def msg(self, input):
    # def msgOpen(self, input):
    # def msgClose(self, input):
    # def help(self, input):


    def users(self, input: str):
        users = input.split("///")[1:]

        print_formatted_text(ANSI("\033[34mUSERS START: \n"))

        for user in users:
            print_formatted_text(ANSI(f"\033[34m{user}"))
        
        print_formatted_text(ANSI("\n \033[34mUSERS END \n"))

    def history(self):
        history = self.hist.get_strings()

        print_formatted_text(ANSI("\033[34mHISTORY START: \n"))

        for line in history:
            print_formatted_text(ANSI(f"\033[34m{line}"))

        print_formatted_text(ANSI("\n \033[34mHISTORY END \n"))


PORT = int(sys.argv[1])

if __name__ == "__main__":
    Client("localhost", PORT)