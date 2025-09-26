import pygame
from .piece import Piece
from .constants import BLACK, ROWS, RED, SQUARE_SIZE, COLS, WHITE

class Board:
    def __init__(self):
        """
        Initializes the game board, setting up the pieces and other game state variables.
        """
        self.board = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.create_board()

    def draw_squares(self, win):
        """
        Draws the checkers board squares on the given surface.

        Args:
        win (pygame.Surface): The surface to draw the squares on.
        """
        win.fill(BLACK)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, RED, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def evaluate(self):
        """
        Evaluates the board and returns a score based on the number of pieces and kings.

        Returns:
        float: The score of the board, considering the number of pieces and kings.
        """
        return self.white_left - self.red_left + (self.white_kings * 0.5 - self.red_kings * 0.5)

    def get_all_pieces(self, color):
        """
        Retrieves all pieces of a specified color.

        Args:
        color (int): The color of the pieces to retrieve (RED or WHITE).

        Returns:
        list: A list of Piece objects of the specified color.
        """
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces

    def move(self, piece, row, col):
        """
        Moves a piece to a new position on the board and handles kinging if necessary.

        Args:
        piece (Piece): The piece to move.
        row (int): The target row.
        col (int): The target column.
        """
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)

        if row == ROWS - 1 or row == 0:
            piece.make_king()
            if piece.color == WHITE:
                self.white_kings += 1
            else:
                self.red_kings += 1

    def get_piece(self, row, col):
        """
        Retrieves the piece at a specific position on the board.

        Args:
        row (int): The row of the piece.
        col (int): The column of the piece.

        Returns:
        Piece: The piece at the specified position, or 0 if no piece is present.
        """
        return self.board[row][col]

    def create_board(self):
        """
        Initializes the board with pieces in their starting positions.
        """
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, WHITE))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, RED))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        """
        Draws the entire board, including the pieces, on the given surface.

        Args:
        win (pygame.Surface): The surface to draw the board on.
        """
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def remove(self, pieces):
        """
        Removes specified pieces from the board and updates the count of remaining pieces.

        Args:
        pieces (list): A list of Piece objects to remove from the board.
        """
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
            if piece != 0:
                if piece.color == RED:
                    self.red_left -= 1
                else:
                    self.white_left -= 1

    def winner(self):
        """
        Determines the winner of the game based on the number of remaining pieces.

        Returns:
        int: The color of the winning player (RED or WHITE), or None if no winner yet.
        """
        if self.red_left <= 0:
            return WHITE
        elif self.white_left <= 0:
            return RED
        return None

    def get_valid_moves(self, piece):
        """
        Retrieves all valid moves for a given piece.

        Args:
        piece (Piece): The piece to find valid moves for.

        Returns:
        dict: A dictionary where keys are tuples representing target positions (row, col), and values are lists of pieces to be captured.
        """
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row

        if piece.color == RED or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == WHITE or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))

        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """
        Helper method to traverse the board to the left and find valid moves.

        Args:
        start (int): The starting row for traversal.
        stop (int): The ending row for traversal.
        step (int): The step direction for traversal (positive or negative).
        color (int): The color of the piece being moved.
        left (int): The starting column for traversal.
        skipped (list): List of pieces skipped in the traversal.

        Returns:
        dict: A dictionary where keys are tuples representing target positions (row, col), and values are lists of pieces to be captured.
        """
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break

            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1

        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        """
        Helper method to traverse the board to the right and find valid moves.

        Args:
        start (int): The starting row for traversal.
        stop (int): The ending row for traversal.
        step (int): The step direction for traversal (positive or negative).
        color (int): The color of the piece being moved.
        right (int): The starting column for traversal.
        skipped (list): List of pieces skipped in the traversal.

        Returns:
        dict: A dictionary where keys are tuples representing target positions (row, col), and values are lists of pieces to be captured.
        """
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break

            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1

        return moves
