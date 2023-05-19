import pickle
import socket
import threading

HOST = "localhost"
PORT = 8000

clients = []
board_lengths = []
lock = threading.Lock()
pairs = []


def send_message(data, client_socket):
    data = pickle.dumps(data)
    client_socket.send(data)


def handle_client(client_socket, address):
    while True:
        try:
            data = client_socket.recv(1024)
            data = pickle.loads(data)
            print(data)
            if not data:
                return
            print(f"Received: {data['message']}")
            if data["message"] == "board_size":
                board_length = data["data"]
                clients.append({"addr": client_socket, "board": board_length})
                for c in clients:
                    if c["addr"] != client_socket:
                        board = generate_board_data(board_length)
                        pairs.append(
                            {
                                "pair": (client_socket, c["addr"]),
                                "board": board,
                            }
                        )
                        send_message(
                            {"message": "Paired", "data": board, "turn": True},
                            client_socket,
                        )
                        send_message(
                            {"message": "Paired", "data": board, "turn": False},
                            c["addr"],
                        )
                        break
            elif data["message"] == "move":
                x, y = data["data"]
                board = get_pair_board(client_socket)
                board = update_baord(board, x, y)
                update_pair_board(board, client_socket)
                send_message(
                    {"message": "board_data", "data": board, "turn": False},
                    client_socket,
                )
                send_message(
                    {"message": "board_data", "data": board, "turn": True},
                    get_user_pair(client_socket),
                )
                if x == 0 and y == 0:
                    send_message(
                        {"message": "You lost!", "data": board},
                        client_socket,
                    )
                    send_message(
                        {"message": "You won!", "data": board},
                        get_user_pair(client_socket),
                    )
                    remove_client(client_socket)
                    remove_client(get_user_pair(client_socket))
                    break

        except:
            print("Disconnected from the server.")
            client_socket.close()
            return


def get_user_pair(client_socket):
    for p in pairs:
        if p["pair"][0] == client_socket or p["pair"][1] == client_socket:
            return p["pair"][1] if p["pair"][0] == client_socket else p["pair"][0]


def update_baord(board, x, y):
    board[x][y] = 1
    # mark as well the right and below cell
    if x < len(board) - 1:
        board[x + 1][y] = 1
    if y < len(board[0]) - 1:
        board[x][y + 1] = 1
    return board


def get_pair_board(pair):
    for p in pairs:
        if p["pair"][0] == pair or p["pair"][1] == pair:
            return p["board"]


def update_pair_board(board, pair):
    for p in pairs:
        if p["pair"][0] == pair or p["pair"][1] == pair:
            p["board"] = board
            break


def remove_client(client_socket):
    with lock:
        if client_socket in clients:
            index = clients.index(client_socket)
            del clients[index]
            del board_lengths[index]


def generate_board_data(board_length):
    # Placeholder function to generate board data (replace with your own implementation)
    return [[0 for _ in range(board_length)] for _ in range(board_length)]


def accept_connections():
    while True:
        client_socket, address = server_socket.accept()
        print(f"Client connected: {address}")
        # Start a new thread to handle client communication
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, address)
        )
        client_thread.start()


# Set up server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print("Server started. Waiting for connections...")

# Start accepting client connections
accept_thread = threading.Thread(target=accept_connections)
accept_thread.start()
