class Board:
    def __init__(self):
        self.board = self.create_board()
        self.turn = "w" # white always starts
        self.en_passant_square = None

    def create_board(self):
        # Empty 8x8 board
        board = [[None for _ in range(8)] for _ in range(8)]

        # Back row piece order
        pieces = ["r", "n", "b", "q", "k", "b", "n", "r"]

        # Place black pieces
        for col in range(8):
            board[0][col] = "b" + pieces[col]  # black back rank
            board[1][col] = "bp"              # black pawns

        # Place white pieces
        for col in range(8):
            board[6][col] = "wp"              # white pawns
            board[7][col] = "w" + pieces[col]  # white back rank

        return board

    def print_board(self):
        print("\nCurrent Board:\n")
        for row in self.board:
            print(" ".join([piece if piece else "--" for piece in row]))

    def get_piece(self, row, col):
        return self.board[row][col]
    
    def move_piece(self, start_pos, end_pos):
        # Reading the start/end positions 
        start_row, start_col = start_pos 
        end_row, end_col = end_pos

        # Get piece
        piece = self.board[start_row][start_col]

        # Temp for no piece
        if piece is None:
            print("No piece was chosen")
            return
        
        # Check if it's correct turn
        if piece[0] != self.turn:
            print(f"It's {self.turn} turn")
            return

        # PAWN
        if piece[1] == "p":
            if not self.is_valid_pawn_move(piece, start_pos, end_pos):
                print("Illegal pawn move!")
                return
             
            # -----------------------
            # SET EN PASSANT TARGET
            # -----------------------
            self.en_passant_square = None

            # double move creates en passant opportunity
            if abs(start_row - end_row) == 2:
                ep_row = (start_row + end_row) // 2
                self.en_passant_square = (ep_row, start_col)

            # -----------------------
            # HANDLE EN PASSANT CAPTURE
            # -----------------------
            if start_col != end_col and self.board[end_row][end_col] is None:
                # capture pawn behind target square
                self.board[start_row][end_col] = None
        # KNIGHT
        elif piece[0] == "n":
            if not self.is_valid_knight_move(piece, start_pos, end_pos):
                print("Illegal knight move!")
                return
        # ROCK
        elif piece[1] == "r":
            if not self.is_valid_rook_move(piece, start_pos, end_pos):
                print("Illegal rook move!")
                return
        # BISHOP
        elif piece[1] == "b":
            if not self.is_valid_bishop_move(piece, start_pos, end_pos):
                print("Illegal bishop move!")
                return
        # QUEEN
        elif piece[1] == "q":
            if not self.is_valid_queen_move(piece, start_pos, end_pos):
                print("Ilegal queen move!")
                return
        # KING
        elif piece[1] == "k":
            if not self.is_valid_king_move(piece, start_pos, end_pos):
                print("Illegal king move!")
                return
            
        # Moving piece
        self.board[end_row][end_col] = piece # new pos
        self.board[start_row][start_col] = None # clearing old pos

        # Switch turn 
        self.turn = "b" if self.turn == "w" else "w"

    def is_valid_pawn_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        direction = -1 if piece[0] == "w" else 1
        target = self.board[end_row][end_col]

        # -----------------------
        # 1. FORWARD MOVE (NO CAPTURE)
        # -----------------------
        if start_col == end_col:
            # must be empty
            if target is not None:
                return False

            # 1 step forward
            if end_row == start_row + direction:
                return True

            # 2 step forward (only from start)
            if piece[0] == "w" and start_row == 6 and end_row == 4:
                return self.board[5][start_col] is None and self.board[4][start_col] is None

            if piece[0] == "b" and start_row == 1 and end_row == 3:
                return self.board[2][start_col] is None and self.board[3][start_col] is None

        # -----------------------
        # 2. CAPTURE MOVE
        # -----------------------
        if abs(start_col - end_col) == 1 and end_row == start_row + direction:
            if target is not None and target[0] != piece[0]:
                return True

        # -----------------------
        # 3. EN PASSANT
        # -----------------------
        if abs(start_col - end_col) == 1 and end_row == start_row + direction:
            if target is None:
                # very simplified en passant placeholder
                if self.en_passant_square == (end_row, end_col):
                    return True

        return False
    
    def is_valid_knight_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)

        # Knight moves: (2,1) or (1,2)
        if (row_diff, col_diff) in [(2, 1), (1, 2)]:
            target = self.board[end_row][end_col]

            # cannot capture own piece
            if target is None or target[0] != piece[0]:
                return True

        return False
    
    def is_valid_rook_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        target = self.board[end_row][end_col]

        # must move in straight line
        if start_row != end_row and start_col != end_col:
            return False

        # direction step
        step_row = 0
        step_col = 0

        if end_row > start_row:
            step_row = 1
        elif end_row < start_row:
            step_row = -1

        if end_col > start_col:
            step_col = 1
        elif end_col < start_col:
            step_col = -1

        # walk path
        r, c = start_row + step_row, start_col + step_col

        while (r, c) != (end_row, end_col):
            if self.board[r][c] is not None:
                return False  # blocked
            r += step_row
            c += step_col

        # destination check
        if target is None or target[0] != piece[0]:
            return True

        return False
    
    def is_valid_bishop_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        target = self.board[end_row][end_col]

        # must move diagonally
        if abs(end_row - start_row) != abs(end_col - start_col):
            return False

        # direction
        step_row = 1 if end_row > start_row else -1
        step_col = 1 if end_col > start_col else -1

        # walk path (same idea as rook)
        r = start_row + step_row
        c = start_col + step_col

        while (r, c) != (end_row, end_col):
            if self.board[r][c] is not None:
                return False  # blocked
            r += step_row
            c += step_col

        # destination check
        if target is None or target[0] != piece[0]:
            return True

        return False
    
    def is_valid_queen_move(self, piece, start, end):
        return (self.is_valid_bishop_move(piece, start, end) or self.is_valid_rook_move(piece, start, end))
    
    def is_valid_king_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        target = self.board[end_row][end_col]

        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)

        # must move at most 1 square in any direction
        if row_diff <= 1 and col_diff <= 1:

            # cannot capture own piece
            if target is None or target[0] != piece[0]:
                return True

        return False