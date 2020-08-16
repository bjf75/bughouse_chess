import __init__ as chess
import engine
import variant

# bhouse_board = variant.BughouseSuperBoard()
# print(bhouse_board.unicode())


# normal_board = chess.Board()
# print(normal_board.unicode())

stockfish = engine.SimpleEngine.popen_uci("stockfish-10-mac/Mac/stockfish-10-64")

board = chess.Board()
while not board.is_game_over():
    result = stockfish.play(board, engine.Limit(time=0.100))
    board.push(result.move)
    print(board.unicode())
    print()

stockfish.quit()

# Crazyhouse Test

# stockfish = engine.SimpleEngine.popen_uci("./stockfish-osx-x86_64")

# board = variant.CrazyhouseBoard()
# while not board.is_game_over():
#     result = stockfish.play(board, engine.Limit(time=0.100))
#     board.push(result.move)
#     print(board.unicode())
#     print()

# stockfish.quit()
