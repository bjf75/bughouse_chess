
# Bryce's import
from pychess import chess as chess
from pychess.chess import variant
import random
# import __init__ as chess
# import variant

from typing import ClassVar, Callable, Dict, Generic, Hashable, Iterable, Iterator, List, Mapping, MutableSet, Optional, SupportsInt, Tuple, Type, TypeVar, Union
import random

PAWN_VAL = 100
KNIGHT_VAL = 320
BISHOP_VAL = 325
ROOK_VAL = 500
QUEEN_VAL = 975
KING_VAL = 32767

MOBILITY_WEIGHT = 2

PAWN_TABLE_W = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -25, -25, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 25, 25, 0, 0, 0,
    5, 5, 10, 27, 27, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0
]
# are the black values correct?
PAWN_TABLE_B = [
    0, 0, 0, 0, 0, 0, 0, 0,
    -50, -50, -50, -50, -50, -50, -50, -50,
    -10, -10, -20, -30, -30, -20, -10, -10,
    -5, -5, -10, -27, -27, -10, -5, -5,
    0, 0, 0, -25, -25, 0, 0, 0,
    -5, 5, 10, 0, 0, 10, 5, -5,
    -5, -10, -10, 25, 25, -10, -10, -5,
    0, 0, 0, 0, 0, 0, 0, 0
]

# PAWN_TABLE_B = [x * -1 for x in PAWN_TABLE_W]

KNIGHT_TABLE_W = [
    -50, -40, -20, -30, -30, -20, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]
# are the black values correct?
# KNIGHT_TABLE_B = [x * -1 for x in KNIGHT_TABLE_W]
KNIGHT_TABLE_B = [
    50, 40, 30, 30, 30, 30, 40, 50,
    40, 20, 0, 0, 0, 0, 20, 40,
    30, 0, -10, -15, -15, -10, 0, 30,
    30, -5, -15, -20, -20, -15, -5, 30,
    30, 0, -15, -20, -20, -15, 0, 30,
    30, -5, -10, -15, -15, -10, -5, 30,
    40, 20, 0, -5, -5, 0, 20, 40,
    50, 40, 20, 30, 30, 20, 40, 50
]
BISHOP_TABLE_W = [
    -20, -10, -40, -10, -10, -40, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]
# are the black values correct?
# BISHOP_TABLE_B = [x * -1 for x in BISHOP_TABLE_W]
BISHOP_TABLE_B = [
    20, 10, 10, 10, 10, 10, 10, 20,
    10, 0, 0, 0, 0, 0, 0, 10,
    10, 0, -5, -10, -10, -5, 0, 10,
    10, -5, -5, -10, -10, -5, -5, 10,
    10, 0, -10, -10, -10, -10, 0, 10,
    10, -10, -10, -10, -10, -10, -10, 10,
    10, -5, 0, 0, 0, 0, -5, 10,
    20, 10, 40, 10, 10, 40, 10, 20
]
KING_TABLE_W = [
    20, 30, 10, 0, 0, 10, 30, 20,
    20, 20, 0, 0, 0, 0, 20, 20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30
]
# are the black values correct?
# KING_TABLE_B = [x * -1 for x in KING_TABLE_W]
KING_TABLE_B = [
    30, 40, 40, 50, 50, 40, 40, 30,
    30, 40, 40, 50, 50, 40, 40, 30,
    30, 40, 40, 50, 50, 40, 40, 30,
    30, 40, 40, 50, 50, 40, 40, 30,
    20, 30, 30, 40, 40, 30, 30, 20,
    10, 20, 20, 20, 20, 20, 20, 10,
    -20, -30, 0, 0, 0, 0, -30, -20,
    -20, -30, -10, 0, 0, -10, -30, -20,
]

# PAWN_TABLE_W_DIFF = [
#     0.01,  0.03,   0.05, 0.04, 0.06, 0.04, 0.02, 0,
#     5.01,  10.01,  10.02, -25, -25, 10.03, 10.04, 5.07,
#     5.02,  -5.01,  -10.02, 0.011, 0.012, -10.01, -5.02, 5.07,
#     0.07,  0.08,   0.09, 25, 25, -0.09, -0.08, -0.07,
#     5.03,  5.04,   9.96, 27, 27, 9.95, 5.05, 5.06,
#     10.05, 9.97, 20, 30, 30, 20, 9.99, 9.98,
#     50, 50, 50, 50, 50, 50, 50, 50,
#     -0.01, -0.03, -0.05, -0.04, -0.06, -0.04, -0.02, -0.015
# ]

PAWN_TABLE_W_DIFF = [sum(i) for i in zip(PAWN_TABLE_W, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

PAWN_TABLE_B_DIFF = [sum(i) for i in zip(PAWN_TABLE_B, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

KNIGHT_TABLE_W_DIFF = [sum(i) for i in zip(KNIGHT_TABLE_W, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

KNIGHT_TABLE_B_DIFF = [sum(i) for i in zip(KNIGHT_TABLE_B, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

BISHOP_TABLE_W_DIFF = [sum(i) for i in zip(BISHOP_TABLE_W, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

BISHOP_TABLE_B_DIFF = [sum(i) for i in zip(BISHOP_TABLE_B, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

KING_TABLE_W_DIFF = [sum(i) for i in zip(KING_TABLE_W, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]

KING_TABLE_B_DIFF = [sum(i) for i in zip(KING_TABLE_B, [random.uniform(-0.1, 0.1) for _ in range(0, 64)])]


def basic_material_eval_bughouse_base(board: variant.BughouseBaseBoardT, player: chess.Color,
                                      ally_diff_pocket=None,
                                      enemy_diff_pocket=None, to_protect=None, to_capture=None
                                      ) -> float:
    """
    @returns the float value of the material score for player in state
    """
    val = 0
    bo = board.occupied_co[chess.BLACK]
    wo = board.occupied_co[chess.WHITE]

    for p, v in [(board.pawns, PAWN_VAL), (board.knights, KNIGHT_VAL),
              (board.bishops, BISHOP_VAL), (board.rooks, ROOK_VAL),
              (board.queens, QUEEN_VAL), (board.kings, KING_VAL)]:
        val += chess.new_popcount(wo & p) * v
        val -= chess.new_popcount(bo & p) * v

    return float(val)


def basic_material_eval(board, player,
                        ally_diff_pocket=None,
                        enemy_diff_pocket=None, to_protect=None, to_capture=None
                        ):
    val = 0
    bo = board.occupied_co[chess.BLACK]
    wo = board.occupied_co[chess.WHITE]

    for p, v in [(board.pawns, PAWN_VAL), (board.knights, KNIGHT_VAL),
              (board.bishops, BISHOP_VAL), (board.rooks, ROOK_VAL),
              (board.queens, QUEEN_VAL), (board.kings, KING_VAL)]:
        val += chess.new_popcount(wo & p) * v
        val -= chess.new_popcount(bo & p) * v

    return float(val)

"""
Here we can put information regarding whatever with respect to evaluation.

According to https://www.chessprogramming.org/Move_Ordering there are different ways to
push for optimized move ordering when evaluating with minimax search.

"""
# from pychess import chess as chess

class UtilityEvalSuper(Generic[chess.BoardT]):
    """
    This is a super class for utility evaluation of chess board states; more
    specifically, for Bughouse chess. 

    Basing material evaluation (at least for now) off of this recommendation:
    https://www.adamberent.com/2019/03/02/chess-board-evaluation/
    Pawn: 100
    Knight: 320
    Bishop: 325
    Rook: 500
    Queen: 975
    King: 32767

    In that blog post, he uses negative values for black and positive values for 
    white. This will probably be the best, but I'm not sure.
    """
    PAWN_VAL = 100
    KNIGHT_VAL = 320
    BISHOP_VAL = 325
    ROOK_VAL = 500
    QUEEN_VAL = 975
    KING_VAL = 32767

    @classmethod
    def utility(cls, board: variant.BughouseSuperBoardT, board_id: str, players_eval: dict,
                ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                to_protect=None, to_capture=None) -> dict:
        """
        utility() is a method devoted to providing a numerical score
        for a player and their opponent (or, optionally, only one) for 
        a given board state. Ideally, this will defer to a chosen evaluation
        class or evaluation method for the given board, but evaluation
        can be implemented in the method itself.

        The default action (for this superclass method) is to run the 
        utility() method in the self.eval_class and return what it returns. 
        This may be overridden.

        params: 
            - @board: a Board to evaluate the current state of
            - @players_eval: a dict with keys representing which which colors to evaluate

        @returns: a new dict with keys being the color and values being floating
        point scores for each respective color (does not modify the dict given).

        TODO: So, we definitely need to consider how to structure a utility evaluation
        function. Most importantly, it should be constant time so as to reduce the 
        performance overhead of evaluating a state (we have plenty of overhead as 
        it is; we don't need any more). One thing that could be very, very useful
        for evaluation is pinning https://en.wikipedia.org/wiki/Pin_(chess). There
        are already methods that have been created to evaluate whether pinning exists
        within chess.BaseBoard. 
        """

        ret = players_eval.copy() # shallow copy is safe, because it should only be two keys
        for player in ret:
            if type(cls) == type(BasicPlusPositionEvalBughouseBase):
                ret[player] = cls._utility(board.get_base_board(board_id), player,
                                           ally_diff_pocket=ally_diff_pocket, enemy_diff_pocket=enemy_diff_pocket,
                                           to_protect=to_protect, to_capture=to_capture)
            else:
                ret[player] = cls._utility(board.get_base_board(board_id), player)
        return ret 

    @classmethod
    def _utility(cls, board: chess.BoardT, player: chess.Color, ally_diff_pocket: variant.BughousePocketT = None,
                 enemy_diff_pocket: variant.BughousePocketT = None, to_protect=None, to_capture=None):
        """
        The _utility helper method. Should be implemented by sub-classes. 
        For this super class method, returns 1 if player is not in checkmate, 
        0 if in checkmate.

        @params:
            - board: the board to evaluate the current state of
            - player: the player to evaluate the state for
        
        @params

        What sub-classes should implement:

        """
        # return cls._utility(board, player)
        raise NotImplementedError
        
    @classmethod
    def basic_material_eval_bughouse_base(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                                          ally_diff_pocket=None, enemy_diff_pocket=None, to_protect=None,
                                          to_capture=None) -> int:
        """
        @returns the float value of the material score for player in state
        """
        val = 0
        bo = board.occupied_co[chess.BLACK]
        wo = board.occupied_co[chess.WHITE]

        # TODO: I'm not sure that this is quite right
        for p, v in [(board.pawns, cls.PAWN_VAL), (board.knights, cls.KNIGHT_VAL), 
                (board.bishops, cls.BISHOP_VAL), (board.rooks, cls.ROOK_VAL), 
                (board.queens, cls.QUEEN_VAL), (board.kings, cls.KING_VAL)]:
            val += chess.new_popcount(wo & p) * v
            val -= chess.new_popcount(bo & p) * v

        return val

    @classmethod
    def basic_material_eval_bughouse_super(cls, board: variant.BughouseSuperBoardT, player,
                                           ally_diff_pocket=None,
                                           enemy_diff_pocket=None, to_protect=None, to_capture=None
                                           ) -> int:
        """
        TODO: I'm not sure how to deal with players from the super board yet.
        """
        raise NotImplementedError

    
class BasicMaterialEvaluationBughouseBase(UtilityEvalSuper):
    """
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass.
    """
    
    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color, ally_diff_pocket=None,
                 enemy_diff_pocket=None, to_protect=None, to_capture=None) -> float:
        return float(cls.basic_material_eval_bughouse_base(board, player))


class BasicPlusPositionEvalBughouseBase(UtilityEvalSuper):
    """ 
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass, as well 
    as adds piece position evaluation for all pawns, knights, bishops, and kings 
    according to the guidance for orthodox chess laid out at 
        https://www.adamberent.com/2019/03/02/piece-square-table/

    TODO: So, as I understand it, the examples that these tables are based on have rank 1 
    at what we perceive as the 'bottom' of the array. This is in contrast to the chess
    module where rank 1 is the 'top' of the array. Thus, I am flipping them to try and
    correct for this in our evaluations. If I am wrong and the originals are what we need,
    they can be found at commit 6e17861
    """

    use_diff_positions = False
    
    @classmethod
    def set_diff_positions(cls, val):
        cls.use_diff_positions = val

    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                 ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                 to_protect=None, to_capture=None) -> float:
        val = cls.basic_material_eval_bughouse_base(board, player)
        if player: # player is white
            wo = board.occupied_co[chess.WHITE]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & wo:
                    if bb_sq & board.pawns:
                        if cls.use_diff_positions:
                            val += PAWN_TABLE_W_DIFF[sq]
                        else:
                            val += PAWN_TABLE_W[sq]
                    elif bb_sq & board.knights:
                        if cls.use_diff_positions:
                            val += KNIGHT_TABLE_W_DIFF[sq]
                        else:
                            val += KNIGHT_TABLE_W[sq]
                    elif bb_sq & board.bishops:
                        if cls.use_diff_positions:
                            val += BISHOP_TABLE_W_DIFF[sq]
                        else:
                            val += BISHOP_TABLE_W[sq]
                    elif bb_sq & board.kings:
                        if cls.use_diff_positions:
                            val += cls.KING_TABLE_W_DIFF[sq]
                        else:
                            val += KING_TABLE_W[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                # enemy_num = 0
                # ally_num = 0
                # for p, v in ally_diff_pocket.pieces.items():
                #     if v > 0:
                #         ally_num = ally_num + 1
                # for p, v in enemy_diff_pocket.pieces.items():
                #     if v > 0:
                #         enemy_num = enemy_num + 1
                # if enemy_num > 0 or ally_num > 0:
                #     print("yes")

                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)
        else: # player is black
            bo = board.occupied_co[chess.BLACK]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & bo:
                    if bb_sq & board.pawns:
                        if cls.use_diff_positions:
                            val += PAWN_TABLE_B_DIFF[sq]
                        else:
                            val += PAWN_TABLE_B[sq]
                    elif bb_sq & board.knights:
                        if cls.use_diff_positions:
                            val += KNIGHT_TABLE_B_DIFF
                        else:
                            val += KNIGHT_TABLE_B[sq]
                    elif bb_sq & board.bishops:
                        if cls.use_diff_positions:
                            val += BISHOP_TABLE_B_DIFF
                        else:
                            val += BISHOP_TABLE_B[sq]
                    elif bb_sq & board.kings:
                        if cls.use_diff_positions:
                            val += KING_TABLE_B_DIFF
                        else:
                            val += KING_TABLE_B[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                # enemy_num = 0
                # ally_num = 0
                # for p, v in ally_diff_pocket.pieces.items():
                #     if v > 0:
                #         ally_num = ally_num + 1
                # for p, v in enemy_diff_pocket.pieces.items():
                #     if v > 0:
                #         enemy_num = enemy_num + 1
                # if enemy_num > 0 or ally_num > 0:
                #     print("yes")

                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)


class BasicPlusPositionEvalBughouseBase_Copy(UtilityEvalSuper):
    """
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass, as well
    as adds piece position evaluation for all pawns, knights, bishops, and kings
    according to the guidance for orthodox chess laid out at
        https://www.adamberent.com/2019/03/02/piece-square-table/

    TODO: So, as I understand it, the examples that these tables are based on have rank 1
    at what we perceive as the 'bottom' of the array. This is in contrast to the chess
    module where rank 1 is the 'top' of the array. Thus, I am flipping them to try and
    correct for this in our evaluations. If I am wrong and the originals are what we need,
    they can be found at commit 6e17861
    """

    use_diff_positions = False

    @classmethod
    def set_diff_positions(cls, val):
        cls.use_diff_positions = val

    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                 ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                 to_protect=None, to_capture=None) -> float:
        val = cls.basic_material_eval_bughouse_base(board, player)
        if player:  # player is white
            wo = board.occupied_co[chess.WHITE]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & wo:
                    if bb_sq & board.pawns:
                        if cls.use_diff_positions:
                            val += PAWN_TABLE_W_DIFF[sq]
                        else:
                            val += PAWN_TABLE_W[sq]
                    elif bb_sq & board.knights:
                        if cls.use_diff_positions:
                            val += KNIGHT_TABLE_W_DIFF[sq]
                        else:
                            val += KNIGHT_TABLE_W[sq]
                    elif bb_sq & board.bishops:
                        if cls.use_diff_positions:
                            val += BISHOP_TABLE_W_DIFF[sq]
                        else:
                            val += BISHOP_TABLE_W[sq]
                    elif bb_sq & board.kings:
                        if cls.use_diff_positions:
                            val += KING_TABLE_W_DIFF[sq]
                        else:
                            val += KING_TABLE_W[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                # enemy_num = 0
                # ally_num = 0
                # for p, v in ally_diff_pocket.pieces.items():
                #     if v > 0:
                #         ally_num = ally_num + 1
                # for p, v in enemy_diff_pocket.pieces.items():
                #     if v > 0:
                #         enemy_num = enemy_num + 1
                # if enemy_num > 0 or ally_num > 0:
                #     print("yes")

                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)
        else:  # player is black
            bo = board.occupied_co[chess.BLACK]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & bo:
                    if bb_sq & board.pawns:
                        if cls.use_diff_positions:
                            val += PAWN_TABLE_B_DIFF[sq]
                        else:
                            val += PAWN_TABLE_B[sq]
                    elif bb_sq & board.knights:
                        if cls.use_diff_positions:
                            val += KNIGHT_TABLE_B_DIFF
                        else:
                            val += KNIGHT_TABLE_B[sq]
                    elif bb_sq & board.bishops:
                        if cls.use_diff_positions:
                            val += BISHOP_TABLE_B_DIFF
                        else:
                            val += BISHOP_TABLE_B[sq]
                    elif bb_sq & board.kings:
                        if cls.use_diff_positions:
                            val += KING_TABLE_B_DIFF
                        else:
                            val += KING_TABLE_B[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                # enemy_num = 0
                # ally_num = 0
                # for p, v in ally_diff_pocket.pieces.items():
                #     if v > 0:
                #         ally_num = ally_num + 1
                # for p, v in enemy_diff_pocket.pieces.items():
                #     if v > 0:
                #         enemy_num = enemy_num + 1
                # if enemy_num > 0 or ally_num > 0:
                #     print("yes")

                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)


class BasicPlusPositionPlusPocketValEvalBughouseBase(UtilityEvalSuper):
    """
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass, as well
    as adds piece position evaluation for all pawns, knights, bishops, and kings
    according to the guidance for orthodox chess laid out at
        https://www.adamberent.com/2019/03/02/piece-square-table/

    TODO: So, as I understand it, the examples that these tables are based on have rank 1
    at what we perceive as the 'bottom' of the array. This is in contrast to the chess
    module where rank 1 is the 'top' of the array. Thus, I am flipping them to try and
    correct for this in our evaluations. If I am wrong and the originals are what we need,
    they can be found at commit 6e17861
    """

    use_diff_positions = False
    pocket_val = 0.5

    @classmethod
    def set_diff_positions(cls, val):
        cls.use_diff_positions = val

    @classmethod
    def set_pocket_val(cls, val):
        cls.pocket_val = val

    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                 ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                 to_protect=None, to_capture=None) -> float:
        val = cls.basic_material_eval_bughouse_base(board, player)
        # Subtract dropped pieces from material val to decentivize instant drops
        self_pocket = board.get_pocket(player)
        if player:  # player is white
            wo = board.occupied_co[chess.WHITE]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & wo:
                    if bb_sq & board.pawns:
                        if cls.use_diff_positions:
                            val += PAWN_TABLE_W_DIFF[sq]
                        else:
                            val += PAWN_TABLE_W[sq]
                    elif bb_sq & board.knights:
                        if cls.use_diff_positions:
                            val += KNIGHT_TABLE_W_DIFF[sq]
                        else:
                            val += KNIGHT_TABLE_W[sq]
                    elif bb_sq & board.bishops:
                        if cls.use_diff_positions:
                            val += BISHOP_TABLE_W_DIFF[sq]
                        else:
                            val += BISHOP_TABLE_W[sq]
                    elif bb_sq & board.kings:
                        if cls.use_diff_positions:
                            val += cls.KING_TABLE_W_DIFF[sq]
                        else:
                            val += KING_TABLE_W[sq]
            if self_pocket is not None:
                for p, v in self_pocket.pieces.items():
                    if p == chess.KING:
                        val += v * KING_VAL * cls.pocket_val
                    elif p == chess.QUEEN:
                        val += v * QUEEN_VAL * cls.pocket_val
                    elif p == chess.ROOK:
                        val += v * ROOK_VAL * cls.pocket_val
                    elif p == chess.BISHOP:
                        val += v * BISHOP_VAL * cls.pocket_val
                    elif p == chess.KNIGHT:
                        val += v * KNIGHT_VAL * cls.pocket_val
                    else:  # p == chess.PAWN
                        val += v * PAWN_VAL * cls.pocket_val
            if ally_diff_pocket is None:
                return float(val)
            else:
                # enemy_num = 0
                # ally_num = 0
                # for p, v in ally_diff_pocket.pieces.items():
                #     if v > 0:
                #         ally_num = ally_num + 1
                # for p, v in enemy_diff_pocket.pieces.items():
                #     if v > 0:
                #         enemy_num = enemy_num + 1
                # if enemy_num > 0 or ally_num > 0:
                #     print("yes")

                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val -= v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)
        else:  # player is black
            bo = board.occupied_co[chess.BLACK]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & board.pawns:
                    if cls.use_diff_positions:
                        val += PAWN_TABLE_B_DIFF[sq]
                    else:
                        val += PAWN_TABLE_B[sq]
                elif bb_sq & board.knights:
                    if cls.use_diff_positions:
                        val += KNIGHT_TABLE_B_DIFF
                    else:
                        val += KNIGHT_TABLE_B[sq]
                elif bb_sq & board.bishops:
                    if cls.use_diff_positions:
                        val += BISHOP_TABLE_B_DIFF
                    else:
                        val += BISHOP_TABLE_B[sq]
                elif bb_sq & board.kings:
                    if cls.use_diff_positions:
                        val += KING_TABLE_B_DIFF
                    else:
                        val += KING_TABLE_B[sq]
            if self_pocket is not None:
                for p, v in self_pocket.pieces.items():
                    if p == chess.KING:
                        val -= v * KING_VAL * cls.pocket_val
                    elif p == chess.QUEEN:
                        val -= v * QUEEN_VAL * cls.pocket_val
                    elif p == chess.ROOK:
                        val -= v * ROOK_VAL * cls.pocket_val
                    elif p == chess.BISHOP:
                        val -= v * BISHOP_VAL * cls.pocket_val
                    elif p == chess.KNIGHT:
                        val -= v * KNIGHT_VAL * cls.pocket_val
                    else:  # p == chess.PAWN
                        val -= v * PAWN_VAL * cls.pocket_val
            if ally_diff_pocket is None:
                return float(val)
            else:
                # enemy_num = 0
                # ally_num = 0
                # for p, v in ally_diff_pocket.pieces.items():
                #     if v > 0:
                #         ally_num = ally_num + 1
                # for p, v in enemy_diff_pocket.pieces.items():
                #     if v > 0:
                #         enemy_num = enemy_num + 1
                # if enemy_num > 0 or ally_num > 0:
                #     print("yes")

                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val -= v
                return float(val)


class BasicPlusMobilityEvalBughouseBase(UtilityEvalSuper):
    """
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass, as well
    as adds a factor corresponding to the number of legal moves the board has
    """
    pocket_val = 0.5

    # pocket_val = 1, for the BasicPlusMobilityEvalBughouseBase_copy class that 
    # Bryce removed 

    @classmethod
    def set_pocket_val(cls, val):
        cls.pocket_val = val

    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                 ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                 to_protect=None, to_capture=None) -> float:
        val = cls.basic_material_eval_bughouse_base(board, player)

        # Subtract dropped pieces from material val to decentivize instant drops
        self_pocket = board.get_pocket(player)
        original_turn = board.turn
        board.turn = player
        if player: # player is white
            mobility = 0
            for move in board.generate_legal_moves():
                if not move.drop:
                    mobility += 1

            val += mobility * MOBILITY_WEIGHT
            board.turn = original_turn

            if self_pocket is not None:
                for p, v in self_pocket.pieces.items():
                    if p == chess.KING:
                        val += v * KING_VAL * cls.pocket_val
                    elif p == chess.QUEEN:
                        val += v * QUEEN_VAL * cls.pocket_val
                    elif p == chess.ROOK:
                        val += v * ROOK_VAL * cls.pocket_val
                    elif p == chess.BISHOP:
                        val += v * BISHOP_VAL * cls.pocket_val
                    elif p == chess.KNIGHT:
                        val += v * KNIGHT_VAL * cls.pocket_val
                    else:  # p == chess.PAWN
                        val += v * PAWN_VAL * cls.pocket_val
            if ally_diff_pocket is None:
                return float(val)
            else:
                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val -= v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)
        else: # player is black
            mobility = 0
            for move in board.generate_legal_moves():
                if not move.drop:
                    mobility += 1

            val -= mobility * MOBILITY_WEIGHT
            board.turn = original_turn

            if self_pocket is not None:
                for p, v in self_pocket.pieces.items():
                    if p == chess.KING:
                        val -= v * KING_VAL * cls.pocket_val
                    elif p == chess.QUEEN:
                        val -= v * QUEEN_VAL * cls.pocket_val
                    elif p == chess.ROOK:
                        val -= v * ROOK_VAL * cls.pocket_val
                    elif p == chess.BISHOP:
                        val -= v * BISHOP_VAL * cls.pocket_val
                    elif p == chess.KNIGHT:
                        val -= v * KNIGHT_VAL * cls.pocket_val
                    else:  # p == chess.PAWN
                        val -= v * PAWN_VAL * cls.pocket_val
            if ally_diff_pocket is None:
                return float(val)
            else:
                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val -= v
                return float(val)


class BasicPlusPositionPlusMobilityEvalBughouseBase(UtilityEvalSuper):
    """
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass, as well
    as adds piece position evaluation for all pawns, knights, bishops, and kings
    according to the guidance for orthodox chess laid out at
        https://www.adamberent.com/2019/03/02/piece-square-table/

    TODO: So, as I understand it, the examples that these tables are based on have rank 1
    at what we perceive as the 'bottom' of the array. This is in contrast to the chess
    module where rank 1 is the 'top' of the array. Thus, I am flipping them to try and
    correct for this in our evaluations. If I am wrong and the originals are what we need,
    they can be found at commit 6e17861
    """

    use_diff_positions = False

    @classmethod
    def set_diff_positions(cls, val):
        cls.use_diff_positions = val

    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                 ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                 to_protect=None, to_capture=None) -> float:
        val = cls.basic_material_eval_bughouse_base(board, player)
        original_turn = board.turn
        board.turn = player
        if player: # player is white
            mobility = 0
            for move in board.generate_legal_moves():
                if not move.drop:
                    mobility += 1

            val += mobility * MOBILITY_WEIGHT
            board.turn = original_turn

            wo = board.occupied_co[chess.WHITE]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & wo:
                    if bb_sq & board.pawns:
                        if cls.use_diff_positions:
                            val += PAWN_TABLE_W_DIFF[sq]
                        else:
                            val += PAWN_TABLE_W[sq]
                    elif bb_sq & board.knights:
                        if cls.use_diff_positions:
                            val += KNIGHT_TABLE_W_DIFF[sq]
                        else:
                            val += KNIGHT_TABLE_W[sq]
                    elif bb_sq & board.bishops:
                        if cls.use_diff_positions:
                            val += BISHOP_TABLE_W_DIFF[sq]
                        else:
                            val += BISHOP_TABLE_W[sq]
                    elif bb_sq & board.kings:
                        if cls.use_diff_positions:
                            val += KING_TABLE_W_DIFF[sq]
                        else:
                            val += KING_TABLE_W[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val -= v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += v
                return float(val)
        else: # player is black
            mobility = 0
            for move in board.generate_legal_moves():
                if not move.drop:
                    mobility += 1

            val -= mobility * MOBILITY_WEIGHT
            board.turn = original_turn

            bo = board.occupied_co[chess.BLACK]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & board.pawns:
                    if cls.use_diff_positions:
                        val += PAWN_TABLE_B_DIFF[sq]
                    else:
                        val += PAWN_TABLE_B[sq]
                elif bb_sq & board.knights:
                    if cls.use_diff_positions:
                        val += KNIGHT_TABLE_B_DIFF
                    else:
                        val += KNIGHT_TABLE_B[sq]
                elif bb_sq & board.bishops:
                    if cls.use_diff_positions:
                        val += BISHOP_TABLE_B_DIFF
                    else:
                        val += BISHOP_TABLE_B[sq]
                elif bb_sq & board.kings:
                    if cls.use_diff_positions:
                        val += KING_TABLE_B_DIFF
                    else:
                        val += KING_TABLE_B[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val -= v
                return float(val)


class BasicPlusPositionPlusMobilityEvalBughouseBaseBeale(UtilityEvalSuper):
    """
    This class evaluates an instance of a _BughouseBaseBoardState for the defined player
    according to the rules for material evaluation defined in the superclass, as well
    as adds piece position evaluation for all pawns, knights, bishops, and kings
    according to the guidance for orthodox chess laid out at
        https://www.adamberent.com/2019/03/02/piece-square-table/

    TODO: So, as I understand it, the examples that these tables are based on have rank 1
    at what we perceive as the 'bottom' of the array. This is in contrast to the chess
    module where rank 1 is the 'top' of the array. Thus, I am flipping them to try and
    correct for this in our evaluations. If I am wrong and the originals are what we need,
    they can be found at commit 6e17861
    """
    PAWN_TABLE_W = [random.randint(-50, 50) for i in range(0,64)]
    # are the black values correct?
    PAWN_TABLE_B = [random.randint(-50, 50) for i in range(0,64)]

    # PAWN_TABLE_B = [x * -1 for x in PAWN_TABLE_W]

    KNIGHT_TABLE_W = [random.randint(-50, 50) for i in range(0,64)]
    # are the black values correct?
    # KNIGHT_TABLE_B = [x * -1 for x in KNIGHT_TABLE_W]
    KNIGHT_TABLE_B = [random.randint(-50, 50) for i in range(0,64)]
    BISHOP_TABLE_W = [random.randint(-50, 50) for i in range(0,64)]
    # are the black values correct?
    # BISHOP_TABLE_B = [x * -1 for x in BISHOP_TABLE_W]
    BISHOP_TABLE_B = [random.randint(-50, 50) for i in range(0,64)]
    KING_TABLE_W = [random.randint(-50, 50) for i in range(0,64)]
    # are the black values correct?
    # KING_TABLE_B = [x * -1 for x in KING_TABLE_W]
    KING_TABLE_B = [random.randint(-50, 50) for i in range(0,64)]

    @classmethod
    def _utility(cls, board: variant.BughouseBaseBoardT, player: chess.Color,
                 ally_diff_pocket: variant.BughousePocketT = None, enemy_diff_pocket: variant.BughousePocketT = None,
                 to_protect=None, to_capture=None) -> float:
        val = cls.basic_material_eval_bughouse_base(board, player)
        occupied_turn = board.turn
        board.turn = player
        if player: # player is white
            mobility = 0
            for move in board.generate_legal_moves():
                if not move.drop:
                    mobility += 1

            val += mobility * MOBILITY_WEIGHT
            board.turn = occupied_turn
            wo = board.occupied_co[chess.WHITE]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & wo:
                    if bb_sq & board.pawns:
                        val += cls.PAWN_TABLE_W[sq]
                    elif bb_sq & board.knights:
                        val += cls.KNIGHT_TABLE_W[sq]
                    elif bb_sq & board.bishops:
                        val += cls.BISHOP_TABLE_W[sq]
                    elif bb_sq & board.kings:
                        val += cls.KING_TABLE_W[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val -= 2*v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val += 2*v
                return float(val)
        else: # player is black
            mobility = 0
            for move in board.generate_legal_moves():
                if not move.drop:
                    mobility += 1

            val -= mobility * MOBILITY_WEIGHT
            board.turn = occupied_turn
            bo = board.occupied_co[chess.BLACK]
            for sq in chess.SQUARES:
                bb_sq = chess.BB_SQUARES[sq]
                if bb_sq & bo:
                    if bb_sq & board.pawns:
                        val += cls.PAWN_TABLE_B[sq]
                    elif bb_sq & board.knights:
                        val += cls.KNIGHT_TABLE_B[sq]
                    elif bb_sq & board.bishops:
                        val += cls.BISHOP_TABLE_B[sq]
                    elif bb_sq & board.kings:
                        val += cls.KING_TABLE_B[sq]
            if ally_diff_pocket is None:
                return float(val)
            else:
                for p, v in to_protect.items():
                    # Failed to protect piece
                    if enemy_diff_pocket.pieces[p] > 0:
                        val += 2*v
                for p, v in to_capture.items():
                    # Succeeded in capturing piece
                    if ally_diff_pocket.pieces[p] > 0:
                        val -= 2*v
                return float(val)