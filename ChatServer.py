import socket
import ChatBase
import select

ERROR_MSG = "Error! "
SERVER_PORT = 1112
SERVER_IP = "127.0.0.1"
users = {}
chats = {
    1: {},
    2: {},
    3: {},
    "big": {}
}


def broadcast_message(chat, sender_conn, message):
    if chat != "big":
        chat = int(chat)  # Convert chat to integer for consistency
    is_quit = False
    for client_conn in chats[chat].keys():
        if message.upper() == "QUIT":
            quit_conn = sender_conn
            is_quit = True
            build_and_send_message(client_conn, ChatBase.PROTOCOL_SERVER["received"],
                                   f"{chat}#{chats[chat][sender_conn]}#{message}")
        else:
            build_and_send_message(client_conn, ChatBase.PROTOCOL_SERVER["received"],
                                   f"{chat}#{chats[chat][sender_conn]}#{message}")
    if is_quit is True:
        chats[chat].pop(quit_conn)
        is_quit = False


def handle_chat(conn, chat):
    global users
    if chat != "big":
        chat = int(chat)  # Convert chat to integer for consistency
    if chat in [1, 2, 3]:
        if len(chats[chat]) < 2:  # Corrected from users[chat] to chats[chat]
            build_and_send_message(conn, ChatBase.PROTOCOL_SERVER["chat_ok"])
            chats[chat][conn] = users[conn.getpeername()]  # Assuming users[conn.getpeername()] contains username
        else:
            send_error(conn, "Chat is full")
    elif chat == "big":
        if len(chats[chat]) < 5:  # Corrected from users[chat] to chats[chat]
            build_and_send_message(conn, ChatBase.PROTOCOL_SERVER["chat_ok"])
            chats[chat][conn] = users[conn.getpeername()]  # Assuming users[conn.getpeername()] contains username
    else:
        send_error(conn, "Invalid chat selection")


def handle_logout_message(conn):
    global users
    global chats
    for chat in range(1, 3):
        if conn in chats[chat].keys():
            chats[chat].pop(conn)
    users.pop(conn.getpeername())
    print("Connection closed")
    conn.close()


def handle_logged(conn):
    global users
    build_and_send_message(conn, ChatBase.PROTOCOL_SERVER["logged_answer"], '\n'.join(users.values()))


def handle_login_message(conn, username):
    """
	Gets socket and message data of login message. Checks  user and pass exists and match.
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
	Recieves: socket, message code and data
	Returns: None (sends answer to client)
	"""
    global users

    if 2 < len(username) < 12:
        if username is not None:
            if username not in users.values():
                build_and_send_message(conn, ChatBase.PROTOCOL_SERVER["login_ok_msg"])
                users[conn.getpeername()] = username
            else:
                send_error(conn, "Name Already Connected!")
        else:
            send_error(conn, "User Got To Be Not Null!")
    else:
        send_error(conn, "User Length Not Valid!")


def send_error(conn, error_msg):
    """"""
    build_and_send_message(conn, ChatBase.PROTOCOL_SERVER["login_failed_msg"], ERROR_MSG + error_msg)


def build_and_send_message(conn, code, data="NONE"):
    """
	Builds a new message using chatlib, wanted code and message.
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), data (str)
	Returns: Nothing
	"""
    try:
        message = ChatBase.build_message(code, data)
        print("[SERVER] ", conn.getpeername(), message)
        conn.sendall(message.encode())

        # Print debug information

    except Exception as exception:
        print(exception)


def recv_message_and_parse(conn):
    """
	Recieves a new message from given socket,
	then parses the message using chatlib.
	Paramaters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message.
	If error occured, will return None, None
	"""
    try:
        full_msg = conn.recv(1024).decode()
        print("[CLIENT] ", conn.getpeername(), full_msg)
        cmd, data = ChatBase.parse_message(full_msg)
        return cmd, data
    except Exception as exception:
        return None, None


def setup_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (SERVER_IP, SERVER_PORT)
    sock.bind(server_address)
    sock.listen(1)
    return sock


def main():
    global chats
    global users
    connection = setup_socket()

    try:
        client_sockets_list = []

        while True:
            ready_to_read, ready_to_write, in_error = select.select([connection] + client_sockets_list,
                                                                    client_sockets_list, [])
            for current_socket in ready_to_read:
                if current_socket is connection:
                    (client_socket, client_address) = connection.accept()
                    print("\nNew Client joined!", client_address)
                    client_sockets_list.append(client_socket)
                else:
                    cmd, data = recv_message_and_parse(current_socket)
                    if cmd == ChatBase.PROTOCOL_CLIENT["logout_msg"]:
                        handle_logout_message(current_socket)
                        client_sockets_list.remove(current_socket)
                    elif cmd == ChatBase.PROTOCOL_CLIENT["login_msg"]:
                        handle_login_message(current_socket, data)
                    elif cmd == ChatBase.PROTOCOL_CLIENT["logged"]:
                        handle_logged(current_socket)
                    elif cmd == ChatBase.PROTOCOL_CLIENT["select_chat"]:
                        handle_chat(current_socket, data)
                    elif cmd == ChatBase.PROTOCOL_CLIENT["send_message"]:
                        for chat in chats.keys():
                            if current_socket in chats[chat].keys():
                                broadcast_message(chat, current_socket, data)
                    elif cmd:
                        # handle_client_message(current_socket, cmd, data)
                        send_error(current_socket, "Not A Valid Command")
                    else:
                        handle_logout_message(current_socket)
                        client_sockets_list.remove(current_socket)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting gracefully...")
    except ConnectionResetError:
        print("Connection reset by client.")
    except Exception as e:
        print("Error:", e)
    finally:
        if current_socket:
            client_sockets_list.remove(current_socket)


main()
