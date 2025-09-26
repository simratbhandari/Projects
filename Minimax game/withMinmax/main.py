import pygame
from minimax.algorithm import minimax
from checkers.game import Game
from checkers.constants import WIDTH, HEIGHT, SQUARE_SIZE, RED, WHITE

FPS = 60

# Initialize the game window
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Checkers')

def get_row_col_from_mouse(pos):
    """
    Converts mouse position to board row and column indices.

    Args:
    pos (tuple): Mouse position (x, y).

    Returns:
    tuple: Row and column indices corresponding to the mouse position.
    """
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

def main():
    """
    Main function to run the checkers game.
    """
    run = True
    clock = pygame.time.Clock()
    game = Game(WIN)  # Initialize the Game instance

    while run:
        clock.tick(FPS)

        if game.turn == WHITE:
            # AI's turn: Use minimax algorithm to make a move
            value, new_board = minimax(game.get_board(), 3, WHITE, game)
            game.ai_move(new_board)

        # Check for winner and reset game if there is a winner
        if game.winner() is not None:
            if game.winner() == RED:
                print('RED WON!')
            elif game.winner() == WHITE:
                print('WHITE WON!')
            game.reset()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Player's turn: Select a piece to move
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                game.select(row, col)

        game.update()  # Update game state and draw the board

    pygame.quit()

if __name__ == "__main__":
    main()
