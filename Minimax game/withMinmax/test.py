import unittest
import pygame
import random
from checkers.board import Board
from checkers.game import Game
from minimax.algorithm import minimax
from checkers.constants import WIDTH, HEIGHT
from checkers.constants import ROWS, COLS
from checkers.game import Game

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
RED = (255, 0, 0)
WHITE = (255, 255, 255)

class GameTest(unittest.TestCase):

    def test_initial_game_state(self):
        board = Board()
        game = Game(WIN)
        score, move = minimax(board, 1, True, game)
        print(move)
        self.assertEqual(score, 0)
        for peice in board.get_all_pieces(RED):
            self.assertNotIn(move, board.get_valid_moves(peice))

   

    def test_draw_scenario(self):
        board = Board()
        game = Game(WIN)
        
        board.move(board.get_piece(2, 1), 3, 2)  
        score, move = minimax(board, 1, True, game)
        print("Draw scenario:", move)
        self.assertEqual(score, 0)  


    def test_opening_strategy(self):
        board = Board()
        game = Game(WIN)
        score, move = minimax(board, 1, True, game)
        print("Opening strategy:", move)
        self.assertIn(score, range(-5, 6))

    def test_complex_mid_game(self):
        board = Board()
        game = Game(WIN)
        board.move(board.get_piece(5, 0), 4, 1)
        board.move(board.get_piece(2, 1), 3, 0)
        score, move = minimax(board, 3, True, game)
        print("Complex mid game", move)
        self.assertTrue(score in range(-15, 16))  
    
    def test_ai_move(self):
        board = Board()
        game = Game(WIN)
        value, new_board = minimax(board, 3, WHITE, game)
        game.ai_move(new_board)
        self.assertNotEqual(board, game.get_board())  
        self.assertTrue(any(piece.color == WHITE for piece in game.get_board().get_all_pieces(WHITE)))  

    def test_board_evaluation(self):
        board = Board()
        game = Game(WIN)
        
        score = board.evaluate()
        self.assertTrue(score in range(-100, 101)) 

    def test_end_game(self):
        
        win = pygame.Surface((800, 800)) 
        game = Game(win)
        board = game.get_board()
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:  
                    piece = board.get_piece(row, col)
                    if piece and piece.color == WHITE:
                        board.remove([piece])
        
        
        game.ai_move(board)  
        self.assertEqual(game.winner(), RED)


    def test_draw_condition(self):
        board = Board()
        game = Game(WIN)
        
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    piece = board.get_piece(row, col)
                    if piece:  # Ensure piece is not 0 (empty)
                        board.remove([piece])
        
        
        game.update()  

        score, _ = minimax(board, 1, True, game)
        self.assertEqual(score, 0)  
    
   
    def test_invalid_move(self):
        board = Board()
        game = Game(WIN)
        piece = board.get_piece(2, 1)
        game.select(2, 1)  
        result = game._move(0, 3) 
        self.assertFalse(result)  
        self.assertEqual(board.get_piece(2, 1), piece) 
   

    def test_king_move(self):
        board = Board()
        piece = board.get_piece(5, 0)
        board.move(piece, 0, 5) 
        piece = board.get_piece(0, 5)
        board.move(piece, 1, 4) 
        self.assertEqual(board.get_piece(1, 4), piece)

   




if __name__ == '__main__':
    unittest.main()
