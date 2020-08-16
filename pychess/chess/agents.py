#! /usr/local/bin/python3

import pychess
from pychess import chess
from pychess.chess import variant
from pychess.chess import ai 
from pychess.chess import utility
import time

from typing import ClassVar, Callable, Dict, Generic, Hashable, Iterable, Iterator, List, Mapping, MutableSet, Optional, SupportsInt, Tuple, Type, TypeVar, Union

import asyncio
import sys


class UCIAgent():
    """
    """

    def __init__(self, name):
        self.name = name

    @staticmethod
    def logandprint(msg, logfile):
        logfile.write(msg + '\n')
        print(msg, file=sys.stdout)

    def parse_commands(self):
        """
        parses uci commands when received
        """
        filename = "mylog.txt"
        with open(filename, 'w') as mylog:

            while True:
                cmd = input()
                if cmd == 'quit':
                    break

                elif cmd == 'uci':
                    UCIAgent.logandprint('id name Liam', mylog)
                    UCIAgent.logandprint('id author Liam', mylog)
                    UCIAgent.logandprint('uciok', mylog)

                elif cmd == 'isready':
                    UCIAgent.logandprint('readyok', mylog)

                elif cmd[0:2] == 'go':
                    UCIAgent.logandprint('bestmove e2e4', mylog)
                # elif cmd
            # for line in sys.stdin:
            #     mylog.write(line)
            #     if line == 'uci':
            #         sys.stdout.write("id name {name}\n".format(self.name))
            #         sys.stdout.write("uciok\n")
            #         sys.stdout.flush()
            #         continue
                # if line == 'isready':
                #     sys.stdout.write("readyok\n")
                #     sys.stdout.flush()
                #     continue
                # if line == 'quit':
                #     break
                # print(line)

        # uci
        # debug
        # isready
        # setoption name <id> [value <x>]
        # register
        # ucinewgame
        # position [fen <fenstring> | startpos ]  moves <move1> .... <movei>
        # go
            # searchmoves <move1> .... <movei>
            # ponder
            # wtime <x>
            # btime <x>
            # winc <x>
            # binc <x>
            # movestop <x>
            # depth <x>
            # nodes <x>
            # mate <x>
            # movetime <x>
            # infinite
        # stop
        # ponderhit
        # quit


class XBoardAgent():
    def __init__(self, name):
        self.name = name
        self.variant = 'standard'
        self.fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.board = chess.Board()
        self.statistics = self.init_statistics()

    def init_statistics(self):
        statistics = dict()
        statistics["total states"] = 0
        statistics["branching"] = 0
        statistics["average states per move"] = 0.0
        statistics["average eval function time"] = 0.0
        statistics["total eval function count"] = 0

        statistics["states"] = 0
        statistics["current branching"] = 0
        statistics["current move"] = 0
        statistics["eval function time"] = 0.0
        statistics["eval function count"] = 0
        return statistics

    def reset_single_move_statistics(self):
        self.statistics["states"] = 0
        self.statistics["current branching"] = 0
        self.statistics["current move"] = self.statistics["current move"] + 1
        self.statistics["eval function time"] = 0.0
        self.statistics["eval function count"] = 0

    def update_statistics(self):
        # self.statistics["current branching"] = self.statistics["states"] ** (1.0 / self.max_depth)

        self.statistics["total states"] = self.statistics["total states"] + self.statistics["states"]
        self.statistics["average states per move"] = self.statistics["total states"] / self.statistics["current move"]
        self.statistics["branching"] = max(self.statistics["current branching"], self.statistics["branching"])
        new_eval_count = self.statistics["total eval function count"] + self.statistics["eval function count"]
        self.statistics["average eval function time"] = \
            (self.statistics["average eval function time"] * self.statistics["total eval function count"] +
                self.statistics["eval function time"]) / new_eval_count
        self.statistics["total eval function count"] = new_eval_count

    def log_statistics(self):
        print("logging")
        f = open(".\\" + self.name + "_" + str(self.statistics["current move"]))
        f.write("Total States for game: " + str(self.statistics["total states"]) + "\n")
        f.write("Max branching factor for game: " + str(self.statistics["branching"]) + "\n")
        f.write("Average states per move for game: " + str(self.statistics["average states per move"]) + "\n")
        f.write("Average eval function execution time for game: " +
                str(self.statistics["average eval function time"]) + "\n")
        f.write("Eval function execution count: " + str(self.statistics["total eval function count"]) + "\n")
        f.write("States for current turn: " + str(self.statistics["states"]) + "\n")
        f.write("Branching factor for current turn: " + str(self.statistics["branching"]) + "\n")
        f.write("Current turn eval function time: " + str(self.statistics["eval function time"]) + "\n")
        f.write("Current turn eval function time: " + str(self.statistics["eval function count"]) + "\n")
        cur_turn_avg_eval = self.statistics["eval function time"] / self.statistics["eval function count"]
        f.write("Current turn eval function average time: " + str(cur_turn_avg_eval) + "\n")
        f.close()

    def cutoff(self, board, depth):
        if depth > 3:
            return True
        else:
            return False

    def minimax(self, board, depth, alpha, beta):
        self.statistics["states"] += 1
        if self.cutoff(board, depth):
            t = time.time()
            eval_result = utility.basic_material_eval(board, board.turn)
            self.statistics["eval function time"] += time.time() - t
            self.statistics["eval function count"] += 1
            return eval_result, None

        else:
            moves = board.generate_legal_moves()
            # self.statistics["current branching"] = max(self.statistics["current branching"], len(moves))
            val = float('-Inf')
            best_move = None
            for move in moves:
                board.push(move)
                possible = self.maximin(board, depth + 1, alpha, beta)[0]
                if possible > val:
                    val = possible
                    best_move = move

                alpha = max(alpha, val)
                if val >= beta:
                    break

                board.pop()

            return val, best_move

    def maximin(self, board, depth, alpha, beta):
        self.statistics["states"] += 1
        if self.cutoff(board, depth):
            t = time.time()
            eval_result = utility.basic_material_eval(board, board.turn)
            self.statistics["eval function time"] += time.time() - t
            self.statistics["eval function count"] += 1
            return eval_result, None

        else:
            moves = board.generate_legal_moves()
            # self.statistics["current branching"] = max(self.statistics["current branching"], len(moves))
            val = float('Inf')
            best_move = None
            for move in moves:
                board.push(move)
                possible = self.minimax(board, depth + 1, alpha, beta)[0]
                if possible < val:
                    val = possible
                    best_move = move

                beta = min(beta, val)
                if val <= alpha:
                    break

                board.pop()

            return val, best_move

    @staticmethod
    def getFen(variant):
        if variant == 'standard':
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        elif variant == 'bughouse':
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1 | rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1"

    @staticmethod
    def logAndPrint(msg, logfile):
        logfile.write(msg + '\n')
        print(msg, file=sys.stdout)

    def parse_commands(self):
        # print(3)
        filename = "mylog.txt"
        with open(filename, 'w') as mylog:
            while True:
                cmd = input()
                mylog.write(cmd + '\n')
                if cmd == 'xboard':
                    pass

                elif cmd[:8] == 'protover':
                    XBoardAgent.logAndPrint('feature myname="Liam"', mylog)
                    XBoardAgent.logAndPrint('feature ping=1', mylog)
                    XBoardAgent.logAndPrint('feature setboard=1', mylog)
                    #XBoardAgent.logAndPrint('feature san=1', mylog)

                elif cmd[:4] == 'ping':
                    XBoardAgent.logAndPrint('pong' + cmd[4:], mylog)

                elif cmd[:7] == 'variant':
                    self.variant = cmd[8:]
                    self.fen = XBoardAgent.getFen(self.variant)

                # elif cmd[:8] == 'usermove':
                #     self.board.push(cmd[9:], )

                elif cmd == 'go':
                    # print('hi')
                    self.reset_single_move_statistics()
                    move = self.minimax(self.board, 0, float('-Inf'), float('Inf'))[1]
                    self.board.push(move)
                    #self.board.push_san(move, myengine.get_board())
                    XBoardAgent.logAndPrint('move ' + move.__str__(), mylog)
                    self.update_statistics()
                    self.log_statistics()

                    #XBoardAgent.logAndPrint('move e2e4', mylog)


class DualAgent(XBoardAgent):
    """
    This is an agent that chooses the next move randomly.
    """

    """
    Potentially implement a custom cutoff function at some point. For now,
    simply cutoff if a certain hard-coded depth is reached.
    """

    pass


"""
If we run this file, the __name__ becomes "__main__", and so this portion of 
code will run. This is useful for running an agent.

This bit of code might need to be abstracted to a different spot, but I am 
just messing around for the moment.

https://docs.python.org/3.7/tutorial/modules.html#executing-modules-as-scripts
"""
if __name__ == "__main__":
    # print(2)
    dual_agent = DualAgent("dual_agent")
    dual_agent.parse_commands()
    # agent
