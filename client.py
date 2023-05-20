import pickle
import socket
import threading

import pygame

HOST = "localhost"
PORT = 8000

pygame.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
WIDTH, HEIGHT = 1200, 600
SCREEN_SIZE = (WIDTH, HEIGHT + 100)


class InputBox:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY
        self.text = ""
        self.font = pygame.font.Font(None, 32)
        self.active = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = WHITE if self.active else GRAY
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode

    def update(self):
        width = max(200, self.rect.width + 10)
        self.rect.width = width

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 0)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_surface = self.font.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        label_surface = self.font.render(self.label, True, BLACK)
        screen.blit(label_surface, (self.rect.x - 150, self.rect.y + 5))


class GameClient:
    def __init__(self):
        self.board_size = (5, 4)
        self.board = []
        self.turn = False
        self.text = "Waiting for a player to join..."
        self.IN_GAME = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((HOST, PORT))

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

        self.run()

    def receive_messages(self):
        while True:
            try:
                data = self.server_socket.recv(1024)
                data = pickle.loads(data)
                if not data:
                    continue
                print(f"Received: {data['message']}")
                if data["message"] == "board_data":
                    self.board = data["data"]
                    self.turn = data["turn"]
                    self.text = "Your turn" if self.turn else "Opponent's turn"

                elif data["message"] == "Paired":
                    self.board = data["data"]
                    self.turn = data["turn"]
                    self.text = "Your turn" if self.turn else "Opponent's turn"
                elif data["message"] == "You lost!":
                    self.turn = False
                    self.text = "You lost! Waiting for a player to join..."
                    self.send_message(
                        {"message": "board_size", "data": self.board_size}
                    )

                elif data["message"] == "You won!":
                    self.turn = False
                    self.text = "You won! Waiting for a player to join..."
                    self.send_message(
                        {"message": "board_size", "data": self.board_size}
                    )

                elif data["message"] == "disconnect":
                    self.text = "Opponent disconnected. Waiting for a player to join..."
                    print("Opponent disconnected.")
                    self.turn = False
            except:
                print("Disconnected from the server.")
                self.server_socket.close()
                break

    def send_message(self, message):
        try:
            pickle.dumps(message)
            self.server_socket.send(pickle.dumps(message))
        except:
            print("Failed to send the message.")

    def handle_click(self, x, y):
        if x < self.board_size[0] and y < self.board_size[1] and self.board[x][y] == 0:
            self.send_message({"message": "move", "data": (x, y)})

    def draw_board(self, window):
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.board[i][j] == 0:
                    pygame.draw.rect(
                        window,
                        (139, 69, 19),
                        (
                            i * (WIDTH // self.board_size[0]) + 1,
                            j * (HEIGHT // self.board_size[1]) + 1,
                            WIDTH // self.board_size[0] - 2,
                            HEIGHT // self.board_size[1] - 2,
                        ),
                    )

                if i == 0 and j == 0 and self.board[i][j] == 0:
                    img = pygame.image.load("img2.png").convert_alpha()
                    img.set_colorkey((255, 255, 255))
                    img = pygame.transform.scale(
                        img, (WIDTH // self.board_size[0], HEIGHT // self.board_size[1])
                    )
                    rect = img.get_rect()

                    rect.move(
                        i * (WIDTH // self.board_size[0]),
                        j * (HEIGHT // self.board_size[1]),
                    )
                    window.blit(img, rect)

    def draw_text(self, text, font, color, surface, x, y):
        text_obj = font.render(text, 1, color)
        text_rect = text_obj.get_rect()
        text_rect.topleft = (x, y)
        surface.blit(text_obj, text_rect)

    def game_loop(self):
        window = pygame.display.set_mode(SCREEN_SIZE)
        running = True

        while running:
            window.fill(WHITE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.send_message({"message": "disconnect"})
                    self.server_socket.close()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.turn:
                        continue
                    pos = pygame.mouse.get_pos()
                    x = pos[0] // (WIDTH // self.board_size[0])
                    y = pos[1] // (HEIGHT // self.board_size[1])
                    self.handle_click(x, y)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        self.send_message({"message": "disconnect"})
                        self.server_socket.close()

            self.draw_board(window)
            self.draw_text(
                self.text,
                pygame.font.SysFont("Arial", 25, bold=True, italic=False),
                BLACK,
                window,
                20,
                SCREEN_SIZE[1] - (SCREEN_SIZE[1] - HEIGHT) // 2 - 25,
            )
            pygame.display.update()

        pygame.quit()

    def choice(self):
        screen = pygame.display.set_mode((400, 200))
        pygame.display.set_caption("Input Box Example")

        width_box = InputBox(200, 50, 140, 32, "Width:")
        height_box = InputBox(200, 100, 140, 32, "Height:")

        button_rect = pygame.Rect(210, 150, 80, 32)
        button_text = pygame.font.Font(None, 24).render("Submit", True, WHITE)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                width_box.handle_event(event)
                height_box.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(event.pos):
                        try:
                            width = int(width_box.text)
                            height = int(height_box.text)
                            print("Width:", width)
                            print("Height:", height)
                            self.board_size = (width, height)
                            self.send_message(
                                {"message": "board_size", "data": (width, height)}
                            )
                            self.IN_GAME = True
                            return
                        except ValueError:
                            print("Invalid input")

            screen.fill(WHITE)
            width_box.draw(screen)
            height_box.draw(screen)
            pygame.draw.rect(screen, BLACK, button_rect)
            screen.blit(button_text, button_rect.move(10, 0))

            pygame.display.flip()

    def run(self):
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

        while True:
            if self.IN_GAME:
                self.game_loop()
            self.choice()


game = GameClient()
game.run()
