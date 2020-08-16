import pychess
from pychess import chess
from pychess.chess import engine

#filename = "/Users/bryce/CS4701/bughouse-chess/pychess/chess/agents.py"
filename = "/Users/lpbreen/Desktop/CS4701-master/bughouse-chess/pychess/chess/agents.py"

#my_engine = engine.SimpleEngine.popen_uci(filename)
# print(1)
my_engine = engine.SimpleEngine.popen_xboard(filename)

board = chess.Board()
while not board.is_game_over():
    result = my_engine.play(board, engine.Limit(time=2))
    board.push(result.move)
    print(board.unicode())
    print()

my_engine.quit()