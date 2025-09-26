import pygame
from copy import deepcopy

RED = (255, 0, 0)
WHITE = (255, 255, 255)

def minimax(position, depth, max_player, game):
    """
    Implements the minimax algorithm with alpha-beta pruning to find the best move for a player.

    Args:
    position (Board): The current state of the game board.
    depth (int): The maximum depth of the search tree.
    max_player (bool): True if the current player is the maximizing player (WHITE), False if minimizing (RED).
    game (Game): The game instance.

    Returns:
    tuple: A tuple where the first element is the evaluation score of the board, and the second element is the best board position.
    """
    ## Write code here
    if depth == 0 or position.winner() != None:
        return position.evaluate(), position

    if max_player:
        max_eval = float('-inf')
        best_move = None
        for move in get_all_moves(position, WHITE, game):
            evaluation = minimax(move, depth - 1, False, game)[0]
            max_eval = max(max_eval, evaluation)
            if max_eval == evaluation:
                best_move = move

        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in get_all_moves(position, RED, game):
            evaluation = minimax(move, depth - 1, True, game)[0]
            min_eval = min(min_eval, evaluation)
            if min_eval == evaluation:
                best_move = move

        return min_eval, best_move

def simulate_move(piece, move, board, game, skip):
    """
    Simulates a move by updating the board with the given move and removing any skipped pieces.

    Args:
    piece (Piece): The piece being moved.
    move (tuple): The target (row, col) to move the piece to.
    board (Board): The current game board.
    game (Game): The game instance.
    skip (list): A list of pieces that are captured by the move.

    Returns:
    Board: The updated board state after the move.
    """
    board.move(piece, move[0], move[1])
    if skip:
        board.remove(skip)

    return board

def get_all_moves(board, color, game):
    """
    Generates all possible moves for a given color.

    Args:
    board (Board): The current game board.
    color (tuple): The color of the pieces to generate moves for (RED or WHITE).
    game (Game): The game instance.

    Returns:
    list: A list of board states resulting from all possible moves for the given color.
    """
    moves = []

    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            # Draw the potential move on the board (optional, currently commented out)
            # draw_moves(game, board, piece)
            temp_board = deepcopy(board)
            temp_piece = temp_board.get_piece(piece.row, piece.col)
            new_board = simulate_move(temp_piece, move, temp_board, game, skip)
            moves.append(new_board)

    return moves

def draw_moves(game, board, piece):
    """
    Draws the valid moves for a given piece on the board to help visualize potential moves.

    Args:
    game (Game): The game instance.
    board (Board): The current game board.
    piece (Piece): The piece for which to draw valid moves.
    """
    valid_moves = board.get_valid_moves(piece)
    board.draw(game.win)
    pygame.draw.circle(game.win, (0, 255, 0), (piece.x, piece.y), 50, 5)
    game.draw_valid_moves(valid_moves.keys())
    pygame.display.update()
    # pygame.time.delay(100)  # Optional delay for visualization
