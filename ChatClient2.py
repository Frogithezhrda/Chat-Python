import socket
import ChatBase
import sys
import threading
import time

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 1112

username = ""
running = True

def receive_messages(conn):
    global running
    while running:
        cmd, data = recv_message_and_parse(conn)
        if cmd == ChatBase.PROTOCOL_SERVER["received"]:
            _, sender, received_data = data.split("#")
            if received_data.upper() == "QUIT":
                print(f"[SERVER] {sender} Has Disconnected.")
                if username == sender:
                    running = False
            else:
                print(f"[{sender.upper()}] {received_data}")


# HELPER SOCKET METHOD

def get_big(conn):
    global running
    cmd, data = build_send_recv_parse(conn, ChatBase.PROTOCOL_CLIENT["select_chat"], "big")
    if cmd != ChatBase.PROTOCOL_SERVER["login_failed_msg"]:
        receive_thread = threading.Thread(target=receive_messages, args=(conn,))
        receive_thread.start()
        print("Enter Messages in the big chat")
        while True:
            message = input()
            build_and_send_message(conn, ChatBase.PROTOCOL_CLIENT["send_message"], message)
            time.sleep(1)  # Sleep briefly to allow messages to appear while typing
            if message.upper() == "QUIT":
                running = False
                receive_thread.join()
                break
        running = True
    else:
        print(data)

def get_chat(conn):
    global running
    print("1 - Chat 1\n2 - Chat 2\n3 - Chat 3")
    chat = input("Choose Chat 1-3: ")
    if not chat.isdigit():
        print("Not Valid Choice!")
    if 4 > int(chat) > 0:
        cmd, data = build_send_recv_parse(conn, ChatBase.PROTOCOL_CLIENT["select_chat"], chat)
        if cmd != ChatBase.PROTOCOL_SERVER["login_failed_msg"]:
            receive_thread = threading.Thread(target=receive_messages, args=(conn,))
            receive_thread.start()
            print("Enter Messages in chat %s!" % chat)
            while True:
                message = input()
                build_and_send_message(conn, ChatBase.PROTOCOL_CLIENT["send_message"], message)
                time.sleep(1)  # Sleep briefly to allow messages to appear while typing
                if message.upper() == "QUIT":
                    running = False
                    receive_thread.join()
                    break
        running = True
    else:
        print("No Chat Exists!")


def build_and_send_message(conn, code, data="NONE"):
    """
	Builds a new message using chatlib, wanted code and message.
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), data (str)
	Returns: Nothing
	"""
    try:
        # Build the message using chatlib's build_message function
        message = ChatBase.build_message(code, data)
        # Send the message to the server through the socket
        conn.sendall(message.encode())

        # Print debug information

    except Exception as exception:
        error_and_exit(exception)


def recv_message_and_parse(conn):
    """
	Recieves a new message from given socket,
	then parses the message using chatlib.
	Paramaters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message.
	If error occured, will return None, None
	"""
    # Implement Code
    # ..
    try:

        full_msg = conn.recv(1024).decode()

        # Parse the received message using chatlib
        cmd, data = ChatBase.parse_message(full_msg)

        # Return the command and data extracted from the message
        return cmd, data
    except Exception as exception:
        print(exception)
        return None, None


def connect():
    # Implement Code
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (SERVER_IP, SERVER_PORT)
    sock.connect(server_address)
    return sock


def error_and_exit(error_msg):
    print("Error:" + str(error_msg))
    sys.exit(1)


def build_send_recv_parse(conn, cmd, data="NONE"):
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)


def login(conn):
    global username
    username = input("Please enter username: \n")
    # Implement code
    try:
        build_and_send_message(conn, ChatBase.PROTOCOL_CLIENT["login_msg"], username)
    except Exception as exception:
        error_and_exit(exception)


def logout(conn):
    # Implement code
    build_and_send_message(conn, ChatBase.PROTOCOL_CLIENT["logout_msg"])
    conn.close()


def get_logged_users(conn):
    cmd, data = build_send_recv_parse(conn, ChatBase.PROTOCOL_CLIENT["logged"])
    print(data)


def choices(connection):
    while True:
        print("c\tEnter chat\nb\tBig channel\nl\tGet logged users\nq\tQuit")
        choice = input("Please enter your choice: ")
        if choice == 'q':
            print("Goodbye!")
            logout(connection)
            break
        elif choice == 'l':
            get_logged_users(connection)
        elif choice == 'c':
            get_chat(connection)
        elif choice == 'b':
            get_big(connection)
        else:
            print("Not Valid Command!")


def main():
    connection = connect()
    login(connection)
    try:
        while True:
            cmd, data = recv_message_and_parse(connection)
            if "ERROR" in cmd:
                print("Error:", data)
                login(connection)
            elif "LOGIN_OK" in cmd:
                print("Logged in!")
                choices(connection)
                break
    except Exception as e:
        error_and_exit(e)


if __name__ == '__main__':
    main()

