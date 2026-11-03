'''
Built this game as a test. Sharing the source for anyone curious.

Game: https://ulsidae.itch.io/chess-with-math
'''
                                             
import tkinter as tk
from tkinter import messagebox, simpledialog
from dataclasses import dataclass
from typing import Optional
import copy, math
import time


FILES = "abcdefgh"
RANKS = "12345678"

WHITE = "white"
BLACK = "black"

EMPTY = None

PIECE_VALUES = { 
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000,
}

UNICODE_PIECES = {
    "white": {
        "P": "♙",
        "N": "♘",
        "B": "♗",
        "R": "♖",
        "Q": "♕",
        "K": "♔",
    },
    "black": {
        "P": "♟",
        "N": "♞",
        "B": "♝",
        "R": "♜",
        "Q": "♛",
        "K": "♚",
    },
}

def opponent(color):
    return BLACK if color == WHITE else WHITE


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def square_name(r, c):
    return FILES[c] + str(8 - r)


def square_from_name(name):
    c = FILES.index(name[0])
    r = 8 - int(name[1])
    return r, c


def color_of(piece):
    if piece is None:
        return None

    if piece.isupper():
        return WHITE

    return BLACK


def piece_type(piece):
    return piece.upper() if piece else None

@dataclass
class Move:
    start: tuple
    end: tuple

    promotion: Optional[str] = None

    is_castle: bool = False
    is_en_passant: bool = False

    captured: Optional[str] = None

    def notation(self):
        s = square_name(*self.start)
        e = square_name(*self.end)

        text = s + e

        if self.promotion:
            text += self.promotion.lower()

        return text

class Board:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [
            list("rnbqkbnr"),
            list("pppppppp"),
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]

        self.turn = WHITE

        self.white_castle_kingside = True
        self.white_castle_queenside = True
        self.black_castle_kingside = True
        self.black_castle_queenside = True

        self.en_passant_target = None

        self.halfmove_clock = 0
        self.fullmove_number = 1

        self.position_history = []


    def clone(self):
        return copy.deepcopy(self)


    def get(self, r, c):
        if not inside(r, c):
            return None

        return self.grid[r][c]

    def set(self, r, c, piece):
        self.grid[r][c] = piece


    def find_king(self, color):
        target = "K" if color == WHITE else "k"

        for r in range(8):
            for c in range(8):
                if self.grid[r][c] == target:
                    return (r, c)

        return None

    def is_square_attacked(self, r, c, by_color):
        # Pawn attacks
        if by_color == WHITE:
            pawn_row = r + 1

            if inside(pawn_row, c - 1):
                if self.grid[pawn_row][c - 1] == "P":
                    return True

            if inside(pawn_row, c + 1):
                if self.grid[pawn_row][c + 1] == "P":
                    return True

        else:
            pawn_row = r - 1

            if inside(pawn_row, c - 1):
                if self.grid[pawn_row][c - 1] == "p":
                    return True

            if inside(pawn_row, c + 1):
                if self.grid[pawn_row][c + 1] == "p":
                    return True

        # Knight attacks
        knight = "N" if by_color == WHITE else "n"

        knight_offsets = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]

        for dr, dc in knight_offsets:
            nr = r + dr
            nc = c + dc

            if inside(nr, nc) and self.grid[nr][nc] == knight:
                return True

        # King attacks
        king = "K" if by_color == WHITE else "k"

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue

                nr = r + dr
                nc = c + dc

                if inside(nr, nc) and self.grid[nr][nc] == king:
                    return True

        # Rook / Queen attacks
        rook = "R" if by_color == WHITE else "r"
        queen = "Q" if by_color == WHITE else "q"

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]

        for dr, dc in directions:
            nr = r + dr
            nc = c + dc

            while inside(nr, nc):
                piece = self.grid[nr][nc]

                if piece is not None:
                    if piece == rook or piece == queen:
                        return True

                    break

                nr += dr
                nc += dc

        # Bishop / Queen attacks
        bishop = "B" if by_color == WHITE else "b"

        directions = [
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]

        for dr, dc in directions:
            nr = r + dr
            nc = c + dc

            while inside(nr, nc):
                piece = self.grid[nr][nc]

                if piece is not None:
                    if piece == bishop or piece == queen:
                        return True

                    break

                nr += dr
                nc += dc

        return False

    def is_in_check(self, color):
        king = self.find_king(color)

        if king is None:
            return True

        return self.is_square_attacked(
            king[0],
            king[1],
            opponent(color),
        )

    def pseudo_moves_for_piece(self, r, c):
        piece = self.grid[r][c]

        if piece is None:
            return []

        color = color_of(piece)

        moves = []

        ptype = piece.upper()

        if ptype == "P":
            direction = -1 if color == WHITE else 1

            start_row = 6 if color == WHITE else 1

            promotion_row = 0 if color == WHITE else 7

            # Forward
            nr = r + direction

            if inside(nr, c) and self.grid[nr][c] is None:

                if nr == promotion_row:
                    for promo in "QRBN":
                        moves.append(
                            Move(
                                (r, c),
                                (nr, c),
                                promotion=promo,
                            )
                        )
                else:
                    moves.append(
                        Move(
                            (r, c),
                            (nr, c),
                        )
                    )

                # Double move
                nr2 = r + direction * 2

                if (
                    r == start_row
                    and inside(nr2, c)
                    and self.grid[nr2][c] is None
                ):
                    moves.append(
                        Move(
                            (r, c),
                            (nr2, c),
                        )
                    )

            # Captures
            for dc in (-1, 1):
                nr = r + direction
                nc = c + dc

                if not inside(nr, nc):
                    continue

                target = self.grid[nr][nc]

                if target is not None:
                    if color_of(target) != color:
                        if nr == promotion_row:
                            for promo in "QRBN":
                                moves.append(
                                    Move(
                                        (r, c),
                                        (nr, nc),
                                        promotion=promo,
                                        captured=target,
                                    )
                                )
                        else:
                            moves.append(
                                Move(
                                    (r, c),
                                    (nr, nc),
                                    captured=target,
                                )
                            )

                # En passant
                if self.en_passant_target == (nr, nc):
                    moves.append(
                        Move(
                            (r, c),
                            (nr, nc),
                            is_en_passant=True,
                        )
                    )

        elif ptype == "N":
            offsets = [
                (-2, -1),
                (-2, 1),
                (-1, -2),
                (-1, 2),
                (1, -2),
                (1, 2),
                (2, -1),
                (2, 1),
            ]

            for dr, dc in offsets:
                nr = r + dr
                nc = c + dc

                if not inside(nr, nc):
                    continue

                target = self.grid[nr][nc]

                if target is None or color_of(target) != color:
                    moves.append(
                        Move(
                            (r, c),
                            (nr, nc),
                            captured=target,
                        )
                    )


        elif ptype == "B":
            directions = [
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
            ]

            moves.extend(
                self.sliding_moves(
                    r,
                    c,
                    directions,
                    color,
                )
            )

        elif ptype == "R":
            directions = [
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            ]

            moves.extend(
                self.sliding_moves(
                    r,
                    c,
                    directions,
                    color,
                )
            )


        elif ptype == "Q":
            directions = [
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            ]

            moves.extend(
                self.sliding_moves(
                    r,
                    c,
                    directions,
                    color,
                )
            )

        elif ptype == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue

                    nr = r + dr
                    nc = c + dc

                    if not inside(nr, nc):
                        continue

                    target = self.grid[nr][nc]

                    if target is None or color_of(target) != color:
                        moves.append(
                            Move(
                                (r, c),
                                (nr, nc),
                                captured=target,
                            )
                        )

            # Castling
            if color == WHITE and r == 7 and c == 4:

                # Kingside
                if self.white_castle_kingside:
                    if (
                        self.grid[7][5] is None
                        and self.grid[7][6] is None
                        and self.grid[7][7] == "R"
                    ):
                        if (
                            not self.is_square_attacked(7, 4, BLACK)
                            and not self.is_square_attacked(7, 5, BLACK)
                            and not self.is_square_attacked(7, 6, BLACK)
                        ):
                            moves.append(
                                Move(
                                    (7, 4),
                                    (7, 6),
                                    is_castle=True,
                                )
                            )

                # Queenside
                if self.white_castle_queenside:
                    if (
                        self.grid[7][1] is None
                        and self.grid[7][2] is None
                        and self.grid[7][3] is None
                        and self.grid[7][0] == "R"
                    ):
                        if (
                            not self.is_square_attacked(7, 4, BLACK)
                            and not self.is_square_attacked(7, 3, BLACK)
                            and not self.is_square_attacked(7, 2, BLACK)
                        ):
                            moves.append(
                                Move(
                                    (7, 4),
                                    (7, 2),
                                    is_castle=True,
                                )
                            )

            elif color == BLACK and r == 0 and c == 4:

                # Kingside
                if self.black_castle_kingside:
                    if (
                        self.grid[0][5] is None
                        and self.grid[0][6] is None
                        and self.grid[0][7] == "r"
                    ):
                        if (
                            not self.is_square_attacked(0, 4, WHITE)
                            and not self.is_square_attacked(0, 5, WHITE)
                            and not self.is_square_attacked(0, 6, WHITE)
                        ):
                            moves.append(
                                Move(
                                    (0, 4),
                                    (0, 6),
                                    is_castle=True,
                                )
                            )

                # Queenside
                if self.black_castle_queenside:
                    if (
                        self.grid[0][1] is None
                        and self.grid[0][2] is None
                        and self.grid[0][3] is None
                        and self.grid[0][0] == "r"
                    ):
                        if (
                            not self.is_square_attacked(0, 4, WHITE)
                            and not self.is_square_attacked(0, 3, WHITE)
                            and not self.is_square_attacked(0, 2, WHITE)
                        ):
                            moves.append(
                                Move(
                                    (0, 4),
                                    (0, 2),
                                    is_castle=True,
                                )
                            )

        return moves

    def sliding_moves(self, r, c, directions, color):
        moves = []

        for dr, dc in directions:
            nr = r + dr
            nc = c + dc

            while inside(nr, nc):
                target = self.grid[nr][nc]

                if target is None:
                    moves.append(
                        Move(
                            (r, c),
                            (nr, nc),
                        )
                    )

                else:
                    if color_of(target) != color:
                        moves.append(
                            Move(
                                (r, c),
                                (nr, nc),
                                captured=target,
                            )
                        )

                    break

                nr += dr
                nc += dc

        return moves

    def legal_moves(self, color=None):
        if color is None:
            color = self.turn

        result = []

        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]

                if piece is None:
                    continue

                if color_of(piece) != color:
                    continue

                for move in self.pseudo_moves_for_piece(r, c):
                    test_board = self.clone()
                    test_board.make_move(move)

                    if not test_board.is_in_check(color):
                        result.append(move)

        return result

    def make_move(self, move):
        r1, c1 = move.start
        r2, c2 = move.end

        piece = self.grid[r1][c1]

        if piece is None:
            return

        color = color_of(piece)

        captured = self.grid[r2][c2]

        # En passant capture
        if move.is_en_passant:
            if color == WHITE:
                captured = self.grid[r2 + 1][c2]
                self.grid[r2 + 1][c2] = None
            else:
                captured = self.grid[r2 - 1][c2]
                self.grid[r2 - 1][c2] = None

        move.captured = captured

        # Move piece
        self.grid[r1][c1] = None

        # Promotion
        if move.promotion:
            promoted = move.promotion

            if color == BLACK:
                promoted = promoted.lower()

            self.grid[r2][c2] = promoted
        else:
            self.grid[r2][c2] = piece

        # Castling rook movement
        if move.is_castle:
            if c2 == 6:
                # Kingside
                rook = self.grid[r2][7]
                self.grid[r2][7] = None
                self.grid[r2][5] = rook

            elif c2 == 2:
                # Queenside
                rook = self.grid[r2][0]
                self.grid[r2][0] = None
                self.grid[r2][3] = rook

        # Update castling rights
        if piece == "K":
            self.white_castle_kingside = False
            self.white_castle_queenside = False

        elif piece == "k":
            self.black_castle_kingside = False
            self.black_castle_queenside = False

        elif piece == "R":
            if (r1, c1) == (7, 0):
                self.white_castle_queenside = False

            elif (r1, c1) == (7, 7):
                self.white_castle_kingside = False

        elif piece == "r":
            if (r1, c1) == (0, 0):
                self.black_castle_queenside = False

            elif (r1, c1) == (0, 7):
                self.black_castle_kingside = False

        # Captured rook destroys castling rights
        if captured == "R":
            if (r2, c2) == (7, 0):
                self.white_castle_queenside = False

            elif (r2, c2) == (7, 7):
                self.white_castle_kingside = False

        elif captured == "r":
            if (r2, c2) == (0, 0):
                self.black_castle_queenside = False

            elif (r2, c2) == (0, 7):
                self.black_castle_kingside = False

        # En passant target
        self.en_passant_target = None

        if piece.upper() == "P":
            if abs(r2 - r1) == 2:
                self.en_passant_target = (
                    (r1 + r2) // 2,
                    c1,
                )

        # Halfmove clock
        if piece.upper() == "P" or captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Fullmove
        if color == BLACK:
            self.fullmove_number += 1

        # Switch turn
        self.turn = opponent(self.turn)

    def is_checkmate(self, color):
        return (
            self.is_in_check(color)
            and len(self.legal_moves(color)) == 0
        )

    def is_stalemate(self, color):
        return (
            not self.is_in_check(color)
            and len(self.legal_moves(color)) == 0
        )

    def insufficient_material(self):
        pieces = []

        for row in self.grid:
            for piece in row:
                if piece is not None:
                    pieces.append(piece)

        # King vs King
        if all(p.upper() == "K" for p in pieces):
            return True

        # King + minor vs King
        if len(pieces) == 3:
            minor = sum(
                1 for p in pieces
                if p.upper() in ("B", "N")
            )

            return minor == 1

        # King + bishop vs king + bishop
        if len(pieces) == 4:
            if all(
                p.upper() in ("K", "B")
                for p in pieces
            ):
                bishops = []

                for r in range(8):
                    for c in range(8):
                        if self.grid[r][c] and self.grid[r][c].upper() == "B":
                            bishops.append((r + c) % 2)

                if len(bishops) == 2:
                    return bishops[0] == bishops[1]

        return False

    def is_threefold_repetition(self):
        if len(self.position_history) < 3:
            return False

        current = self.position_key()

        count = 0

        for key in self.position_history:
            if key == current:
                count += 1

        return count >= 3

    def position_key(self):
        board_string = ""

        for row in self.grid:
            for piece in row:
                board_string += piece or "."

        rights = (
            self.white_castle_kingside,
            self.white_castle_queenside,
            self.black_castle_kingside,
            self.black_castle_queenside,
        )

        return (
            board_string,
            self.turn,
            rights,
            self.en_passant_target,
        )

    def game_status(self):
        color = self.turn

        legal = self.legal_moves(color)

        if not legal:
            if self.is_in_check(color):
                return "checkmate"

            return "stalemate"

        if self.halfmove_clock >= 100:
            return "50move"

        if self.insufficient_material():
            return "insufficient"

        if self.is_threefold_repetition():
            return "repetition"

        return "playing"

class ChessAI:
    def __init__(self, color, depth=3):
        self.color = color
        self.depth = depth

        self.nodes = 0

        self.transposition = {}

    def choose_move(self, board):
        self.nodes = 0
        self.transposition.clear()

        moves = board.legal_moves(self.color)

        if not moves:
            return None

        ordered = self.order_moves(board, moves)

        best_move = ordered[0]
        best_score = -math.inf

        alpha = -math.inf
        beta = math.inf

        for move in ordered:
            child = board.clone()
            child.make_move(move)

            score = -self.search(
                child,
                self.depth - 1,
                -beta,
                -alpha,
            )

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move

    # Negamax!
    def search(self, board, depth, alpha, beta):
        self.nodes += 1

        status = board.game_status()

        if status == "checkmate":
            return -999999 - depth

        if status in (
            "stalemate",
            "50move",
            "insufficient",
            "repetition",
        ):
            return 0

        if depth <= 0:
            return self.evaluate(board)

        key = (
            board.position_key(),
            depth,
        )

        if key in self.transposition:
            return self.transposition[key]

        moves = board.legal_moves(board.turn)

        moves = self.order_moves(board, moves)

        best = -math.inf

        for move in moves:
            child = board.clone()
            child.make_move(move)

            score = -self.search(
                child,
                depth - 1,
                -beta,
                -alpha,
            )

            best = max(best, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        self.transposition[key] = best

        return best

    def evaluate(self, board):
        score = 0

        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]

                if piece is None:
                    continue

                value = PIECE_VALUES[piece.upper()]

                # Positional bonuses
                center_distance = abs(3.5 - r) + abs(3.5 - c)

                center_bonus = int(
                    (7 - center_distance) * 4
                )

                if piece.upper() == "P":
                    advance = (
                        6 - r
                        if piece.isupper()
                        else r - 1
                    )

                    value += advance * 8

                elif piece.upper() == "N":
                    value += center_bonus * 2

                elif piece.upper() == "B":
                    value += center_bonus

                if piece.isupper():
                    score += value
                else:
                    score -= value

        # Mobility
        current = board.turn

        mobility = len(board.legal_moves(current))

        if current == WHITE:
            score += mobility * 2
        else:
            score -= mobility * 2

        # King safety
        if board.is_in_check(WHITE):
            score -= 35

        if board.is_in_check(BLACK):
            score += 35

        if self.color == WHITE:
            return score

        return -score

    def order_moves(self, board, moves):
        scored = []

        for move in moves:
            score = 0

            if move.captured:
                score += (
                    PIECE_VALUES[move.captured.upper()]
                    * 10
                )

                piece = board.grid[
                    move.start[0]
                ][
                    move.start[1]
                ]

                score -= PIECE_VALUES[piece.upper()]

            if move.promotion:
                score += PIECE_VALUES[move.promotion]

            if move.is_castle:
                score += 50

            scored.append((score, move))

        scored.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        return [m for _, m in scored]

class ChessGUI:
    def __init__(self, root):
        self.root = root

        self.root.title("Chess with math - by ulsidae")
        self.root.resizable(False, False)

        self.board = Board()

        self.history = []

        self.selected = None

        self.legal_for_selected = []

        self.ai_enabled = True
        self.ai_color = BLACK

        self.ai_depth = 2

        self.ai_thinking = False

        self.move_number = 0

        self.last_move = None

        self.start_time = time.time()

        self.create_ui()

        self.update_ui()

    def create_ui(self):
        self.main = tk.Frame(
            self.root,
            bg="#202124",
        )

        self.main.pack(
            padx=15,
            pady=15,
        )

        self.title = tk.Label(
            self.main,
            text="Chess with math",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#202124",
        )

        self.title.pack(
            pady=(0, 10),
        )

        self.board_frame = tk.Frame(
            self.main,
            bg="#111111",
            bd=3,
            relief="solid",
        )

        self.board_frame.pack()

        self.buttons = []

        for r in range(8):
            row = []

            for c in range(8):
                button = tk.Button(
                    self.board_frame,
                    text="",
                    font=("Arial", 30),
                    width=2,
                    height=1,
                    relief="flat",
                    bd=0,
                    command=lambda rr=r, cc=c: self.on_square_click(rr, cc),
                )

                button.grid(
                    row=r,
                    column=c,
                )

                row.append(button)

            self.buttons.append(row)

        self.status = tk.Label(
            self.main,
            text="",
            font=("Arial", 13, "bold"),
            fg="white",
            bg="#202124",
        )

        self.status.pack(
            pady=10,
        )

        self.moves_label = tk.Label(
            self.main,
            text="Moves: 0",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#202124",
        )

        self.moves_label.pack()

        controls = tk.Frame(
            self.main,
            bg="#202124",
        )

        controls.pack(
            pady=10,
        )

        tk.Button(
            controls,
            text="New Game",
            width=12,
            command=self.new_game,
        ).grid(row=0, column=0, padx=4)

        tk.Button(
            controls,
            text="Undo",
            width=12,
            command=self.undo,
        ).grid(row=0, column=1, padx=4)

        tk.Button(
            controls,
            text="AI: ON",
            width=12,
            command=self.toggle_ai,
        ).grid(row=0, column=2, padx=4)

        tk.Button(
            controls,
            text="AI Depth",
            width=12,
            command=self.change_depth,
        ).grid(row=0, column=3, padx=4)

        self.ai_label = tk.Label(
            self.main,
            text="You: White    AI: Black",
            fg="#aaaaaa",
            bg="#202124",
            font=("Arial", 10),
        )

        self.ai_label.pack()

    def square_color(self, r, c):
        if (r + c) % 2 == 0:
            return "#f0d9b5"

        return "#b58863"

    def update_ui(self):
        selected_moves = {
            move.end
            for move in self.legal_for_selected
        }

        for r in range(8):
            for c in range(8):
                button = self.buttons[r][c]

                base = self.square_color(r, c)

                # Last move highlight
                if self.last_move:
                    if (
                        (r, c) == self.last_move.start
                        or
                        (r, c) == self.last_move.end
                    ):
                        base = "#c9b458"

                # Selected square
                if self.selected == (r, c):
                    base = "#7fc97f"

                # Legal move
                if (r, c) in selected_moves:
                    base = "#90c8ff"

                # Check
                piece = self.board.grid[r][c]

                if piece:
                    color = color_of(piece)

                    if piece.upper() == "K":
                        if self.board.is_in_check(color):
                            base = "#e57373"

                button.configure(
                    bg=base,
                    activebackground=base,
                )

                if piece:
                    button.configure(
                        text=UNICODE_PIECES[
                            color_of(piece)
                        ][
                            piece.upper()
                        ],
                        fg=(
                            "#111111"
                            if color_of(piece) == WHITE
                            else "#000000"
                        ),
                    )
                else:
                    button.configure(
                        text="",
                    )

        self.moves_label.configure(
            text=f"Moves: {self.move_number}",
        )

        self.update_status()

    def update_status(self):
        status = self.board.game_status()

        if status == "checkmate":
            winner = opponent(self.board.turn)

            self.status.configure(
                text=f"CHECKMATE — {winner.upper()} WINS"
            )

            return

        if status == "stalemate":
            self.status.configure(
                text="STALEMATE — DRAW"
            )

            return

        if status == "50move":
            self.status.configure(
                text="50-MOVE RULE — DRAW"
            )

            return

        if status == "insufficient":
            self.status.configure(
                text="INSUFFICIENT MATERIAL — DRAW"
            )

            return

        if status == "repetition":
            self.status.configure(
                text="THREEFOLD REPETITION — DRAW"
            )

            return

        if self.ai_thinking:
            self.status.configure(
                text="AI IS THINKING..."
            )

            return

        turn_text = (
            "WHITE"
            if self.board.turn == WHITE
            else "BLACK"
        )

        if self.board.is_in_check(self.board.turn):
            self.status.configure(
                text=f"{turn_text} — CHECK!"
            )
        else:
            self.status.configure(
                text=f"{turn_text} TO MOVE"
            )

    def on_square_click(self, r, c):
        if self.ai_thinking:
            return

        if self.board.game_status() != "playing":
            return

        # AI's turn
        if self.ai_enabled and self.board.turn == self.ai_color:
            return

        piece = self.board.grid[r][c]

        # Nothing selected
        if self.selected is None:
            if piece and color_of(piece) == self.board.turn:
                self.selected = (r, c)

                self.legal_for_selected = [
                    move
                    for move in self.board.legal_moves(
                        self.board.turn
                    )
                    if move.start == self.selected
                ]

                self.update_ui()

            return

        # Clicking own piece switches selection
        if piece and color_of(piece) == self.board.turn:
            self.selected = (r, c)

            self.legal_for_selected = [
                move
                for move in self.board.legal_moves(
                    self.board.turn
                )
                if move.start == self.selected
            ]

            self.update_ui()

            return

        # Try selected move
        chosen = None

        for move in self.legal_for_selected:
            if move.end == (r, c):
                chosen = move
                break

        if chosen is None:
            self.selected = None
            self.legal_for_selected = []

            self.update_ui()

            return

        # Promotion dialog
        if chosen.promotion:
            promotion = self.ask_promotion()

            if promotion is None:
                return

            chosen.promotion = promotion

        self.execute_move(chosen)

    def ask_promotion(self):
        dialog = tk.Toplevel(self.root)

        dialog.title("Promotion")

        dialog.transient(self.root)

        dialog.grab_set()

        result = {
            "value": None
        }

        tk.Label(
            dialog,
            text="Choose promotion:",
            font=("Arial", 14, "bold"),
        ).pack(padx=20, pady=15)

        def choose(value):
            result["value"] = value
            dialog.destroy()

        for piece, name in [
            ("Q", "Queen"),
            ("R", "Rook"),
            ("B", "Bishop"),
            ("N", "Knight"),
        ]:
            tk.Button(
                dialog,
                text=name,
                width=15,
                command=lambda p=piece: choose(p),
            ).pack(
                padx=20,
                pady=4,
            )

        self.root.wait_window(dialog)

        return result["value"]

    def execute_move(self, move):
        self.history.append(
            self.board.clone()
        )

        self.board.make_move(move)

        self.board.position_history.append(
            self.board.position_key()
        )

        self.move_number += 1

        self.last_move = move

        self.selected = None

        self.legal_for_selected = []

        self.update_ui()

        if self.board.game_status() != "playing":
            self.show_game_end()

            return

        # AI
        if (
            self.ai_enabled
            and self.board.turn == self.ai_color
        ):
            self.start_ai()

    def start_ai(self):
        self.ai_thinking = True

        self.update_ui()

        self.root.after(
            100,
            self.run_ai,
        )

    def run_ai(self):
        ai = ChessAI(
            self.ai_color,
            depth=self.ai_depth,
        )

        move = ai.choose_move(
            self.board
        )

        self.ai_thinking = False

        if move:
            self.execute_move(move)

        self.update_ui()

    def new_game(self):
        self.board = Board()

        self.history.clear()

        self.selected = None

        self.legal_for_selected = []

        self.last_move = None

        self.move_number = 0

        self.ai_thinking = False

        self.board.position_history.append(
            self.board.position_key()
        )

        self.update_ui()

    def undo(self):
        if not self.history:
            return

        # Undo player's move
        self.board = self.history.pop()

        self.move_number = max(
            0,
            self.move_number - 1,
        )

        self.selected = None

        self.legal_for_selected = []

        self.last_move = None

        # If AI was enabled, also undo AI's previous move
        if (
            self.ai_enabled
            and self.board.turn == self.ai_color
            and self.history
        ):
            self.board = self.history.pop()

            self.move_number = max(
                0,
                self.move_number - 1,
            )

        self.ai_thinking = False

        self.update_ui()

    def toggle_ai(self):
        self.ai_enabled = not self.ai_enabled

        # Find the toggle button
        controls = self.main.winfo_children()

        for widget in controls:
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button):
                        if child.cget("text").startswith("AI:"):
                            child.configure(
                                text=(
                                    "AI: ON"
                                    if self.ai_enabled
                                    else "AI: OFF"
                                )
                            )

        self.ai_label.configure(
            text=(
                "You: White    AI: Black"
                if self.ai_enabled
                else "Human vs Human"
            )
        )

        self.update_ui()

    def change_depth(self):
        value = simpledialog.askinteger(
            "AI Depth",
            "Enter AI depth (1-4):",
            initialvalue=self.ai_depth,
            minvalue=1,
            maxvalue=4,
        )

        if value:
            self.ai_depth = value

            self.status.configure(
                text=f"AI depth changed to {value}"
            )

    def show_game_end(self):
        status = self.board.game_status()

        if status == "checkmate":
            winner = opponent(
                self.board.turn
            )

            messagebox.showinfo(
                "Game Over",
                f"Checkmate!\n\n{winner.upper()} wins.",
            )

        elif status == "stalemate":
            messagebox.showinfo(
                "Game Over",
                "Stalemate.\n\nDraw.",
            )

        elif status == "50move":
            messagebox.showinfo(
                "Game Over",
                "50-move rule.\n\nDraw.",
            )

        elif status == "insufficient":
            messagebox.showinfo(
                "Game Over",
                "Insufficient material.\n\nDraw.",
            )

        elif status == "repetition":
            messagebox.showinfo(
                "Game Over",
                "Threefold repetition.\n\nDraw.",
            )

def print_board(board):
    print()

    print("    a b c d e f g h")
    print("   -----------------")

    for r in range(8):
        rank = 8 - r

        line = f"{rank} |"

        for c in range(8):
            piece = board.grid[r][c]

            if piece:
                symbol = UNICODE_PIECES[
                    color_of(piece)
                ][
                    piece.upper()
                ]

            else:
                symbol = "."

            line += f" {symbol}"

        line += f" | {rank}"

        print(line)

    print("   -----------------")
    print("    a b c d e f g h")
    print()

def cli_game():
    board = Board()

    board.position_history.append(
        board.position_key()
    )

    print()
    print("=" * 40)
    print("          PYTHON CHESS")
    print("=" * 40)

    while True:
        print_board(board)

        status = board.game_status()

        if status != "playing":
            print("GAME OVER:", status)
            break

        print(
            f"{board.turn.upper()} TO MOVE"
        )

        raw = input(
            "Move (e2e4 / quit): "
        ).strip().lower()

        if raw == "quit":
            break

        if len(raw) not in (4, 5):
            print("Invalid move.")
            continue

        try:
            start = square_from_name(
                raw[:2]
            )

            end = square_from_name(
                raw[2:4]
            )

        except Exception:
            print("Invalid square.")
            continue

        promotion = None

        if len(raw) == 5:
            promotion = raw[4].upper()

            if promotion not in "QRBN":
                print("Invalid promotion.")
                continue

        candidates = [
            move
            for move in board.legal_moves(
                board.turn
            )
            if move.start == start
            and move.end == end
        ]

        if not candidates:
            print("Illegal move.")
            continue

        move = candidates[0]

        if move.promotion:
            move.promotion = (
                promotion or "Q"
            )

        board.make_move(move)

        board.position_history.append(
            board.position_key()
        )

def main():
    root = tk.Tk()

    app = ChessGUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()
