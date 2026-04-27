import random
import time
import math

class AgentAI:
    def __init__(self, board, color, depth):
        self.board = board
        self.color = color
        self.depth = depth

    def make_move(self):
        ## WORKS ON BLACK. I MEAN AI IS BLACK
        ## changes marked OB to change for white (OW)

        best_move = None
        best_score = math.inf ## OB
        #best_score = -math.inf ## OW

        moves = self.board.get_all_legal_moves(self.color)

        # sorting by captures
        moves.sort(key=lambda m:
            self.board.board[m[1][0]][m[1][1]] is not None,
            reverse=True
        )

        for move in moves:
            self.board.move_piece(move[0], move[1])

            score = self.minimax(self.depth - 1, -math.inf, math.inf, True) ## OB
            #score = self.minimax(self.depth - 1, -math.inf, math.inf, False) ## OW

            self.board.undo_move()

            #if score > best_score: ##OW
            if score < best_score:
                best_score = score
                best_move = move

        if best_move:
            self.board.move_piece(best_move[0], best_move[1])

    def minimax(self, depth, alpha, beta, is_maximizing):
        if depth == 0:
            return self.board.evaluate()

        color = "w" if is_maximizing else "b"
        moves = self.board.get_all_legal_moves(color)

        if not moves:
            if self.board.is_in_check(color):
                # checkmate
                if is_maximizing:
                    return -99999  # white is checkmated → bad for white
                else:
                    return 99999   # black is checkmated → good for white
            else:
                return 0  # stalemate
            
        if is_maximizing:
            max_eval = -math.inf
            for move in moves:
                self.board.move_piece(move[0], move[1])
                eval = self.minimax(depth - 1, alpha, beta, False)
                self.board.undo_move()
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)

                if beta <= alpha:
                    break   
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                self.board.move_piece(move[0], move[1])
                eval = self.minimax(depth - 1, alpha, beta, True)
                self.board.undo_move()
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)

                if beta <= alpha:
                    break
            return min_eval