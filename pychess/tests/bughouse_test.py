import pychess
from pychess import chess as chess
from pychess.chess import variant as variant


board = variant.BughouseSuperBoard()

board.get_base_board("A").get_pocket(True).add(5)
print(board.get_base_board("A").get_pocket(True))
board.get_base_board("A").get_pocket(True).add(3)
board.get_base_board("A").get_pocket(True).add(1)
board.get_base_board("A").get_pocket(True).add(1)
board.get_base_board("A").get_pocket(False).add(5)
# board.get_base_board("A").get_pocket(False).add(1)
p = board.get_base_board("A").get_pocket(False).diff(board.get_base_board("A").get_pocket(True))
print(p)
# print(board)
# # print(board.boardB.turn)
# board.push(chess.Move(3, 51), board_id="B")
# print(board)
# print(board.fen())
# board.push(chess.Move(52, 2), board_id="B")
# print(board.fen())
# # print(board.boardB.turn)
# print(board)
# print(board.fen())
# print(board.get_pocket('A'))
# print(board.get_pocket('B'))


# board = variant.BughouseSuperBoard()
# board_normal = chess.Board()
# # print(board_normal.parse_san("e10"))
# print(board_normal)
# print(board_normal.fen())
# # board_normal.push(chess.Move(3, 51))
# ctr = 0
# for move in board.get_base_board("A").generate_legal_moves():
#     ctr += 1
# print(ctr)
# print(board.get_base_board("A").fullmove_number)
# board.push_san("e4", target="A")
# board.get_base_board("A").turn = chess.WHITE

# ctr = 0
# for move in board.get_base_board("A").generate_legal_moves():
#     ctr += 1
# print(ctr)


# print(board)
# board.push_san("e5", target="A")
# print(board)
# board.push_san("Qh5", target="A")
# print(board)
# board.push_san("d5", target="A")
# print(board)
# board.push_san("Qe5", target="A")
# print(board)
# board.push_san("Qe7", target="A")
# print(board)
# # print(board._attackers_mask(True))
# print(board.fen())


# crazy_board = variant.CrazyhouseBoard()
# print(crazy_board.board_fen())
# crazy_board.push(chess.Move(3, 51))
# print(crazy_board)
# print(crazy_board.board_fen())
# print(crazy_board.fen())
# print(crazy_board.castl)

# crazy_board.push_san("e4")
# print(crazy_board)
# board.push_san("e4", "A")
# print(board)

# Bottom left is 0, goes up 1 from right to left and resets and goes up
# print(board.boardA.turn)

#
# board.push(chess.Move(10, 20), board_id="A")
# print(board.fen())
# # print(board.boardB.turn)
# board.push(chess.Move(3, 51), board_id="B")
# print(board.fen())
# board.push(chess.Move(52, 2), board_id="B")
# print(board.fen())
# # print(board.boardB.turn)
# print(board)
# print(board.fen())
# print(board.get_pocket('A'))
# print(board.get_pocket('B'))
