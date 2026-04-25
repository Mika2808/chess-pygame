class Board:
    def __init__(self):
        self.board = self.create_board()
        self.turn = "w" # white always starts
        self.en_passant_square = None # state for en passant
        self.move_history = [] # record of mvoes

        # Data for castling
        self.king_moved = { "w" : False, "b": False}
        self.rook_moved = {
            "w" : {"king_side": False, "queen_side": False},
            "b" : {"king_side": False, "queen_side": False},
            }


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

        # For moves record
        move = {
            "piece": piece,
            "start": start_pos,
            "end": end_pos,
            "captured": self.board[end_row][end_col] if self.board[end_row][end_col] is not None else None,
            
            "is_en_passant": False,
            "prev_en_passant": self.en_passant_square,
            "captured_pos": None,
            
            "promotion": None,
            "is_castling": False,
            "rook_start": None,
            "rook_end": None,
            "prev_king_moved": self.king_moved.copy(),
            "prev_rook_moved": {
                "w": self.rook_moved["w"].copy(),
                "b": self.rook_moved["b"].copy()
            }
        }   

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
            
            # promotion
            if piece[1] == "p":
                if end_row == 0 or end_row == 7:
                    move["promotion"] = "q"  # default queen
            
            # en passant
            if start_col != end_col and self.board[end_row][end_col] is None:
                move["is_en_passant"] = True
                move["captured_pos"] = (start_row, end_col)
                move["captured"] = self.board[start_row][end_col]
                move["prev_en_passant"] = self.en_passant_square

        # KNIGHT
        elif piece[1] == "n":
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
            # castling
            if abs(start_col - end_col) == 2:

                if not self.is_castling_move(start_pos, end_pos):
                    print("Illegal castling")
                    return

                move["is_castling"] = True

                row = start_row

                if end_col == 6:  # king side
                    move["rook_start"] = (row, 7)
                    move["rook_end"] = (row, 5)
                else:  # queen side
                    move["rook_start"] = (row, 0)
                    move["rook_end"] = (row, 3)

            else:
                # normal king move
                if not self.is_valid_king_move(piece, start_pos, end_pos):
                    print("Illegal king move!")
                    return
            

        # Check own king after move
        if not self.is_legal_move(start_pos, end_pos):
            print("Illegal move: king would be in check")
            return
        
        self.apply_move(move)

    def apply_move(self, move):
        start_row, start_col = move["start"]
        end_row, end_col = move["end"]

        piece = move["piece"]

        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None

        if move["captured"] and not move["is_en_passant"]:
            # already removed by overwrite, nothing extra needed
            pass

        if move["is_en_passant"]:
            r, c = move["captured_pos"]
            self.board[r][c] = None

        if move["promotion"]:
            self.board[end_row][end_col] = piece[0] + move["promotion"]
            self.en_passant_square = None

        if piece[1] == "p":
            if abs(start_row - end_row) == 2:
                ep_row = (start_row + end_row) // 2
                self.en_passant_square = (ep_row, start_col)

        self.turn = "b" if self.turn == "w" else "w"

        if piece[1] == "k":
            self.king_moved[piece[0]] = True

        if piece[1] == "r":
            if piece[0] == "w":
                if start_col == 0:
                    self.rook_moved["w"]["queen_side"] = True
                if start_col == 7:
                    self.rook_moved["w"]["king_side"] = True
            else:
                if start_col == 0:
                    self.rook_moved["b"]["queen_side"] = True
                if start_col == 7:
                    self.rook_moved["b"]["king_side"] = True        

        # CASTLING: move rook
        if move.get("is_castling"):
            rsr, rsc = move["rook_start"]
            rer, rec = move["rook_end"]

            rook = self.board[rsr][rsc]
            self.board[rer][rec] = rook
            self.board[rsr][rsc] = None

        self.move_history.append(move)

    def is_valid_pawn_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        direction = -1 if piece[0] == "w" else 1
        target = self.board[end_row][end_col]

        # 1. Forward move without capturing
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

        # 2. Capturing piece
        if abs(start_col - end_col) == 1 and end_row == start_row + direction:
            if target is not None and target[0] != piece[0]:
                return True

        # 3. En passant
        if abs(start_col - end_col) == 1 and end_row == start_row + direction:
            if target is None:
                # very simplified en passant placeholder
                if self.en_passant_square == (end_row, end_col):
                    return True

        return False
    
    def undo_move(self):
        if not self.move_history:
            return

        move = self.move_history.pop()

        start_row, start_col = move["start"]
        end_row, end_col = move["end"]

        piece = move["piece"]

        # STEP 1: restore moved piece
        self.board[start_row][start_col] = piece

        # STEP 2: restore destination square
        if move["is_en_passant"]:
            # en passant → destination square was EMPTY
            self.board[end_row][end_col] = None
        else:
            # normal move → restore captured piece (or None)
            self.board[end_row][end_col] = move["captured"]

        # STEP 3: undo castling
        if move["is_castling"]:
            rsr, rsc = move["rook_start"]
            rer, rec = move["rook_end"]

            rook = self.board[rer][rec]
            self.board[rsr][rsc] = rook
            self.board[rer][rec] = None

        # STEP 4: restore en passant capture
        if move["is_en_passant"]:
            r, c = move["captured_pos"]
            self.board[r][c] = move["captured"]

        # STEP 5: restore state
        self.king_moved = move["prev_king_moved"]
        self.rook_moved = move["prev_rook_moved"]
        self.en_passant_square = move["prev_en_passant"]

        # STEP 6: switch turn
        self.turn = "b" if self.turn == "w" else "w"

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

        # walk path
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
        # queen = rook val + bishop val
        return (self.is_valid_bishop_move(piece, start, end) or self.is_valid_rook_move(piece, start, end))
    
    def is_valid_king_move(self, piece, start, end):
        start_row, start_col = start
        end_row, end_col = end

        target = self.board[end_row][end_col]

        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)

        if row_diff <= 1 and col_diff <= 1:

            # cannot capture own piece
            if target is None or target[0] != piece[0]:
                return True

        return False
    
    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == color + "k":
                    return (r, c)
        return None
    
    def is_square_attacked(self, square, by_color):
        target_row, target_col = square

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]

                if piece is None:
                    continue

                if piece[0] != by_color:
                    continue

                p_type = piece[1]

                if p_type == "p":
                    if self.is_pawn_attacking(r, c, target_row, target_col, by_color):
                        return True

                elif p_type == "n":
                    if self.is_knight_attacking(r, c, target_row, target_col):
                        return True

                elif p_type == "b":
                    if self.is_bishop_attacking(r, c, target_row, target_col):
                        return True

                elif p_type == "r":
                    if self.is_rook_attacking(r, c, target_row, target_col):
                        return True

                elif p_type == "q":
                    if self.is_queen_attacking(r, c, target_row, target_col):
                        return True

                elif p_type == "k":
                    if self.is_king_attacking(r, c, target_row, target_col):
                        return True

        return False
    
    def is_in_check(self, color):
        king_pos = self.find_king(color)

        if king_pos is None:
            return False  # safety

        enemy_color = "b" if color == "w" else "w"

        return self.is_square_attacked(king_pos, enemy_color)
    
    def is_knight_attacking(self, r, c, tr, tc):
        return (abs(r - tr), abs(c - tc)) in [
            (2, 1), (1, 2)
        ]
    
    def is_pawn_attacking(self, r, c, tr, tc, color):
        direction = -1 if color == "w" else 1

        return (tr == r + direction and abs(tc - c) == 1)
    
    def is_bishop_attacking(self, r, c, tr, tc):
        if abs(tr - r) != abs(tc - c):
            return False

        dr = 1 if tr > r else -1
        dc = 1 if tc > c else -1

        rr, cc = r + dr, c + dc

        while (rr, cc) != (tr, tc):
            if self.board[rr][cc] is not None:
                return False
            rr += dr
            cc += dc

        return True
    
    def is_rook_attacking(self, r, c, tr, tc):
        if r != tr and c != tc:
            return False

        if r == tr:
            step = 1 if tc > c else -1
            cc = c + step

            while cc != tc:
                if self.board[r][cc] is not None:
                    return False
                cc += step

        else:
            step = 1 if tr > r else -1
            rr = r + step

            while rr != tr:
                if self.board[rr][c] is not None:
                    return False
                rr += step

        return True
    
    def is_queen_attacking(self, r, c, tr, tc):
        return (
            self.is_bishop_attacking(r, c, tr, tc) or
            self.is_rook_attacking(r, c, tr, tc)
        )
    
    def is_king_attacking(self, r, c, tr, tc):
        return max(abs(tr - r), abs(tc - c)) == 1
    
    def is_legal_move(self, start_pos, end_pos):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]

        if piece is None:
            return False

        # -----------------------
        # STEP 1: piece validation (CRITICAL FIX)
        # -----------------------
        valid = False

        if piece[1] == "p":
            valid = self.is_valid_pawn_move(piece, start_pos, end_pos)
        elif piece[1] == "n":
            valid = self.is_valid_knight_move(piece, start_pos, end_pos)
        elif piece[1] == "b":
            valid = self.is_valid_bishop_move(piece, start_pos, end_pos)
        elif piece[1] == "r":
            valid = self.is_valid_rook_move(piece, start_pos, end_pos)
        elif piece[1] == "q":
            valid = self.is_valid_queen_move(piece, start_pos, end_pos)
        elif piece[1] == "k":
             # NORMAL KING MOVE
            if self.is_valid_king_move(piece, start_pos, end_pos):
                valid = True

            # CASTLING MOVE (special case)
            elif abs(start_col - end_col) == 2:
                if self.is_castling_move(start_pos, end_pos):
                    valid = True
                else:
                    return False

        if not valid:
            return False

        # STEP 2: build move 
        move = {
            "piece": piece,
            "start": start_pos,
            "end": end_pos,
            "captured": self.board[end_row][end_col] if self.board[end_row][end_col] is not None else None,

            "is_en_passant": False,
            "prev_en_passant": self.en_passant_square,
            "captured_pos": None,

            "promotion": None,
            "is_castling": False,
            "rook_start": None,
            "rook_end": None,
            "prev_king_moved": self.king_moved.copy(),
            "prev_rook_moved": {
                "w": self.rook_moved["w"].copy(),
                "b": self.rook_moved["b"].copy()
            }
        }

        # STEP 3: special cases

        # en passant
        if piece[1] == "p":
            if start_col != end_col and self.board[end_row][end_col] is None:
                move["is_en_passant"] = True
                move["captured_pos"] = (start_row, end_col)
                move["captured"] = self.board[start_row][end_col]

        # castling (IMPORTANT: validate it)
        if piece[1] == "k" and abs(start_col - end_col) == 2:
            if not self.is_castling_move(start_pos, end_pos):
                return False

            move["is_castling"] = True

            row = start_row
            if end_col == 6:
                move["rook_start"] = (row, 7)
                move["rook_end"] = (row, 5)
            else:
                move["rook_start"] = (row, 0)
                move["rook_end"] = (row, 3)

        # STEP 4: simulate move
        self.apply_move(move)

        in_check = self.is_in_check(piece[0])

        # undo move
        self.undo_move()

        # STEP 5: final decision
        return not in_check
    
    def has_any_legal_move(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]

                if piece is None or piece[0] != color:
                    continue

                for tr in range(8):
                    for tc in range(8):
                        if (r, c) == (tr, tc):
                            continue

                        if self.is_legal_move((r, c), (tr, tc)):
                            return True

        return False
    
    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False

        return not self.has_any_legal_move(color)
    
    def is_stalemate(self, color):
        return (
            not self.is_in_check(color)
            and not self.has_any_legal_move(color)
        )
    
    def is_castling_move(self, start_pos, end_pos):
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        piece = self.board[start_row][start_col]
        color = piece[0]

        # must be king
        if piece[1] != "k":
            return False

        # must move 2 squares horizontally
        if abs(end_col - start_col) != 2:
            return False
        
        # must be the same row
        if start_row != end_row:
            return False
        
        # king cannot currently be in check
        if self.is_in_check(color):
            return False

        # determine side
        if end_col > start_col:
            return self.can_castle_kingside(color)
        else:
            return self.can_castle_queenside(color)
    
    def can_castle_kingside(self, color):
        row = 7 if color == "w" else 0
        enemy = "b" if color == "w" else "w"

        if self.king_moved[color]:
            return False

        if self.rook_moved[color]["king_side"]:
            return False

        # path must be empty
        if self.board[row][5] is not None or self.board[row][6] is not None:
            return False

        # squares must not be attacked
        if self.is_square_attacked((row, 5), enemy):
            return False
        if self.is_square_attacked((row, 6), enemy):
            return False

        return True
    
    def can_castle_queenside(self, color):
        row = 7 if color == "w" else 0
        enemy = "b" if color == "w" else "w"

        if self.king_moved[color]:
            return False

        if self.rook_moved[color]["queen_side"]:
            return False

        # path must be empty
        if (
            self.board[row][1] is not None or
            self.board[row][2] is not None or
            self.board[row][3] is not None
        ):
            return False

        # squares must not be attacked
        if self.is_square_attacked((row, 3), enemy):
            return False
        if self.is_square_attacked((row, 2), enemy):
            return False

        return True
    
    def get_legal_moves(self, start_pos):
        moves = []

        for row in range(8):
            for col in range(8):
                end_pos = (row, col)

                # reuse your existing logic
                if self.is_legal_move(start_pos, end_pos):
                    moves.append(end_pos)

        return moves