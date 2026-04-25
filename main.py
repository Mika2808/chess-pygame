from src.game.board import Board
from src.ui.game import Game

def main():
    board = Board()
    game = Game(board)
    game.run()

def test_check(board):
    board.board = [[None for _ in range(8)] for _ in range(8)]

    # white king
    board.board[7][4] = "wk"

    # black rook giving check
    board.board[0][4] = "br"

    print(board.is_in_check("w"))  # should be True    

def test_20_moves(board):
    moves = [
        ((6, 4), (4, 4)),  # e4
        ((1, 4), (3, 4)),  # e5
        ((7, 6), (5, 5)),  # Nf3
        ((0, 1), (2, 2)),  # Nc6
        ((7, 5), (4, 2)),  # bishop out
        ((0, 6), (2, 5)),  # knight out
        ((6, 3), (4, 3)),  # d4
        ((1, 3), (3, 3)),  # d5
        ((7, 1), (5, 2)),  # Nc3
        ((0, 5), (3, 2)),  # bishop attack line
        ((6, 2), (4, 2)),  # c pawn
        ((1, 2), (3, 2)),  # c pawn black
        ((7, 3), (3, 7)),  # queen diagonal attempt (if free)
        ((0, 3), (4, 7)),  # queen mirror idea
        ((6, 5), (5, 5)),  # pawn step
        ((1, 5), (2, 5)),  # pawn step
        ((7, 4), (6, 4)),  # king move attempt (usually invalid early but test)
        ((0, 4), (1, 4)),  # black king move attempt (also likely invalid)
        ((6, 6), (4, 6)),  # pawn push
        ((1, 6), (3, 6)),  # pawn push
    ]

    for i, (start, end) in enumerate(moves):
        print(f"\nMove {i+1}: {start} → {end}")
        board.move_piece(start, end)
        board.print_board()

    for i, (start, end) in enumerate(moves):
        print(f"\nMove {i+1}: {start} → {end}")
        board.undo_move()
        board.print_board()

if __name__ == "__main__":
    main()