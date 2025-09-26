import pygame
from checkers.board import Board
from .constants import RED, WHITE, BLUE, SQUARE_SIZE

class Game:
    def __init__(self, win):
        """
        Initializes the game state and sets up the game window.

        Args:
        win (pygame.Surface): The surface to draw the game on.
        """
        self._init()
        self.win = win

    def update(self):
        """
        Updates the game display by drawing the board and valid moves, and refreshing the screen.
        """
        self.board.draw(self.win)
        self.draw_valid_moves(self.valid_moves)
        pygame.display.update()

    def _init(self):
        """
        Resets the game state to its initial values.
        """
        self.selected = None
        self.board = Board()
        self.turn = RED
        self.valid_moves = {}

    def winner(self):
        """
        Checks if there is a winner.

        Returns:
        int: The color of the winner (RED or WHITE), or None if no winner yet.
        """
        return self.board.winner()  

    def reset(self):
        """
        Resets the game state to start a new game.
        """
        self._init()

    def select(self, row, col):
        """
        Selects a piece based on the provided row and column. If a piece is selected and moved successfully,
        the move is processed. If no valid move is made, the selection is cleared and re-attempted.

        Args:
        row (int): The row of the piece to select or move.
        col (int): The column of the piece to select or move.

        Returns:
        bool: True if the selection was successful, False otherwise.
        """
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        piece = self.board.get_piece(row, col)
        if piece != 0 and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True

        return False

    def _move(self, row, col):
        """
        Processes a move for the selected piece to the specified row and column. Updates the board and handles
        capturing of opponent's pieces if necessary.

        Args:
        row (int): The target row for the move.
        col (int): The target column for the move.

        Returns:
        bool: True if the move was successful, False otherwise.
        """
        piece = self.board.get_piece(row, col)
        if self.selected and piece == 0 and (row, col) in self.valid_moves:
            self.board.move(self.selected, row, col)
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove(skipped)
            self.change_turn()
        else:
            return False

        return True

    def draw_valid_moves(self, moves):
        """
        Draws indicators on the board for valid moves.

        Args:
        moves (dict): A dictionary where keys are tuples representing target positions (row, col), and values 
                      are lists of pieces that would be captured.
        """
        for move in moves:
            row, col = move
            pygame.draw.circle(self.win, BLUE, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)

    def change_turn(self):
        """
        Switches the turn between RED and WHITE players.
        """
        self.valid_moves = []
        if self.turn == RED:
            self.turn = WHITE
        else:
            self.turn = RED

    def get_board(self):
        """
        Retrieves the current board instance.

        Returns:
        Board: The current Board instance.
        """
        return self.board

    def ai_move(self, board):
        """
        Updates the board state with a new board configuration after an AI move.

        Args:
        board (Board): The updated Board instance after the AI move.
        """
        self.board = board
        self.change_turn()
