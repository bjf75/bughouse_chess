import pychess
from pychess import chess as chess
from pychess.chess import variant as variant
from pychess.chess import ai as ai 
from pychess.chess.ai import CommChannel as CommChannel

import unittest
import logging

def test1():
    board = variant.BughouseBaseBoard('A', "rnbqkbnr/pppppppp/8/8/8/7N/PPPPPPPP/RNBQKB1R[] b KQkq - 0 2")
    moves = list()
    for mv in board.generate_legal_moves():
        moves.append(mv)
    print(moves)

def test2():
    super_board = variant.BughouseSuperBoard()
    super_board.push(chess.Move.from_uci("g1h3"), 'A')
    print(super_board.unicode_ext())
    moves = list()
    for mv in super_board.get_base_board('A').generate_legal_moves():
        moves.append(mv)
    print(moves)

def test3():
    """
    make these moves, follow what happens
    g1h3
    e7e5
    h3f4
    e5f4
    """
    super_board = variant.BughouseSuperBoard()
    moves = [
        "g1h3",
        "e7e5",
        "h3f4",
        "e5f4"
    ]
    for mv in moves:
        super_board.push(chess.Move.from_uci(mv), 'A')
        print(super_board.unicode_ext())

def test4():
    """
    make these moves, follow what happens
    g1h3
    e7e5
    h3f4
    e5f4
    """
    super_board = variant.BughouseSuperBoard()
    moves = [
        "g1h3",
        "e7e5",
        "h3f4",
        "e5f4"
    ]
    for mv in moves:
        super_board.push(chess.Move.from_uci(mv), 'A')
        print(super_board.unicode_ext())
    super_board.pop()
    print(super_board.unicode_ext())
    print(super_board.get_base_board('B').pockets)

def test5():
    """
    make these moves, follow what happens
    g1h3
    g7g5
    h3g5
    P@a3        
    """
    super_board = variant.BughouseSuperBoard()
    moves = [
        "g1h3",
        "g7g5",
        "h3g4",
        "P@a3"
    ]
    for mv in moves:
        super_board.push(chess.Move.from_uci(mv), 'A')
        print(super_board.unicode_ext(borders=True, labels=True))
    super_board.pop()
    print(super_board.unicode_ext())
    print(super_board.get_base_board('B').pockets)


def test6():
    """
    make these moves, follow what happens
    g1h3
    g7g5
    h3g5
    P@a3        
    """
    super_board = variant.BughouseSuperBoard()
    moves = [
        "g1h3",
        "g7g5",
        "h3g5"
    ]
    for mv in moves:
        super_board.push(chess.Move.from_uci(mv), 'A')
        print(super_board.unicode_ext(borders=True, labels=True))
        print("{} pockets {}".format('A', super_board.get_base_board('A').pockets))
        print("{} pockets {}".format('B', super_board.get_base_board('B').pockets))
    moves = []
    for mv in super_board.get_base_board('A').generate_legal_moves():
        moves.append(mv)
    print(moves)
    super_board.pop()
    # print(super_board.unicode_ext())
    print(super_board.get_base_board('B').pockets)


def test7():
    """
    make these moves, follow what happens
    g1h3 a
    b2b3 b
    a7a6 a
    g8h6 b
    h3g5 a
    b1c3 b
    b7b5 a
    h8g8 b
    g5h7 a
    a1b1 b
    f7f5 a
    """
    super_board = variant.BughouseSuperBoard()
    moves = [
        ("g1h3", 'A'),
        ("b2b3", 'B'),
        ("a7a6", 'A'),
        ("g8h6", 'B'),
        ("h3g5", 'A'),
        ("b1c3", 'B'),
        ("b7b5", 'A'),
        ("h8g8", 'B'),
        ("g5h7", 'A'),
        ("a1b1", 'B'),
        ("f7f5", 'A')
    ]
    for (mv,b) in moves:
        super_board.push(chess.Move.from_uci(mv), b)
        print(super_board.unicode_ext(borders=True, labels=True))
        print("{} pockets {}".format('A', super_board.get_base_board('A').pockets))
        print("{} pockets {}".format('B', super_board.get_base_board('B').pockets))
    moves = []
    for mv in super_board.get_base_board('B').generate_legal_moves():
        moves.append(mv)
    print(moves)
    eval_class = chess.utility.BasicMaterialEvaluationBughouseBase()
    blackB = ai.PartneredAI("blackB", super_board, chess.B, chess.BLACK, eval_class, False, max_depth=4)
    move = blackB.choose_move()
    super_board.push(move, 'B')
    # super_board.pop()
    # print(super_board.unicode_ext())
    print("{} pockets {}".format('A', super_board.get_base_board('A').pockets))
    print("{} pockets {}".format('B', super_board.get_base_board('B').pockets))

def test8():
    """
    make these moves, follow what happens
    g1h3 a
    b2b3 b
    a7a6 a
    g8h6 b
    h3g5 a
    b1c3 b
    b7b5 a
    h8g8 b
    g5h7 a
    a1b1 b
    f7f5 a
    """
    super_board = variant.BughouseSuperBoard()
    moves = [
        ("g1h3","A"),
        ("f2f3","B"),
        ("g8f6","A"),
        ("g8h6","B"),
        ("h3g5","A"),
        ("d2d3","B"),
        ("b7b5","A"),
        ("h8g8","B"),
        ("g5h7","A"),
        ("a2a4","B"),
        ("f6e4","A"),
        ("g8h8","B"),
        ("h7f8","A"),
        ("g1h3","B"),
        ("e8f8","A"),
        ("h8g8","B"),
        ("h1g1","A"),
        ("N@e5","B"),
        ("g7g5","A"),
        ("g8h8","B"),
        ("g1h1","A"),
        ("g2g3","B"),
        ("h8h7","A"),
        ("h8g8","B"),
        ("h1g1","A"),
        ("b2b3","B"),
        ("h7g7","A"),
        ("g8h8","B"),
        ("g1h1","A"),
        ("b1a3","B"),
        ("f8g8","A"),
        ("h8g8","B"),
        ("h1g1","A"),
        ("f1g2","B"),
        ("g8h7","A")
    ]
    for (mv,b) in moves:
        super_board.push(chess.Move.from_uci(mv), b)
        print(super_board.unicode_ext(borders=True, labels=True))
        print("{} pockets {}".format('A', super_board.get_base_board('A').pockets))
        print("{} pockets {}".format('B', super_board.get_base_board('B').pockets))
    moves = []
    for mv in super_board.get_base_board('B').generate_legal_moves():
        moves.append(mv)
    print(moves)
    eval_class = chess.utility.BasicMaterialEvaluationBughouseBase()
    blackB = ai.PartneredAI("blackB", super_board, chess.B, chess.BLACK, eval_class, False, max_depth=4)
    move = blackB.choose_move()
    super_board.push(move, 'B')
    # super_board.pop()
    # print(super_board.unicode_ext())
    print("{} pockets {}".format('A', super_board.get_base_board('A').pockets))
    print("{} pockets {}".format('B', super_board.get_base_board('B').pockets))


if __name__ == "__main__":
    # unittest.main()
    logging.basicConfig(filename="logs/fix-example-game-1.txt", level=logging.INFO)
    test8()
    