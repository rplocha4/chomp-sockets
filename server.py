import pickle
import random
import socket
import threading


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.board_lengths = []
        self.lock = threading.Lock()
        self.pairs = []

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

    def start(self):
        print("Server started. Waiting for connections...")
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.start()

    def accept_connections(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Client connected: {address}")
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket, address)
            )
            client_thread.start()

    def send_message(self, data, client_socket):
        data = pickle.dumps(data)
        client_socket.send(data)

    def handle_client(self, client_socket, address):
        while True:
            try:
                data = client_socket.recv(1024)
                data = pickle.loads(data)
                if not data:
                    continue
                print(f"Received: {data['message']}")
                if data["message"] == "board_size":
                    width, height = data["data"]
                    self.clients.append({"addr": client_socket, "board": data["data"]})
                    for c in self.clients:
                        if (
                            c["addr"] != client_socket
                            and c["board"] == data["data"]
                            and self.not_in_pairs(c["addr"])
                        ):
                            board = self.generate_board_data(width, height)
                            self.pairs.append(
                                {
                                    "pair": (client_socket, c["addr"]),
                                    "board": board,
                                }
                            )
                            turn = random.choice([True, False])

                            self.send_message(
                                {"message": "Paired", "data": board, "turn": turn},
                                client_socket,
                            )
                            self.send_message(
                                {"message": "Paired", "data": board, "turn": not turn},
                                c["addr"],
                            )
                            break
                elif data["message"] == "play again":
                    width, height = data["data"]
                    for c in self.clients:
                        if (
                            c["addr"] != client_socket
                            and c["board"] == data["data"]
                            and self.not_in_pairs(c["addr"])
                        ):
                            board = self.generate_board_data(width, height)
                            self.pairs.append(
                                {
                                    "pair": (client_socket, c["addr"]),
                                    "board": board,
                                }
                            )
                            turn = random.choice([True, False])
                            self.send_message(
                                {"message": "Paired", "data": board, "turn": turn},
                                client_socket,
                            )
                            self.send_message(
                                {"message": "Paired", "data": board, "turn": not turn},
                                c["addr"],
                            )
                            break
                elif data["message"] == "move":
                    x, y = data["data"]
                    board = self.get_pair_board(client_socket)
                    board = self.update_board(board, x, y)
                    self.update_pair_board(board, client_socket)
                    self.send_message(
                        {"message": "board_data", "data": board, "turn": False},
                        client_socket,
                    )
                    self.send_message(
                        {"message": "board_data", "data": board, "turn": True},
                        self.get_user_pair(client_socket),
                    )
                    if x == 0 and y == 0:
                        self.send_message(
                            {"message": "You lost!", "data": board},
                            client_socket,
                        )
                        self.send_message(
                            {"message": "You won!", "data": board},
                            self.get_user_pair(client_socket),
                        )
                        self.remove_client(client_socket)
                        self.remove_client(self.get_user_pair(client_socket))
                        self.remove_pair(client_socket)
                elif data["message"] == "disconnect":
                    pair = self.get_user_pair(client_socket)
                    self.remove_client(client_socket)
                    self.send_message({"message": "disconnect"}, pair)
                    self.remove_pair(client_socket)
                    break

            except Exception as e:
                print(e)
                print("Disconnected from the server.")
                client_socket.close()
                return

    def get_user_pair(self, client_socket):
        for p in self.pairs:
            if p["pair"][0] == client_socket or p["pair"][1] == client_socket:
                return p["pair"][1] if p["pair"][0] == client_socket else p["pair"][0]

    def update_board(self, board, x, y):
        for i in range(x, len(board)):
            for j in range(y, len(board[i])):
                board[i][j] = 1
        return board

    def not_in_pairs(self, client_socket):
        for p in self.pairs:
            if p["pair"][0] == client_socket or p["pair"][1] == client_socket:
                return False
        return True

    def get_pair_board(self, pair):
        for p in self.pairs:
            if p["pair"][0] == pair or p["pair"][1] == pair:
                return p["board"]

    def update_pair_board(self, board, pair):
        for p in self.pairs:
            if p["pair"][0] == pair or p["pair"][1] == pair:
                p["board"] = board
                break

    def remove_pair(self, client_socket):
        with self.lock:
            for p in self.pairs:
                if p["pair"][0] == client_socket or p["pair"][1] == client_socket:
                    index = self.pairs.index(p)
                    del self.pairs[index]
                    break

    def remove_client(self, client_socket):
        with self.lock:
            for c in self.clients:
                if c["addr"] == client_socket:
                    index = self.clients.index(c)
                    del self.clients[index]
                    break

    def generate_board_data(self, width, height):
        return [[0 for _ in range(height)] for _ in range(width)]


server = Server("localhost", 8000)
server.start()
