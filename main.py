from src.game.board import Board
from src.ui.game import Game
import copy

def main():
    board = Board()
    game = Game(board)
    game.run()

### TESTING

def test_bishop_empty():
    board = Board()

    board.board = [[None for _ in range(8)] for _ in range(8)]
    board.board[4][4] = "wb"

    board.init_bitboards()
    board.update_occupancy()

    moves = board.get_bishop_moves_bb("w")

    print("Bishop from (4,4):")
    for m in moves:
        print(m)

def test_rook_empty():
    board = Board()

    # clear board completely
    board.board = [[None for _ in range(8)] for _ in range(8)]

    # place one white rook in center
    board.board[4][4] = "wr"

    # rebuild bitboards
    board.init_bitboards()
    board.update_occupancy()

    moves = board.get_rook_moves_bb("w")

    print("Rook moves from (4,4):")
    for m in moves:
        print(m)

def test_pawns():
    board = Board()

    print("White pawn moves:")
    print(bin(board.bitboards["wp"]))
    print(board.occupancy["all"])
    for row in board.board:
        print(row)

    print("wp:", bin(board.bitboards["wp"]))
    print("bp:", bin(board.bitboards["bp"]))
    print("wr:", bin(board.bitboards["wr"]))
    print("br:", bin(board.bitboards["br"]))
    print("occupancy w:", bin(board.occupancy["w"]))
    print("occupancy b:", bin(board.occupancy["b"]))
    print("occupancy all:", bin(board.occupancy["all"]))

    moves = board.get_pawn_moves_bb("b")

    for m in moves:
        print(m)

def test_undo():
    board = Board()

    # init bitboards if not already in __init__
    board.init_bitboards()

    print("Initial board:")
    for row in board.board:
        print(row)

    # save state
    board_before = copy.deepcopy(board.board)
    bitboards_before = board.bitboards.copy()

    # make a move (example: white pawn e2 → e4)
    start = (6, 4)
    end = (4, 4)

    print("\nMaking move:", start, "->", end)
    board.move_piece(start, end)

    print("\nBoard after move:")
    for row in board.board:
        print(row)

    # undo
    print("\nUndoing move...")
    board.undo_move()

    print("\nBoard after undo:")
    for row in board.board:
        print(row)

    print("\nBoard restored:", board.board == board_before)

    bitboards_equal = True
    for k in bitboards_before:
        if board.bitboards[k] != bitboards_before[k]:
            print(f"Mismatch in bitboard {k}")
            bitboards_equal = False

    print("Bitboards restored:", bitboards_equal)


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


if __name__ == "__main__":
    main()