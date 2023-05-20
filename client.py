import pickle
import socket
import threading

import pygame

HOST = "localhost"
PORT = 8000

pygame.init()


WIDTH, HEIGHT = 1200, 600
SCREEN_SIZE = (WIDTH, HEIGHT + 100)
window = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Client")
BOARD_SIZE = (5, 4)

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
                text = "You lost! Waiting for a player to join..."
            elif data["message"] == "You won!":
                turn = False
                text = "You won! Waiting for a player to join..."
            elif data["message"] == "disconnect":
                text = "Opponent disconnected. Waiting for a player to join..."
                print("Opponent disconnected.")
                turn = False
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
    if x < BOARD_SIZE[0] and y < BOARD_SIZE[1] and board[x][y] == 0:
        send_message({"message": "move", "data": (x, y)})


def draw_board():
    for i in range(len(board)):
        for j in range(len(board[i])):

            # draw brown square based on smaller dimension with gaps between squares
            if board[i][j] == 0:
                pygame.draw.rect(
                    window,
                    (139, 69, 19),
                    (
                        i * (WIDTH // BOARD_SIZE[0]) + 1,
                        j * (HEIGHT // BOARD_SIZE[1]) + 1,
                        WIDTH // BOARD_SIZE[0] - 2,
                        HEIGHT // BOARD_SIZE[1] - 2,
                    ),
                )

            if i == 0 and j == 0 and board[i][j] == 0:
                img = pygame.image.load("img2.png").convert_alpha()
                img.set_colorkey((255, 255, 255))
                img = pygame.transform.scale(
                    img, (WIDTH // BOARD_SIZE[0], HEIGHT // BOARD_SIZE[1])
                )
                rect = img.get_rect()

                rect.move(i * (WIDTH // BOARD_SIZE[0]), j * (HEIGHT // BOARD_SIZE[1]))
                window.blit(img, rect)

    # for i in range(0, BOARD_SIZE[0] + 1):
    #     pygame.draw.line(
    #         window,
    #         BLACK,
    #         (i * (WIDTH // BOARD_SIZE[0]), 0),
    #         (i * (WIDTH // BOARD_SIZE[0]), HEIGHT),
    #         2,
    #     )
    # for i in range(0, BOARD_SIZE[1] + 1):
    #     pygame.draw.line(
    #         window,
    #         BLACK,
    #         (0, i * (HEIGHT // BOARD_SIZE[1])),
    #         (WIDTH, i * (HEIGHT // BOARD_SIZE[1])),
    #         2,
    #     )


def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, 1, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)


receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

send_message({"message": "board_size", "data": BOARD_SIZE})
running = True
while running:
    window.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            send_message({"message": "disconnect"})
            server_socket.close()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not turn:
                continue
            pos = pygame.mouse.get_pos()
            x = pos[0] // (WIDTH // BOARD_SIZE[0])
            y = pos[1] // (HEIGHT // BOARD_SIZE[1])
            handle_click(x, y)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                send_message({"message": "disconnect"})
                server_socket.close()

    draw_board()
    draw_text(
        text,
        pygame.font.SysFont("Arial", 25, bold=True, italic=False),
        BLACK,
        window,
        20,
        SCREEN_SIZE[1] - (SCREEN_SIZE[1] - HEIGHT) // 2 - 25,
    ),
    pygame.display.update()
pygame.quit()
