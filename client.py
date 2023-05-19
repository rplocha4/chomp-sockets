import pickle
import socket
import threading

import pygame

HOST = "localhost"
PORT = 8000

# Initialize Pygame
pygame.init()

# Set up the Pygame window
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Client")
BOARD_SIZE = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
board = []
turn = False
text = "Waiting for a player to join..."

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.connect((HOST, PORT))


def receive_messages():
    global board
    global turn
    global text
    while True:
        try:
            data = server_socket.recv(1024)
            data = pickle.loads(data)
            if not data:
                continue
            print(f"Received: {data['message']}")
            if data["message"] == "board_data":
                board = data["data"]
                turn = data["turn"]
                text = "Your turn" if turn else "Opponent's turn"

            elif data["message"] == "Paired":
                board = data["data"]
                turn = data["turn"]
                text = "Your turn" if turn else "Opponent's turn"
            elif data["message"] == "You lost!":
                turn = False
                text = "You lost!"
                # server_socket.close()
                break
            elif data["message"] == "You won!":
                turn = False
                text = "You won!"
                # server_socket.close()
                break

        except:
            print("Disconnected from the server.")
            server_socket.close()
            break


def send_message(message):
    try:
        pickle.dumps(message)
        server_socket.send(pickle.dumps(message))
    except:
        print("Failed to send the message.")


def handle_click(x, y):
    if x < BOARD_SIZE and y < BOARD_SIZE and board[x][y] == 0:
        # board[x][y] = 1
        # # mark as well the right and below cell
        # if x < BOARD_SIZE - 1:
        #     board[x + 1][y] = 1
        # if y < BOARD_SIZE - 1:
        #     board[x][y + 1] = 1
        print(x, y)
        send_message({"message": "move", "data": (x, y), "turn": not turn})


def draw_board():

    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] == 0:
                # draw a white filled rectangle
                pygame.draw.rect(window, WHITE, (i * 50, j * 50, 50, 50))
            elif board[i][j] == 1:
                pygame.draw.rect(window, (100, 100, 100), (i * 50, j * 50, 50, 50))

            # draw a gap between the tiles
            pygame.draw.line(window, BLACK, (i * 50, 0), (i * 50, 500))
            pygame.draw.line(window, BLACK, (0, j * 50), (500, j * 50))


def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, 1, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)


# Start a new thread to receive messages from the server
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

send_message({"message": "board_size", "data": 10})
# Game loop
running = True
while running:
    window.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # if mouse is clicked get position of board
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not turn:
                continue
            pos = pygame.mouse.get_pos()
            column = pos[0] // 50
            row = pos[1] // 50
            # check if the tile is in bounds
            handle_click(column, row)

    # Update the game display
    draw_board()

    draw_text(
        text,
        pygame.font.SysFont("Arial", 30),
        BLACK,
        window,
        100,
        500,
    )

    pygame.display.update()
pygame.quit()
