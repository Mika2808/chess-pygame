import pygame
from src.game.agent import AgentAI

class Game:
    def __init__(self, engine):
        self.engine = engine  # your chess logic
        self.ai = AgentAI(engine, "b", 3)

        pygame.init()

        self.WIDTH = 640
        self.HEIGHT = 640
        self.ROWS = 8
        self.COLS = 8
        self.SQUARE_SIZE = self.WIDTH // self.COLS

        # colors
        self.WHITE = (240, 217, 181)
        self.BROWN = (181, 136, 99)

        # window
        self.win = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chess")
        self.running = True
        self.ai_moved = False
        # loading pieces
        self.pieces = self.load_pieces()
        
        # for highlisghitng moves
        self.legal_moves = []
        
        self.highlight_surface = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
        self.highlight_surface.fill((0, 255, 0, 100))  # RGBA (last = transparency)
        
        # selecting squre
        self.selected_square = None

    def draw_board(self):
        self.win.fill(self.WHITE)

        for row in range(self.ROWS):
            for col in range(self.COLS):
                if (row + col) % 2 == 1:
                    pygame.draw.rect(
                        self.win,
                        self.BROWN,
                        (col * self.SQUARE_SIZE,
                         row * self.SQUARE_SIZE,
                         self.SQUARE_SIZE,
                         self.SQUARE_SIZE)
                    )

                if self.selected_square == (row, col):
                                pygame.draw.rect(
                                    self.win,
                                    (255, 255, 0),
                                    (col * self.SQUARE_SIZE,
                                    row * self.SQUARE_SIZE,
                                    self.SQUARE_SIZE,
                                    self.SQUARE_SIZE),
                                    3
                                )

                if (row, col) in self.legal_moves:
                    self.win.blit(
                        self.highlight_surface,
                        (col * self.SQUARE_SIZE, row * self.SQUARE_SIZE)
                    )

    def run(self):
        while self.running:
            # AI turn
            if self.engine.turn == "b" and not self.ai_moved:
                self.ai.make_move()
                self.ai_moved = True

            # Player turn → reset flag
            if self.engine.turn == "w":
                self.ai_moved = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())

            self.draw_board()
            self.draw_pieces()

            pygame.display.update()

        pygame.quit()

    def load_pieces(self):
        pieces = {}

        base_path = "assets/pieces/"

        names = [
            "wp", "wn", "wb", "wr", "wq", "wk",
            "bp", "bn", "bb", "br", "bq", "bk"
        ]

        for name in names:
            img = pygame.image.load(base_path + name + ".png")
            img = pygame.transform.scale(img, (self.SQUARE_SIZE, self.SQUARE_SIZE))
            pieces[name] = img

        return pieces
    
    def draw_pieces(self):
        board = self.engine.board

        for row in range(8):
            for col in range(8):
                piece = board[row][col]

                if piece is not None:
                    self.win.blit(
                        self.pieces[piece],
                        (col * self.SQUARE_SIZE, row * self.SQUARE_SIZE)
                    )

    def get_square_from_mouse(self, pos):
        x, y = pos
        row = y // self.SQUARE_SIZE
        col = x // self.SQUARE_SIZE
        return (row, col)
    
    def handle_click(self, pos):
        row, col = self.get_square_from_mouse(pos)
        clicked_square = (row, col)

        piece = self.engine.board[row][col]

        # CASE 1: nothing selected
        if self.selected_square is None:
            if piece is not None and piece[0] == self.engine.turn:
                self.selected_square = clicked_square
                self.legal_moves = self.engine.get_legal_moves(clicked_square)
            return

        # CASE 2: click same square → deselect
        if clicked_square == self.selected_square:
            self.selected_square = None
            self.legal_moves = []
            return

        # CASE 3: click own piece → switch selection
        if piece is not None and piece[0] == self.engine.turn:
            self.selected_square = clicked_square
            self.legal_moves = self.engine.get_legal_moves(clicked_square)
            return

        # CASE 4: attempt move (ONLY if legal)
        if clicked_square in self.legal_moves:
            self.engine.move_piece(self.selected_square, clicked_square)

        # CASE 5: reset selection after attempt
        self.selected_square = None
        self.legal_moves = []