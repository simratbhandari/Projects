import pygame
from .constants import RED, WHITE, SQUARE_SIZE, GREY, CROWN

class Piece:
    PADDING = 15
    OUTLINE = 2

    def __init__(self, row, col, color):
        """
        Initializes a piece with its position and color.

        Args:
        row (int): The row index of the piece on the board.
        col (int): The column index of the piece on the board.
        color (tuple): The color of the piece, typically RED or WHITE.
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()

    def calc_pos(self):
        """
        Calculates the position (x, y) of the piece based on its row and column.
        """
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2

    def make_king(self):
        """
        Promotes the piece to a king by setting the king attribute to True.
        """
        self.king = True

    def draw(self, win):
        """
        Draws the piece on the given window surface.

        Args:
        win (pygame.Surface): The surface on which to draw the piece.
        """
        radius = SQUARE_SIZE // 2 - self.PADDING
        pygame.draw.circle(win, GREY, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            win.blit(CROWN, (self.x - CROWN.get_width() // 2, self.y - CROWN.get_height() // 2))

    def move(self, row, col):
        """
        Updates the piece's position and recalculates its x, y coordinates.

        Args:
        row (int): The new row index of the piece.
        col (int): The new column index of the piece.
        """
        self.row = row
        self.col = col
        self.calc_pos()

    def __repr__(self):
        """
        Provides a string representation of the piece.

        Returns:
        str: The color of the piece as a string.
        """
        return str(self.color)
