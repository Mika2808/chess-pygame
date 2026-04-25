import pygame

class Game:
    def __init__(self, engine):
        self.engine = engine  # your chess logic

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
        
        # loading pieces
        self.pieces = self.load_pieces()

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

    def run(self):
        while self.running:

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

        if self.selected_square is None:
            piece = self.engine.board[row][col]

            if piece is not None:
                self.selected_square = (row, col)
        else: 
            start = self.selected_square
            end = (row,col)

            self.engine.move_piece(start, end)

            self.selected_square = None