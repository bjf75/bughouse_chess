import pychess
import os
from pychess import chess
from pychess.chess import engine 
from pychess.chess import variant 

# filename = "../script-runners/script1.sh"
# filename = "/Users/bryce/CS4701/bughouse-chess/pychess/script-runners/script1.sh"
filename = "/Users/bryce/CS4701/bughouse-chess/pychess/ai/agents.py"
# filename = "/Users/bryce/CS4701/bughouse-chess/pychess/ai/agents.py"

print(os.getcwd())

engine = chess.engine.SimpleEngine.popen_uci(filename)

board = chess.variant.BughouseSuperBoard()
info = engine.analyse(board, chess.engine.Limit(time=0.100))
print("Score:", info["score"])
# Score: +20

# board = chess.variant.Board("r1bqkbnr/p1pp1ppp/1pn5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 2 4")
# info = engine.analyse(board, chess.engine.Limit(depth=20))
# print("Score:", info["score"])
# Score: #1

engine.quit()