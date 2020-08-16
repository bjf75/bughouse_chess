import pychess
from pychess import chess as chess
from pychess.chess import variant as variant

board = variant.BughouseSuperBoard()
board_normal = chess.Board()
# print(board_normal.parse_san("e10"))
print(board)

# sq1 = chess.Square("e2")
# Bottom left is 0, goes up 1 from right to left and resets and goes up
print(board.boardA.turn)
board.push(chess.Move(10, 20), board_id="A")
print(board.boardB.turn)
board.push(chess.Move(3, 51), board_id="B")
print(board.boardB.turn)
print(board)
print(board.get_pocket('A'))
print(board.get_pocket('B'))
