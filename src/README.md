# py_chat

A simple terminal chat application (server + client) using Python sockets.  
Features multi-client broadcast, server-side history, private messaging, basic commands, and prompt-toolkit based client UI.

## Contents
- `src/multi-server.py` — server executable
- `src/multi-client.py` — client executable

## Install dependencies:
`pip3 install -r requirements.txt`

## Starting Server

Start the server (pick a port):
```sh
python3 src/multi-server.py 12345
```

Start a client (connect to same port):
```sh
python3 src/multi-client.py 12345
```

The client will prompt for a username on start, then a user can start messaging and using commands

## Commands (client)
- `/help` — show available commands
- `/leave` — leave the chat (client disconnects)
- `/users` — request current user list 
- `/name new_name` — request a name change
- `/history` — request full server history
- `/history N` — request last N lines from server history
- `/msg username message` — send one private message to `username`

## Server exit command
- `/exit {secs}` Schedules shutdown in `{secs}` seconds (default 5)

## Notes:
- Server shutdown sends server message to all users
- If users are still in server when it shuts down, closes all sockets of users.
- Since prompt-toolkit is used, "stty sane" is used on server shutdown if client is still in server to clean up the terminal
- ANSI colour formatting is used. Red messages are from the server, blue are from commands, and yellow are private messages
- Private messaging will send the message to the recipient, and a confirmation message to the sender
- The server stores all user message history. Clients request history using `/history` and the server returns a JSON array of history lines. 
Use `/history N` to request the most recent N lines.
