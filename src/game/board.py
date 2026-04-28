from src.game.evaluation import (
    PIECE_VALUES,
    PAWN_TABLE,
    KNIGHT_TABLE,
    BISHOP_TABLE,
    ROOK_TABLE,
    QUEEN_TABLE,
    KING_TABLE_MID
)

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
        
        
        # bitboards
        self.bitboards = {
            "wp": 0,
            "wn": 0,
            "wb": 0,
            "wr": 0,
            "wq": 0,
            "wk": 0,
            "bp": 0,
            "bn": 0,
            "bb": 0,
            "br": 0,
            "bq": 0,
            "bk": 0,
        }

        self.occupancy = {
            "w": 0,
            "b": 0,
            "all": 0
        }

        self.init_bitboards()
        self.update_occupancy()

        self.KNIGHT_MOVES = self.init_knight_moves()
        self.KING_MOVES = self.init_king_moves()
    
    def init_king_moves(self):
        moves = [0] * 64

        king_offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1),
        ]

        for row in range(8):
            for col in range(8):
                sq = row * 8 + col
                attacks = 0

                for dr, dc in king_offsets:
                    r = row + dr
                    c = col + dc

                    if 0 <= r < 8 and 0 <= c < 8:
                        target_sq = r * 8 + c
                        attacks |= (1 << target_sq)

                moves[sq] = attacks

        return moves
    
    def init_knight_moves(self):
        moves = [0] * 64

        knight_offsets = [
            (-2, -1), (-2, 1),
            (-1, -2), (-1, 2),
            (1, -2), (1, 2),
            (2, -1), (2, 1),
        ]

        for row in range(8):
            for col in range(8):
                sq = row * 8 + col
                attacks = 0

                for dr, dc in knight_offsets:
                    r = row + dr
                    c = col + dc

                    if 0 <= r < 8 and 0 <= c < 8:
                        target_sq = r * 8 + c
                        attacks |= (1 << target_sq)

                moves[sq] = attacks

        return moves
    
    def get_knight_moves_bb(self, color):
        moves = []

        knights = self.bitboards[color + "n"]
        own_occ = self.occupancy[color]

        while knights:
            sq = (knights & -knights).bit_length() - 1  # get LS1B index
            knights &= knights - 1  # remove LS1B

            attacks = self.KNIGHT_MOVES[sq]

            # remove own pieces
            attacks &= ~own_occ

            # iterate over attack squares
            while attacks:
                target_sq = (attacks & -attacks).bit_length() - 1
                attacks &= attacks - 1

                start = (sq // 8, sq % 8)
                end = (target_sq // 8, target_sq % 8)

                moves.append((start, end))

        return moves
    
    def get_king_moves_bb(self, color):
        moves = []

        king = self.bitboards[color + "k"]
        own_occ = self.occupancy[color]

        if king == 0:
            return []

        sq = (king & -king).bit_length() - 1

        attacks = self.KING_MOVES[sq]

        # remove own pieces
        attacks &= ~own_occ

        while attacks:
            target_sq = (attacks & -attacks).bit_length() - 1
            attacks &= attacks - 1

            start = (sq // 8, sq % 8)
            end = (target_sq // 8, target_sq % 8)

            moves.append((start, end))

        return moves
    
    def get_pawn_moves_bb(self, color):
        moves = []

        pawns = self.bitboards[color + "p"]
        own = self.occupancy[color]
        enemy = self.occupancy["b" if color == "w" else "w"]
        empty = ~self.occupancy["all"] & ((1 << 64) - 1)

        if color == "w":
            # -------------------
            # SINGLE PUSH
            # -------------------
            single = (pawns << 8) & empty

            # -------------------
            # DOUBLE PUSH
            # -------------------
            rank_2 = 0x000000000000FF00
            double = ((pawns & rank_2) << 16) & empty & (empty << 8)

            # -------------------
            # CAPTURES
            # -------------------
            cap_left = (pawns << 7) & enemy
            cap_right = (pawns << 9) & enemy

        else:
            # -------------------
            # SINGLE PUSH
            # -------------------
            single = (pawns >> 8) & empty

            # -------------------
            # DOUBLE PUSH
            # -------------------
            rank_7 = 0x00FF000000000000
            double = ((pawns & rank_7) >> 16) & empty & (empty >> 8)

            # -------------------
            # CAPTURES
            # -------------------
            cap_left = (pawns >> 9) & enemy
            cap_right = (pawns >> 7) & enemy

        return self._extract_pawn_moves(pawns, single, double, cap_left, cap_right, color)
    
    def _extract_pawn_moves(self, pawns, single, double, capL, capR, color):
        moves = []

        def pop(lsb):
            return (lsb & -lsb).bit_length() - 1

        # SINGLE PUSH
        temp = single
        while temp:
            to_sq = pop(temp)
            temp &= temp - 1

            from_sq = to_sq - 8 if color == "w" else to_sq + 8

            moves.append(((from_sq // 8, from_sq % 8),
                        (to_sq // 8, to_sq % 8)))

        # DOUBLE PUSH
        temp = double
        while temp:
            to_sq = pop(temp)
            temp &= temp - 1

            from_sq = to_sq - 16 if color == "w" else to_sq + 16

            moves.append(((from_sq // 8, from_sq % 8),
                        (to_sq // 8, to_sq % 8)))

        # CAPTURES
        for bb in [capL, capR]:
            temp = bb
            while temp:
                to_sq = pop(temp)
                temp &= temp - 1

                if color == "w":
                    from_sq1 = to_sq - 7
                    from_sq2 = to_sq - 9
                else:
                    from_sq1 = to_sq + 7
                    from_sq2 = to_sq + 9

                # pick correct pawn later (simplified version)
                from_sq = from_sq1 if self.bitboards[color + "p"] & (1 << from_sq1) else from_sq2

                moves.append(((from_sq // 8, from_sq % 8),
                            (to_sq // 8, to_sq % 8)))

        return moves
    
    def update_occupancy(self):
        self.occupancy["w"] = (
            self.bitboards["wp"] |
            self.bitboards["wn"] |
            self.bitboards["wb"] |
            self.bitboards["wr"] |
            self.bitboards["wq"] |
            self.bitboards["wk"]
        )

        self.occupancy["b"] = (
            self.bitboards["bp"] |
            self.bitboards["bn"] |
            self.bitboards["bb"] |
            self.bitboards["br"] |
            self.bitboards["bq"] |
            self.bitboards["bk"]
        )

        self.occupancy["all"] = self.occupancy["w"] | self.occupancy["b"]

    def set_bit(self, bb, square):
        return bb | (1 << square)

    def clear_bit(self, bb, square):
        return bb & ~(1 << square)

    def get_bit(self, bb, square):
        return (bb >> square) & 1
    
    def init_bitboards(self):
        self.bitboards = {
            "wp": 0, "wn": 0, "wb": 0, "wr": 0, "wq": 0, "wk": 0,
            "bp": 0, "bn": 0, "bb": 0, "br": 0, "bq": 0, "bk": 0
        }

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    sq = row * 8 + col
                    self.bitboards[piece] |= (1 << sq)
    
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
        self.en_passant_square = None

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

        start_sq = start_row * 8 + start_col
        end_sq = end_row * 8 + end_col
        captured = move["captured"]

        # remove piece from start
        self.bitboards[piece] = self.clear_bit(self.bitboards[piece], start_sq)

        # place on end
        self.bitboards[piece] = self.set_bit(self.bitboards[piece], end_sq)
        self.update_occupancy()
        if captured:
            self.bitboards[captured] = self.clear_bit(
                self.bitboards[captured], end_sq
            )

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

        captured = move["captured"]

        start_sq = start_row * 8 + start_col
        end_sq = end_row * 8 + end_col

        # STEP 1: restore moved piece
        self.board[start_row][start_col] = piece
        
        # bitboards: move piece back
        self.bitboards[piece] = self.clear_bit(self.bitboards[piece], end_sq)
        self.bitboards[piece] = self.set_bit(self.bitboards[piece], start_sq)
                                             
        # STEP 2: restore destination square
        if move["is_en_passant"]:
            # en passant → destination square was EMPTY
            self.board[end_row][end_col] = None
        else:
            # normal move → restore captured piece (or None)
            self.board[end_row][end_col] = move["captured"]
            
            if captured:
                # restore captured piece on end square
                self.bitboards[captured] = self.set_bit(
                    self.bitboards[captured], end_sq
                )

        # STEP 3: undo castling
        if move["is_castling"]:
            rsr, rsc = move["rook_start"]
            rer, rec = move["rook_end"]

            rook = self.board[rer][rec]

            # board
            self.board[rsr][rsc] = rook
            self.board[rer][rec] = None
            
            # bitboards
            rook_start_sq = rsr * 8 + rsc
            rook_end_sq = rer * 8 + rec

            self.bitboards[rook] = self.clear_bit(
                self.bitboards[rook], rook_end_sq
            )
            self.bitboards[rook] = self.set_bit(
                self.bitboards[rook], rook_start_sq
            )

        # STEP 4: restore en passant capture
        if move["is_en_passant"]:
            r, c = move["captured_pos"]
            self.board[r][c] = move["captured"]
            
            # bitboards
            cap_sq = r * 8 + c
            self.bitboards[captured] = self.set_bit(
                self.bitboards[captured], cap_sq
            )

        # STEP 5: restore state
        self.king_moved = move["prev_king_moved"]
        self.rook_moved = move["prev_rook_moved"]
        self.en_passant_square = move["prev_en_passant"]
        self.update_occupancy()
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
    
    def get_all_legal_moves(self, color):
        moves_all = []

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]

                if piece is not None and piece[0] == color:
                    start = (row, col)

                    for r in range(8):
                        for c in range(8):
                            end = (r, c)

                            if self.is_legal_move(start, end):
                                moves_all.append((start, end))

        return moves_all
    
    def evaluate(self):
        return (
            self.evaluate_material() +
            self.evaluate_pawns() +
            self.evaluate_knights() + 
            self.evaluate_bishops() + 
            self.bishop_pair_bonus() +
            self.evaluate_rooks() +
            self.evaluate_rook_files() +
            self.evaluate_rook_seventh_rank() + 
            self.evaluate_queens() +
            self.evaluate_king()
        )
    
    def evaluate_material(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            value = PIECE_VALUES[piece[1]]

            if piece[0] == "w":
                score += value
            else:
                score -= value

        return score
    
    def evaluate_pawns(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "p":
                continue

            if piece[0] == "w":
                score += PAWN_TABLE[row][col]
            else:
                score -= PAWN_TABLE[7 - row][col]

        return score
    
    def evaluate_knights(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "n":
                continue

            if piece[0] == "w":
                score += KNIGHT_TABLE[row][col]
            else:
                score -= KNIGHT_TABLE[7 - row][col]

        return score
    
    def evaluate_bishops(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "b":
                continue

            if piece[0] == "w":
                score += BISHOP_TABLE[row][col]
            else:
                score -= BISHOP_TABLE[7 - row][col]

        return score
    
    def bishop_pair_bonus(self):
        white_bishops = 0
        black_bishops = 0

        for piece, _, _ in self.get_all_pieces():
            if piece == "wb":
                white_bishops += 1
            elif piece == "bb":
                black_bishops += 1

        score = 0

        if white_bishops >= 2:
            score += 30
        if black_bishops >= 2:
            score -= 30

        return score
    
    def evaluate_rooks(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "r":
                continue

            if piece[0] == "w":
                score += ROOK_TABLE[row][col]
            else:
                score -= ROOK_TABLE[7 - row][col]

        return score
    
    def evaluate_rook_files(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "r":
                continue

            file_col = col

            own_pawn = False
            enemy_pawn = False

            for r in range(8):
                sq = self.board[r][file_col]
                if sq:
                    if sq[1] == "p":
                        if sq[0] == piece[0]:
                            own_pawn = True
                        else:
                            enemy_pawn = True

            # open file
            if not own_pawn and not enemy_pawn:
                if piece[0] == "w":
                    score += 25
                else:
                    score -= 25

            # semi-open file
            elif not own_pawn and enemy_pawn:
                if piece[0] == "w":
                    score += 10
                else:
                    score -= 10

        return score
    
    def evaluate_rook_seventh_rank(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "r":
                continue

            if piece[0] == "w" and row == 1:
                score += 20
            elif piece[0] == "b" and row == 6:
                score -= 20

        return score
    
    def evaluate_queens(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "q":
                continue

            if piece[0] == "w":
                score += QUEEN_TABLE[row][col]
            else:
                score -= QUEEN_TABLE[7 - row][col]

        return score
    
    def evaluate_king(self):
        score = 0

        for piece, row, col in self.get_all_pieces():
            if piece[1] != "k":
                continue

            if piece[0] == "w":
                score += KING_TABLE_MID[row][col]
            else:
                score -= KING_TABLE_MID[7 - row][col]

        return score
    
    def get_all_pieces(self):
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    yield piece, row, col