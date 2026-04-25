import random
import time

class AgentAI:
    def __init__(self, board, color):
        self.board = board
        self.color = color

    def make_move(self):
        moves = self.board.get_all_legal_moves(self.color)

        if not moves:
            return

        move = random.choice(moves)
        # optional "thinking time"
        time.sleep(0.5)
        self.board.move_piece(move[0], move[1])