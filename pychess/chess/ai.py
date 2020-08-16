"""
This file contains a Bughouse AIs

"""

import math

from pychess import chess as chess
from pychess.chess import variant
from pychess.chess import utility as utility
from typing import ClassVar, Callable, Dict, Generic, Hashable, Iterable, Iterator, List, Mapping, MutableSet, Optional, SupportsInt, Tuple, Type, TypeVar, Union
import time
import multiprocessing as mp
import logging
import pickle
import random

# The default maximum allowed depth of search. May be overridden in
# a specific instance of an AI
MAX_DEPTH = 10


class CommChannel:
    """
    Objects of this class are to be used to communicate between partnered
    AIs the pieces they wish to see captured (to benefit themselves) as well as
    pieces they want protected... as well as the value or cost to them.

    This should be secured with a lock, as it is not thread-safe.

    self.please_capture: a dictionary of piece types with
    the value of their capture by the partner to the player.

    self.please_protect: a dictionary of piece types with the harm that
    would be done to the player if caught by the partner's opponent.
    """

    def __init__(self):
        self.please_capture = dict()
        self.please_protect = dict()

    def set_please_capture(self, pairs: dict):
        for key in pairs:
            if not key in chess.PIECE_TYPES:
                raise ValueError("The provided key is not a valid piece type.")

            self.please_capture[key] = pairs[key]

    def set_please_protect(self, pairs: dict):
        for key in pairs:
            if not key in chess.PIECE_TYPES:
                raise ValueError("The provided key is not a valid piece type.")
            self.please_protect[key] = pairs[key]

    def get_please_capture(self):
        return self.please_capture.copy()

    def get_please_protect(self):
        return self.please_protect.copy()


class AI:
    """
    The superclass of all AIs
    """

    def __init__(self, name: str, board: variant.BughouseSuperBoard, eval_class: utility.UtilityEvalSuper,
                 max_depth: int = MAX_DEPTH, print_stats: bool = False, log: bool = False, max_states: bool = 1000000,
                 iter_deep: bool = True, nxt_dep_func=None, move_order_fn=None, allow_fivefold_repetition=False):
        """
        :param name:
        :param max_depth:
        :param board:
        :param eval_class:
        :param statistics:
        :param log:
        :param max_states: default is 1000000; this is the number of states that
            causes iterative deepening to stop trying further depths
        :param iter_deep: default is True; if True, uses dynamic iterative deepening
            until an iteration has reached max_states or until it has reached max_depth,
            which ever comes first; if False, just goes until it has reached the max_depth
        :param nxt_dep_func: default is None; if this is None, the next depth for
            each call to minimax/maximin is the previous depth - 1; if it is not
            None, it must be an instance method (called with self.fun()). Currently, only
            the keyword argument 'move=mv', where mv is the move being considered,
            will be used as a parameter. This should be changed as new nxt_dep_func methods
            are made with different parameter requirements.
        :param move_order_fn: default is None; if this is None, the ordering of move evaluation
            is determined by the move generator; otherwise, if it is not None, it must be an
            instance method (called with self.fun()) that determines the ordering of move evaluation
        :param allow_fivefold_repetition: if you allow fivefold repetition, then a draw may occur from
            such case; otherwise, a move that would cause fivefold repetition is not allowed
            to be chosen, this may cause a losing move to be chosen
        """
        self.name = name
        self.max_depth = max_depth  # The maximum depth of search
        self.board = board
        self.eval_class = eval_class
        self.log = log
        self.max_states = max_states
        self.use_iter_deep = iter_deep
        self.nxt_dep_func = nxt_dep_func
        self.move_order_fn = move_order_fn
        self.allow_fivefold_repetition = allow_fivefold_repetition

    def minimax(self, *args, **kwargs):
        """
        Should be implemented by subclasses, including parameter types, because this varies
        according to the design of the AI.
        """
        raise NotImplementedError()

    def maximin(self, *args, **kwargs):
        """
        Should be implemented by subclasses, including parameter types, because this varies
        according to the design of the AI.
        """
        raise NotImplementedError()

    def choose_move(self) -> chess.Move:
        if self.use_iter_deep:
            return self.iter_deep_choose_move()
        return self.basic_choose_move()

    def basic_choose_move(self) -> chess.Move:
        raise NotImplementedError()

    def iter_deep_choose_move(self) -> chess.Move:
        raise NotImplementedError()

    @classmethod
    def get_moves(cls, board: chess.BoardT) -> Iterator[chess.Move]:
        """
        The default is returning the generator from board.generate_legal_moves()

        @params:
            - board: the board to get the next set of moves from

        @returns:
            - a generator of Move objects that can be iterated through

        A subclass can choose to override this method if they have some better
        idea of the order in which moves should be iterated through and/or
        an idea of moves to skip.

        TODO: make sure this does not have some sort of issue with the wrong colors;
        this method might need to have the color of the player as a parameter. Could
        be even more complicated with an independent AI.
        """
        return board.generate_legal_moves()

    def piece_drop_nxt_depth(self, **kwargs):
        """
        :param kwargs: should include 'move=mv' where mv is a chess.Move
            object. should also include 'depth=depth' where depth is the depth
            value of the caller.
        :returns: depth + 1 if move is not a drop; else returns self.max_depth - 2
        """
        if kwargs["move"].drop:
            if self.max_depth - 2 > kwargs["depth"] + 1:
                return self.max_depth - 2
            else:
                return kwargs["depth"] + 1
        return kwargs["depth"] + 1

    def rand_move_reorder(self, moves):
        """
        Randomly shuffles the order of moves; returns the result
        (makes a copy of the parameter before doing this)

        :param moves: the list of moves to shuffle
        :return: shuffled moves
        """
        r_moves = moves.copy()
        random.shuffle(r_moves)
        return r_moves

    def capture_drop_reorder(self, moves):
        """
        Randomly shuffles the order of moves; returns the result
        (makes a copy of the parameter before doing this)

        :param moves: the list of moves to shuffle
        :return: shuffled moves
        """
        r_moves = moves.copy()
        captures = list()
        drops = list()
        others = list()
        for mv in r_moves:
            if mv.capture:
                captures.append(mv)
            elif mv.drop:
                drops.append(mv)
            else:
                others.append(mv)
        if not captures == []:
            random.shuffle(captures)
        if not drops == []:
            random.shuffle(drops)
        if not others == []:
            random.shuffle(others)

        return captures + drops + others

    def utility(self, board: variant.BughouseSuperBoardT, board_id: str, players_eval: dict,
                ally_diff_pocket: variant.BughousePocketT = None,
                 enemy_diff_pocket: variant.BughousePocketT = None, to_protect=None, to_capture=None) -> dict:
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

        @returns a new dict with keys being the color and values being floating
        point scores for each respective color (does not modify the dict given).

        TODO: So, we definitely need to consider how to structure a utility evaluation
        function. Most importantly, it should be constant time so as to reduce the
        performance overhead of evaluating a state (we have plenty of overhead as
        it is; we don't need any more). One thing that could be very, very useful
        for evaluation is pinning https://en.wikipedia.org/wiki/Pin_(chess). There
        are already methods that have been created to evaluate whether pinning exists
        within chess.BaseBoard.
        """
        return self.eval_class.utility(board, board_id, players_eval, ally_diff_pocket=ally_diff_pocket,
                 enemy_diff_pocket=enemy_diff_pocket, to_protect=to_protect, to_capture=to_capture)

    def log_avail_moves(self, board, moves, depth, board_id, func):
        if self.log:
            turn = "white" if board.get_base_board(board_id).turn else "black"
            moves_print = list()
            for mv in moves:
                moves_print.append(mv.uci())
            logging.info("{0}: depth {1}, board {2}, turn {3}, moves available {4}".format(func, depth, board_id, turn, moves_print))

    def log_before_push(self, board, move, depth, board_id, func):
        if self.log:
            turn = "white" if board.get_base_board(board_id).turn else "black"
            logging.info("{0} before push: depth {1}, board {2}, turn {3}, move {4}, pockets[wA {5}, bA {6}, wB {7}, "
                         "bB {8}]".format(func, depth, board_id, turn, move, board.get_base_board(
                chess.A).get_pocket(chess.WHITE), board.get_base_board(chess.A).get_pocket(chess.BLACK), board.get_base_board(chess.B).get_pocket(chess.WHITE), board.get_base_board(chess.B).get_pocket(chess.BLACK)))

    def log_after_push(self, board, move, depth, board_id, func):
        if self.log:
            turn = "white" if board.get_base_board(board_id).turn else "black"
            logging.info("{0} after push : depth {1}, board {2}, turn {3}, move {4}, pockets[wA {5}, bA {6}, wB {7}, "
                         "bB {8}]".format(func, depth, board_id, turn, move, board.get_base_board(
                chess.A).get_pocket(chess.WHITE), board.get_base_board(chess.A).get_pocket(chess.BLACK),
                                          board.get_base_board(chess.B).get_pocket(chess.WHITE),
                                          board.get_base_board(chess.B).get_pocket(chess.BLACK)))

    def log_after_pop(self, board, move, depth, board_id, func):
        if self.log:
            turn = "white" if board.get_base_board(board_id).turn else "black"
            logging.info("{0} after pop  : depth {1}, board {2}, turn {3}, move {4}, pockets[wA {5}, bA {6}, wB {7}, "
                         "bB {8}]".format(func, depth, board_id, turn, move, board.get_base_board(
                chess.A).get_pocket(chess.WHITE), board.get_base_board(chess.A).get_pocket(chess.BLACK),
                                          board.get_base_board(chess.B).get_pocket(chess.WHITE),
                                          board.get_base_board(chess.B).get_pocket(chess.BLACK)))

    def log_forbidden_move_removal(self, board, depth, board_id, func, mv):
        if self.log:
            turn = "white" if board.get_base_board(board_id).turn else "black"
            logging.info("{0}: depth {1}, board {2}, turn {3}, removed forbidden move {4}".format(func, depth, board_id, turn, mv))


class PartneredAI(AI):
    """
    This class is a class for partnered AIs.

    In reality, each partner will be playing for itself, and will simply be
    another copy of this AI.

    Partners can be either communicating or quiet depending on the communicating
    parameter given on instantiation.

    To start out, they will only play synchronous games.
    """

    def __init__(self, name: str, board: variant.BughouseSuperBoard, board_id: str, color: chess.Color, eval_class:
    chess.utility.UtilityEvalSuper, communicating: bool = False, max_depth: int = MAX_DEPTH, print_stats: bool = False,
                 log: bool = False, max_states: bool = 1000000, iter_deep: bool = True, nxt_dep_func=None, move_order_fn=None, allow_fivefold_repetition=False):
        """
        :param name: the agent's name
        :param board: the super board for this agent's game
        :param board_id: the board_id of this agent's board
        :param color: the color of this agent on their board
        :param eval_class: the evaluation class used for evaluating a board
        :param communicating: whether this agent communicates with its partner

        :param allow_fivefold_repetition: if you allow fivefold repetition, then a draw may occur from
            such case; otherwise, a move that would cause fivefold repetition is not allowed
            to be chosen, this may cause a losing move to be chosen
        TODO: push communications down to the AIs
        """
        super().__init__(name, board, eval_class, max_depth=max_depth, print_stats=print_stats, log=log,
                         max_states=max_states, iter_deep=iter_deep, nxt_dep_func=nxt_dep_func, move_order_fn=move_order_fn, allow_fivefold_repetition=allow_fivefold_repetition)
        self.board_id = board_id
        self.color = color
        if communicating:
            self.partner_comm = CommChannel()
            self.tell_partner = CommChannel()
        self.communicating = communicating
        self.statistics = Statistics(max_depth, print_stats, board_id, color)


    def minimax(self, board: variant.BughouseSuperBoardT, board_id: str, depth: int, cutoff=None, a=-math.inf,
                          b=math.inf, original_ally_pocket: variant.BughousePocketT=None,
                          original_enemy_pocket: variant.BughousePocketT=None,
                          forbidden_moves=None) -> (float, chess.Move):
        """
        This is a minimax program with alphabeta pruning.
        Modeled after Bryce's hw3 solution from 4700

        :param board: the super_board to evaluate
        :param board_id: the baseboard id to evaluate
        :param depth: the current depth of search
        :param cutoff: an optional function to determine whether to cut off searching
        :param a: *alpha* represents the best choice so far for maximin (worst for minimax)
        :param b: *beta* represents the best choice so far for minimax (worst for maximin)
        :param original_ally_pocket: is the original pocket (before minimax was first called) of the ally of this agent
        :param original_enemy_pocket: is the original pocket (before minimax was first called) of the enemy of this
        agent in the other board
        :param forbidden_moves: moves that we do not want to allow; not passed to following iterations; must
            be a list of Move objects
        :return:
            - the utility of the state if the state is terminal,
                null action (because no further action is possible)
            - the maximum utility possible from the maximin result of taking each action,
                the action taken
            - the state's utility value if the cutoff depth has been reached,
                null action (because we are not allowed to continue actions)
        """
        self.statistics.inc_states()
        # The default cutoff test is whether we've reached the max_depth
        if cutoff is None:
            def cutoff(board, depth):
                return depth >= self.max_depth

        # checkmate is terminal
        if board.get_base_board(board_id).is_checkmate():
                return -float("inf"), chess.Move.null()

        # The cutoff condition has been reached
        if cutoff(board, depth):
            players = dict()
            players[self.color] = None
            if self.communicating:
                if board_id == "A":
                    ally_diff = original_ally_pocket.diff(board.get_base_board("B").get_pocket(not self.color))
                    enemy_diff = original_enemy_pocket.diff(board.get_base_board("B").get_pocket(self.color))
                else:
                    ally_diff = original_ally_pocket.diff(board.get_base_board("A").get_pocket(not self.color))
                    enemy_diff = original_enemy_pocket.diff(board.get_base_board("A").get_pocket(self.color))
                t = time.time()
                test1 = self.partner_comm.get_please_protect()
                test2 = self.partner_comm.get_please_capture()
                res = self.utility(board, board_id, players, ally_diff_pocket=ally_diff, enemy_diff_pocket=enemy_diff,
                                   to_protect=self.partner_comm.get_please_protect(),
                                   to_capture=self.partner_comm.get_please_capture())
                self.statistics.eval_func_time(t)
                self.statistics.eval_func_count_inc()
                return res[self.color], chess.Move.null()
            else:
                t = time.time()
                res = self.utility(board, board_id, players)
                self.statistics.eval_func_time(t)
                self.statistics.eval_func_count_inc()
                return res[self.color], chess.Move.null()

        # Other situations
        val = -float("inf")
        best_move = None
        moves = list()
        for mv in self.get_moves(board.get_base_board(board_id)):
            moves.append(mv)
        
        # remove any forbidden moves if they exist
        if forbidden_moves:
            for mv in forbidden_moves:
                try:
                    moves.remove(mv)
                    self.log_forbidden_move_removal(mv)
                except:
                    pass

        # logging
        self.statistics.current_branching_max(len(moves))
        self.log_avail_moves(board, moves, depth, board_id, "minimax")

        # order the moves in a specific way if provided
        if self.move_order_fn:
            moves = self.move_order_fn(self=self, moves=moves)

        for mv in moves:
            self.log_before_push(board, mv, depth, board_id, "minimax")
            board.push(mv, board_id)  # push first
            self.log_after_push(board, mv, depth, board_id, "minimax")
            nxt_dep = self.nxt_dep_func(self=self, depth=depth, move=mv) if self.nxt_dep_func else depth + 1
            new_val, _ = self.maximin(board, board_id, nxt_dep, cutoff, a, b,
                                                original_ally_pocket=original_ally_pocket,
                                                original_enemy_pocket=original_enemy_pocket)
            board.pop()  # then pop
            self.log_after_pop(board, mv, depth, board_id, "minimax")
            if new_val > val or best_move is None:
                val = new_val
                best_move = mv
            if val >= b:
                if best_move is None:
                    raise UnboundLocalError("minimax: best_move was about to be returned"
                        " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
                        .format(self.statistics.get_states_evaluated(), depth, moves))
                return val, best_move
            a = max(a, val)
        if best_move is None:
            raise UnboundLocalError("minimax: best_move was about to be returned"
                " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
                .format(self.statistics.get_states_evaluated(), depth, moves))
        return val, best_move

    def maximin(self, board: variant.BughouseSuperBoardT, board_id: str, depth: int, cutoff=None, a=-math.inf,
                          b=math.inf, original_ally_pocket: variant.BughousePocketT=None,
                          original_enemy_pocket: variant.BughousePocketT=None,
                          forbidden_moves=None) -> (float, chess.Move):
        """
        This is a maximin program with alphabeta pruning.
        Modeled after Bryce's hw3 solution from 4700

        :param board: the super_board to evaluate
        :param board_id: the baseboard id to evaluate
        :param depth: the current depth of search
        :param cutoff: an optional function to determine whether to cut off searching
        :param a: *alpha* represents the best choice so far for maximin (worst for minimax)
        :param b: *beta* represents the best choice so far for minimax (worst for maximin)
        :param original_ally_pocket: is the original pocket (before minimax was first called) of the ally of this agent
        :param original_enemy_pocket: is the original pocket (before minimax was first called) of the enemy of this
        :param forbidden_moves: moves that we do not want to allow; not passed to following iterations; must
            be a list of Move objects
        agent in the other board
        :return:
            - the utility of the state if the state is terminal,
                null action (because no further action is possible)
            - the maximum utility possible from the maximin result of taking each action,
                the action taken
            - the state's utility value if the cutoff depth has been reached,
                null action (because we are not allowed to continue actions)
        """
        self.statistics.inc_states()
        # The default cutoff test is whether we've reached self.max_depth
        if cutoff is None:
            def cutoff(board, depth):
                return depth >= self.max_depth

        # checkmate is terminal
        if board.get_base_board(board_id).is_checkmate():
                return float("inf"), chess.Move.null()

        # The cutoff condition has been reached
        if cutoff(board, depth):
            players = dict()
            players[self.color] = None
            if self.communicating:
                if board_id == "A":
                    pocket = board.get_base_board("B").get_pocket(not self.color)
                    pieces = pocket.pieces
                    # print(board.get_base_board("B").get_pocket(not self.color))
                    ally_diff = original_ally_pocket.diff(board.get_base_board("B").get_pocket(not self.color))
                    # print(board.get_base_board("B").get_pocket(self.color))
                    enemy_diff = original_enemy_pocket.diff(board.get_base_board("B").get_pocket(self.color))
                else:
                    ally_diff = original_ally_pocket.diff(board.get_base_board("A").get_pocket(not self.color))
                    enemy_diff = original_enemy_pocket.diff(board.get_base_board("A").get_pocket(self.color))
                t = time.time()
                # print(ally_diff)
                # print(enemy_diff)
                # print("ok")
                to_protect = self.partner_comm.get_please_protect()
                to_capture = self.partner_comm.get_please_capture()
                res = self.utility(board, board_id, players, ally_diff_pocket=ally_diff, enemy_diff_pocket=enemy_diff,
                                   to_protect=to_protect,
                                   to_capture=to_capture)
                self.statistics.eval_func_time(t)
                self.statistics.eval_func_count_inc()
                return res[self.color], chess.Move.null()
            else:
                t = time.time()
                res = self.utility(board, board_id, players)
                self.statistics.eval_func_time(t)
                self.statistics.eval_func_count_inc()
                return res[self.color], chess.Move.null()

        # Other situations
        val = float("inf")
        best_move = None
        moves = list()
        for mv in self.get_moves(board.get_base_board(board_id)):
            moves.append(mv)

        # remove any forbidden moves if they exist
        if forbidden_moves:
            for mv in forbidden_moves:
                try:
                    moves.remove(mv)
                    self.log_forbidden_move_removal(mv)
                except:
                    pass

        # logging
        self.statistics.current_branching_max(len(moves))
        self.log_avail_moves(board, moves, depth, board_id, "maximin")

        # order the moves in a specific way if provided
        if self.move_order_fn:
            moves = self.move_order_fn(self=self, moves=moves)

        for mv in moves:
            self.log_before_push(board, mv, depth, board_id, "maximin")
            board.push(mv, board_id)  # push first
            self.log_after_push(board, mv, depth, board_id, "maximin")
            nxt_dep = self.nxt_dep_func(self=self, depth=depth, move=mv) if self.nxt_dep_func else depth + 1
            new_val, _ = self.minimax(board, board_id, nxt_dep, cutoff, a, b,
                                                original_ally_pocket=original_ally_pocket,
                                                original_enemy_pocket=original_enemy_pocket)
            board.pop()  # then pop
            self.log_after_pop(board, mv, depth, board_id, "maximin")
            if new_val < val or best_move is None:
                val = new_val
                best_move = mv
            if val <= a:
                if best_move is None:
                    raise UnboundLocalError("maximin: best_move was about to be returned"
                        " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
                        .format(self.statistics.get_states_evaluated(), depth, moves))
                return val, best_move
            b = min(b, val)
        if best_move is None:
            raise UnboundLocalError("maximin: best_move was about to be returned"
                " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
                .format(self.statistics.get_states_evaluated(), depth, moves))
        return val, best_move

    def partners_advice(self, advice: CommChannel):
        """
        Given advice from a partner, take that into account if communicating.
        """
        if self.communicating:
            self.partner_comm = advice

    def give_advice(self) -> CommChannel:
        """
        Give advice to a partner. Returns None if not communicating.
        """
        if self.communicating:
            return self.tell_partner
        return None

    def basic_choose_move(self) -> chess.Move:
        """
        Do an alpha-beta minimax search with at most depth max_depth. Return the result.
        """
        self.statistics.single_move_reset()
        # copy the board
        super_boardc = self.board.copy()
        def cutoff(b, d): return d >= self.max_depth
        forbidden_moves = list()
        if self.board_id == "A":
            other_board = "B"
        else:
            other_board = "A"
        while True:
            if self.color:
                # player is white: trying to maximize moves
                if self.communicating:
                    original_ally_pocket = super_boardc.get_base_board(other_board).get_pocket(not self.color)
                    original_enemy_pocket = super_boardc.get_base_board(other_board).get_pocket(self.color)
                    best_val, best_move = self.minimax(super_boardc, self.board_id, 0, cutoff,
                                                       original_ally_pocket=original_ally_pocket,
                                                       original_enemy_pocket=original_enemy_pocket, forbidden_moves=forbidden_moves)
                    self.find_dangerous_drops(best_move, best_val)
                    self.find_valuable_drops(best_move, best_val)
                else:
                    _, best_move = self.minimax(super_boardc, self.board_id, 0, cutoff, forbidden_moves=forbidden_moves)
            else:
                # color is black: trying to minimize moves
                if self.communicating:
                    original_ally_pocket = super_boardc.get_base_board(other_board).get_pocket(not self.color)
                    original_enemy_pocket = super_boardc.get_base_board(other_board).get_pocket(self.color)
                    best_val, best_move = self.maximin(super_boardc, self.board_id, 0, cutoff,
                                                       original_ally_pocket=original_ally_pocket,
                                                       original_enemy_pocket=original_enemy_pocket, forbidden_moves=forbidden_moves)
                    self.find_dangerous_drops(best_move, best_val)
                    self.find_valuable_drops(best_move, best_val)
                else:
                    _, best_move = self.maximin(super_boardc, self.board_id, 0, cutoff, forbidden_moves=forbidden_moves)
            if not self.allow_fivefold_repetition:
                super_boardc.push(best_move, self.board_id)
                is_fivefold_repetition = super_boardc.is_fivefold_repetition()
                super_boardc.pop()
                if not is_fivefold_repetition:
                    break
                else:
                    forbidden_moves = [best_move]
                    best_move = None
            else:
                break
        self.statistics.update()
        self.statistics.log()
        return best_move

    def iter_deep_choose_move(self) -> chess.Move:
        """
        iterative_deepening() executes minimax and maximin in an iterative
        deepening fashion. Increasing depth one ply per round.

        @params:
            - player: the player color that the best move is being searched for
            - board: the starting board to search from for the next move
            - max_depth: the maximum number of plies to search
            - a: alpha
            - b: beta

        @returns:
            -

        Note: Independent AIs that handle both boards at once should reimplement this method; it's not designed
        to handle an AI that can play either side.
        """
        # copy the board
        super_boardc = self.board.copy()
        dep_count = 1
        best_move = None
        self.statistics.single_move_reset()
        forbidden_moves = list()
        if self.board_id == "A":
            other_board = "B"
        else:
            other_board = "A"
        while True:  # need to keep going if the chosen move causes fivefold repetition, and that is set to False
            while dep_count <= self.max_depth and self.statistics.get_states_evaluated() <= self.max_states:
                self.statistics.iter_deep_reset()
                def cutoff(b, d): return d >= dep_count
                if self.color:
                    # color is white: trying to maximize moves
                    if self.communicating:
                        original_ally_pocket = super_boardc.get_base_board(other_board).get_pocket(not self.color)
                        original_enemy_pocket = super_boardc.get_base_board(other_board).get_pocket(self.color)
                        best_val, best_move = self.minimax(super_boardc, self.board_id, 0, cutoff,
                                                           original_ally_pocket=original_ally_pocket,
                                                           original_enemy_pocket=original_enemy_pocket, forbidden_moves=forbidden_moves)
                        # self.find_dangerous_drops(best_move, best_val) # why were these removed?
                        # self.find_valuable_drops(best_move, best_val)
                    else:
                        _, best_move = self.minimax(super_boardc, self.board_id, 0, cutoff, forbidden_moves=forbidden_moves)
                else:
                    # color is black: trying to minimize moves
                    if self.communicating:
                        original_ally_pocket = super_boardc.get_base_board(other_board).get_pocket(not self.color)
                        original_enemy_pocket = super_boardc.get_base_board(other_board).get_pocket(self.color)
                        best_val, best_move = self.maximin(super_boardc, self.board_id, 0, cutoff,
                                                           original_ally_pocket=original_ally_pocket,
                                                           original_enemy_pocket=original_enemy_pocket, forbidden_moves=forbidden_moves)
                        # self.find_dangerous_drops(best_move, best_val) # why were these removed?
                        # self.find_valuable_drops(best_move, best_val)
                    else:
                        _, best_move = self.maximin(super_boardc, self.board_id, 0, cutoff, forbidden_moves=forbidden_moves)
                dep_count += 1
            if best_move is None:
                raise UnboundLocalError("best_move was about to be returned empty; here are the stats: states evaluated {0}, dep_count {1}".format(
                    self.statistics.get_states_evaluated(), dep_count))
            if not self.allow_fivefold_repetition:
                super_boardc.push(best_move, self.board_id)
                is_fivefold_repetition = super_boardc.is_fivefold_repetition()
                super_boardc.pop()
                if not is_fivefold_repetition:
                    if self.communicating:
                        self.find_dangerous_drops(best_move, best_val)
                        self.find_valuable_drops(best_move, best_val)
                    break
                else:
                    dep_count = 1
                    forbidden_moves = [best_move]
                    best_move = None
            else:
                if self.communicating:
                    self.find_dangerous_drops(best_move, best_val)
                    self.find_valuable_drops(best_move, best_val)
                break
        self.statistics.update()
        self.statistics.log()
        return best_move

    def find_dangerous_drops(self, move: chess.Move, old_val):
        """
        If communicating is set to True, this will check to see what additional
        pieces added to our opponent's pocket could enable them to mate us.
        This is evaluated after our move is decided.

        :param move: the move we will make first
        :param old_val: This is the value the best old move will give
        """
        if self.communicating:
            super_boardc = self.board.copy()
            super_boardc = self.board.copy()
            super_boardc.push(move, self.board_id)

            our_poc = super_boardc.get_base_board(self.board_id).get_pocket(self.color).copy()
            opp_poc = super_boardc.get_base_board(self.board_id).get_pocket(not self.color).copy()
            # ^ our opponent's current pocket; no need to check a
            # piece that they already have, because that just adds calc time

            not_in_pos = variant.BughousePocket()  # the pieces our opponent does not currently have in pocket (minus the king)
            for p in chess.PIECE_TYPES:
                if not p == chess.KING:
                    not_in_pos.add(p)
            # not_in_pos.remove(chess.KING)
            for p, num in opp_poc.pieces.items():
                if num > 0:
                    not_in_pos.remove(p)

            danger = dict()
            if self.board_id == "A":
                other_board = "B"
            else:
                other_board = "A"
            for p, i in not_in_pos.pieces.items():
                original_ally_pocket = super_boardc.get_base_board(other_board).get_pocket(not self.color).copy()
                original_enemy_pocket = super_boardc.get_base_board(other_board).get_pocket(self.color).copy()
                if i > 0:
                    print("###########################")
                    super_boardc.get_pocket(self.board_id)
                    print(original_ally_pocket)
                    print(original_enemy_pocket)
                    super_boardc.push_to_pocket(p, self.board_id, not self.color)
                    super_boardc.get_pocket(self.board_id)
                    if self.color:
                        new_val, new_best_move = self.maximin(super_boardc, self.board_id, 2,
                                                                        original_ally_pocket=original_ally_pocket,
                                                                        original_enemy_pocket=original_enemy_pocket)
                    else:
                        new_val, new_best_move = self.maximin(super_boardc, self.board_id, 2,
                                                                        original_ally_pocket=original_ally_pocket,
                                                                        original_enemy_pocket=original_enemy_pocket)
                    danger[p] = new_val - old_val
                    super_boardc.rm_from_pocket(p, self.board_id, not self.color)

            self.tell_partner.set_please_protect(danger)

            # super # I don't know what I was doing below
            # boardc.set_pocket(not self.color, not_in_pos) # set our opponent's pocket to the pieces it doesn't have

    def find_valuable_drops(self, move: chess.Move, old_val):
        """
        If communicating is set to True, this will check to see what additional
        pieces added to our pocket are valuable for this agent to gain a significant
        advantage or mate

        :param move: the move we will make first
        :param old_val: This is the value the best old move will give
        """

        if self.communicating:
            super_boardc = self.board.copy()
            super_boardc = self.board.copy()
            super_boardc.push(move, self.board_id)

            our_poc = super_boardc.get_base_board(self.board_id).get_pocket(self.color).copy()
            opp_poc = super_boardc.get_base_board(self.board_id).get_pocket(not self.color).copy()
            # ^ our opponent's current pocket; no need to check a
            # piece that they already have, because that just adds calc time

            not_in_pos = variant.BughousePocket()  # the pieces our opponent does not currently have in pocket (minus the king)
            for p in chess.PIECE_TYPES:
                if not p == chess.KING:
                    not_in_pos.add(p)
            # not_in_pos.remove(chess.KING)
            for p, num in our_poc.pieces.items():
                if num > 0:
                    not_in_pos.remove(p)

            benefit = dict()
            if self.board_id == "A":
                other_board = "B"
            else:
                other_board = "A"
            for p, i in not_in_pos.pieces.items():
                original_ally_pocket = super_boardc.get_base_board(other_board).get_pocket(not self.color).copy()
                original_enemy_pocket = super_boardc.get_base_board(other_board).get_pocket(self.color).copy()
                if i > 0:
                    super_boardc.push_to_pocket(p, self.board_id, self.color)
                    if self.color:
                        new_val, new_best_move = self.maximin(super_boardc, self.board_id, 2,
                                                              original_ally_pocket=original_ally_pocket,
                                                              original_enemy_pocket=original_enemy_pocket)
                    else:
                        new_val, new_best_move = self.maximin(super_boardc, self.board_id, 2,
                                                              original_ally_pocket=original_ally_pocket,
                                                              original_enemy_pocket=original_enemy_pocket)
                    benefit[p] = new_val - old_val
                    super_boardc.rm_from_pocket(p, self.board_id, self.color)

            self.tell_partner.set_please_capture(benefit)


class SolitaryAIHandler:
    """
    Handles a solitary AI.

    Basically, in order to be consistent with the game playing structure
    with the partnered AIs, this class is needed.

    It contains a reference to a solitary/singular/independent AI, and requests
    the next move for the board_id and color that this class represents.

    That way, the same AI can be shared by two handlers, and each handler can
    interface between the game playing structure and the AI without really
    disrupting how everything else works.
    """

    def __init__(self, name, ai, board_id: str, color: chess.Color):
        self.name = name
        self.ai = ai
        self.board_id = board_id
        self.color = color
        class Stats:
            """
            This class is an intermediary to connect to the statistics class
            of the SolitaryAI object.
            """
            def __init__(self, ai):
                self.ai = ai

            def return_stats(self):
                return self.ai.statistics.return_stats()
        self.statistics = Stats(self.ai)

    def choose_move(self):
        return self.ai.choose_move(self.board_id, self.color)

    def partners_advice(self, advice):
        pass

    def give_advice(self):
        pass

class SolitaryAI(AI):
    """
    This class is for a singular, solitary (independent) AI that plays both boards.
    I.e, it is its own partner in Bughouse Chess.

    To start out, it will only play synchronous games.
    """

    def __init__(self, name: str, board: variant.BughouseSuperBoard, is_maxing: bool, boardA_color: chess.Color, boardB_color: chess.Color, eval_class: chess.utility.UtilityEvalSuper,
                 max_depth: int = MAX_DEPTH, print_stats: bool = False,
                 log: bool = False, max_states: bool = 1000000, iter_deep: bool = True, nxt_dep_func=None, move_order_fn=None, allow_fivefold_repetition=False):
    # def __init__(self, name: str, board: variant.BughouseSuperBoard, color_dic, is_maxing, eval_class: chess.utility.UtilityEvalSuper,
    #              max_depth: int = MAX_DEPTH):
        """
        :param name: the agent's name
        :param board: the super board for this agent's game
        :param board_id: the board_id of this agent's board
        :param color: the color of this agent on their board
        :param eval_class: the evaluation class used for evaluating a board
        TODO: push communications down to the AIs
        TODO: communications should be handled with multiprocessing Queues
        """
        super().__init__(name, board, eval_class, max_depth=max_depth, print_stats=print_stats,
                         log=log, max_states=max_states, iter_deep=iter_deep, nxt_dep_func=nxt_dep_func,
                         move_order_fn=move_order_fn, allow_fivefold_repetition=allow_fivefold_repetition)
        self.boardA_color = boardA_color
        self.boardB_color = boardB_color
        self.statistics = Statistics(max_depth, print_stats)
        self.is_maxing = is_maxing

    def utility(self, board, board_id: str, color: chess.Color):
        fst_dic = dict()
        snd_dic = dict()
        fst_dic[self.boardA_color] = None
        snd_dic[self.boardB_color] = None
        fst = super().utility(board, chess.A, fst_dic)
        snd = super().utility(board, chess.B, snd_dic)

        fst = fst[self.boardA_color]
        snd = snd[self.boardB_color]

        if self.is_maxing:
            if self.boardA_color: # is white
                ret = fst - snd
            else:
                ret = snd - fst
        else:
            if self.boardA_color: # is white
                ret = snd - fst
            else:
                ret = fst - snd
        return ret

    @staticmethod
    def flip(board_id):
        if board_id == 'A':
            return 'B'
        else:
            return 'A'

    @staticmethod
    def flip_color(color):
        if color == chess.WHITE:
            return chess.BLACK
        else:
            return chess.WHITE

    def cutoff(self, board, depth):
        if depth > 3:
            return True
        else:
            return False

    @staticmethod
    def board_logger(board: variant.BughouseSuperBoardT, msg: str):
        print(msg)
        print(board.get_base_board('A').move_stack)
        print(board.get_base_board('B').move_stack)
        print(board.get_base_board('A').pockets)
        print(board.get_base_board('B').pockets)

    def minimax(self, board: variant.BughouseSuperBoardT, board_id: str, depth: int, move_count: int, cutoff=None, alpha=float('-Inf'), beta=float('Inf'), forbidden_moves=None) -> (float, chess.Move):
        """
        :param board: the super_board to evaluate
        :param board_id: the baseboard id to evaluate
        :param depth: the current depth of search
        :param cutoff: an optional function to determine whether to cut off searching
        :param a: *alpha* represents the best choice so far for maximin (worst for minimax)
        :param b: *beta* represents the best choice so far for minimax (worst for maximin)
        :param forbidden_moves: moves that we do not want to allow; not passed to following iterations; must
            be a list of Move objects
        :return:
            - the utility of the state if the state is terminal,
                null action (because no further action is possible)
            - the maximum utility possible from the maximin result of taking each action,
                the action taken
            - the state's utility value if the cutoff depth has been reached,
                null action (because we are not allowed to continue actions)
        """
        color = board.get_base_board(board_id).turn # TODO: may need to change

        if cutoff is None:
            def cutoff(board, depth):
                return depth >= self.max_depth

        # checkmate is terminal
        if board.get_base_board(board_id).is_checkmate():
                #print('CHECKMATE: ' + board_id)
                #print(board.unicode_ext(borders=True, labels=True))
                return float('-Inf'), chess.Move.null()

        if cutoff(board, depth):
            eval_result = self.utility(board, board_id, color)
            t = time.time()
            self.statistics.eval_func_time(t)
            self.statistics.eval_func_count_inc()
            return eval_result, None

        # Other situations
        val = float('-Inf')
        best_move = None
        moves = list()
        for mv in self.get_moves(board.get_base_board(board_id)):
            moves.append(mv)

        # remove any forbidden moves if they exist
        if forbidden_moves:
            for mv in forbidden_moves:
                try:
                    moves.remove(mv)
                    self.log_forbidden_move_removal(mv)
                except:
                    pass

        # logging
        self.statistics.current_branching_max(len(moves))
        self.log_avail_moves(board, moves, depth, board_id, "minimax")

        # order the moves in a specific way if provided
        if self.move_order_fn:
            moves = self.move_order_fn(self=self, moves=moves)

        # save = board.get_base_board(board_id).turn
        for move in moves:
            self.log_before_push(board, mv, depth, board_id, "minimax")
            # board.get_base_board(board_id).turn = save
            # board = self.board.copy()
            board.push(move, board_id) # push first
            self.log_after_push(board, mv, depth, board_id, "minimax")
            nxt_dep = self.nxt_dep_func(self=self, depth=depth, move=mv) if self.nxt_dep_func else depth + 1
            # possible = self.maximin(board, self.flip(board_id), nxt_dep, cutoff, alpha, beta)[0]
            if move_count % 4 == 3:
                possible = self.minimax(board, self.flip(board_id), depth + 1, move_count + 1, cutoff, alpha, beta)[0]
            else:
                possible = self.maximin(board, self.flip(board_id), depth + 1, move_count + 1, cutoff, alpha, beta)[0]
            board.pop() # then pop
            self.log_after_pop(board, mv, depth, board_id, "minimax")
            if possible > val:
                val = possible
                best_move = move

            alpha = max(alpha, val)
            if val >= beta:
                # if best_move is None:
                #     raise UnboundLocalError("minimax: best_move was about to be returned"
                #         " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
                #         .format(self.statistics.get_states_evaluated(), depth, moves))
                return val, best_move
        # if best_move is None:
        #     raise UnboundLocalError("minimax: best_move was about to be returned"
        #         " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
        #         .format(self.statistics.get_states_evaluated(), depth, moves))
        return val, best_move

    def maximin(self, board: variant.BughouseSuperBoardT, board_id: str, depth: int, move_count: int, cutoff=None, alpha=float('-Inf'), beta=float('Inf'), forbidden_moves=None) -> (float, chess.Move):
        """
        :param board: the super_board to evaluate
        :param board_id: the baseboard id to evaluate
        :param depth: the current depth of search
        :param cutoff: an optional function to determine whether to cut off searching
        :param a: *alpha* represents the best choice so far for maximin (worst for minimax)
        :param b: *beta* represents the best choice so far for minimax (worst for maximin)
        :param forbidden_moves: moves that we do not want to allow; not passed to following iterations; must
            be a list of Move objects
        :return:
            - the utility of the state if the state is terminal,
                null action (because no further action is possible)
            - the maximum utility possible from the maximin result of taking each action,
                the action taken
            - the state's utility value if the cutoff depth has been reached,
                null action (because we are not allowed to continue actions)
        """
        color = board.get_base_board(board_id).turn # TODO: may need to change

        if cutoff is None:
            def cutoff(board, depth):
                return depth >= self.max_depth

        # checkmate is terminal
        if board.get_base_board(board_id).is_checkmate():
                #print('CHECKMATE: ' + board_id)
                #print(board.unicode_ext(borders=True, labels=True))
                return float('Inf'), chess.Move.null()

        if cutoff(board, depth):
            eval_result = self.utility(board, board_id, color)
            t = time.time()
            self.statistics.eval_func_time(t)
            self.statistics.eval_func_count_inc()
            return eval_result, None

        # Other situations
        val = float('Inf')
        best_move = None
        moves = list()
        for mv in self.get_moves(board.get_base_board(board_id)):
            moves.append(mv)

        # remove any forbidden moves if they exist
        if forbidden_moves:
            for mv in forbidden_moves:
                try:
                    moves.remove(mv)
                    self.log_forbidden_move_removal(mv)
                except:
                    pass

        # logging
        self.statistics.current_branching_max(len(moves))
        self.log_avail_moves(board, moves, depth, board_id, "maximin")

        # order the moves in a specific way if provided
        if self.move_order_fn:
            moves = self.move_order_fn(self=self, moves=moves)

        # save = board.get_base_board(board_id).turn
        for move in moves:
            # board.get_base_board(board_id).turn = save
            # board = self.board.copy()
            self.log_before_push(board, mv, depth, board_id, "maximin")
            board.push(move, board_id) # push first
            self.log_after_push(board, mv, depth, board_id, "maximin")
            nxt_dep = self.nxt_dep_func(self=self, depth=depth, move=mv) if self.nxt_dep_func else depth + 1
            # possible = self.minimax(board, self.flip(board_id), nxt_dep, cutoff, alpha, beta)[0]
            if move_count % 4 == 1:
                possible = self.maximin(board, self.flip(board_id), depth + 1, move_count + 1, cutoff, alpha, beta)[0]
            else:
                possible = self.minimax(board, self.flip(board_id), depth + 1, move_count + 1, cutoff, alpha, beta)[0]
            board.pop() # then pop
            self.log_after_pop(board, mv, depth, board_id, "maximin")
            if possible < val:
                val = possible
                best_move = move

            beta = min(beta, val)
            if val <= alpha:
                # if best_move is None:
                #     raise UnboundLocalError("maximin: best_move was about to be returned"
                #         " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
                #         .format(self.statistics.get_states_evaluated(), depth, moves))
                return val, best_move
        # if best_move is None:
        #     raise UnboundLocalError("maximin: best_move was about to be returned"
        #         " empty; here are the stats: states evaluated {0}, depth {1}, moves {2}"
        #         .format(self.statistics.get_states_evaluated(), depth, moves))
        return val, best_move

    # def choose_move(self, board_id) -> chess.Move:
        # if self.is_maxing:
        #     _, best_move = self.minimax(super_boardc, board_id, 0, 0)
        # else:
        #     _, best_move = self.maximin(super_boardc, board_id, 0, 0)
        # return best_move

    def choose_move(self, board_id: str, color: chess.Color) -> chess.Move:
        if self.use_iter_deep:
            mv = self.iter_deep_choose_move(board_id, color)
        else:
            mv = self.basic_choose_move(board_id, color)
        assert mv is not None, "Can't choose None for a move!"
        return mv

    def basic_choose_move(self, board_id, color) -> chess.Move:
        """
        Do an alpha-beta minimax search with at most depth max_depth. Return the result.
        """
        self.statistics.single_move_reset()
        # copy the board
        super_boardc = self.board.copy()
        def cutoff(b, d): return d >= self.max_depth
        forbidden_moves = list()
        if board_id == "A":
            other_board = "B"
        else:
            other_board = "A"
        while True:
            if self.is_maxing:
                # trying to maximize moves
                _, best_move = self.minimax(super_boardc, board_id, 0, 0, cutoff, forbidden_moves=forbidden_moves)
            else:
                # trying to minimize moves
                _, best_move = self.maximin(super_boardc, board_id, 0, 0, cutoff, forbidden_moves=forbidden_moves)
            if not self.allow_fivefold_repetition:
                if best_move == None:
                    best_move = next(self.get_moves(self.board.get_base_board(board_id)))
                super_boardc.push(best_move, board_id)
                is_fivefold_repetition = super_boardc.is_fivefold_repetition()
                super_boardc.pop()
                if not is_fivefold_repetition:
                    break
                else:
                    forbidden_moves = [best_move]
                    best_move = None
            else:
                break
        self.statistics.update()
        self.statistics.log()
        return best_move

    def iter_deep_choose_move(self, board_id, color) -> chess.Move:
        """
        iterative_deepening() executes minimax and maximin in an iterative
        deepening fashion. Increasing depth one ply per round.

        @params:
            - player: the player color that the best move is being searched for
            - board: the starting board to search from for the next move
            - max_depth: the maximum number of plies to search
            - a: alpha
            - b: beta

        @returns:
            -

        Note: Independent AIs that handle both boards at once should reimplement this method; it's not designed
        to handle an AI that can play either side.
        """
         # copy the board
        print()
        print()
        print('new search!')
        print(board_id)
        print(color)

        super_boardc = self.board.copy()
        dep_count = 1
        best_move = None
        self.statistics.single_move_reset()
        forbidden_moves = list()
        if board_id == "A":
            other_board = "B"
        else:
            other_board = "A"
        while True:  # need to keep going if the chosen move causes fivefold repetition, and that is set to False
            while dep_count <= self.max_depth and self.statistics.get_states_evaluated() <= self.max_states:
                self.statistics.iter_deep_reset()
                def cutoff(b, d): return d >= dep_count
                if self.is_maxing:
                    # trying to maximize moves
                    _, best_move = self.minimax(super_boardc, board_id, 0, 0, cutoff, forbidden_moves=forbidden_moves)
                else:
                    # trying to minimize moves
                    _, best_move = self.maximin(super_boardc, board_id, 0, 0, cutoff, forbidden_moves=forbidden_moves)
                dep_count += 1
            # if best_move is None:
            #     raise UnboundLocalError("best_move was about to be returned empty; here are the stats: states evaluated {0}, dep_count {1}".format(
            #         self.statistics.get_states_evaluated(), dep_count))
            if best_move == None:
                best_move = next(self.get_moves(self.board.get_base_board(board_id)))
            if not self.allow_fivefold_repetition:
                super_boardc.push(best_move, board_id)
                is_fivefold_repetition = super_boardc.is_fivefold_repetition()
                super_boardc.pop()
                if not is_fivefold_repetition:
                    break
                else:
                    dep_count = 1
                    forbidden_moves = [best_move]
                    best_move = None
            else:
                break
        self.statistics.update()
        self.statistics.log()
        return best_move

    def partners_advice(self, advice):
        pass

    def give_advice(self):
        pass

class Statistics:

    def __init__(self, max_depth, print_stats: bool = False, board_id=None, color=None):
        self.print_stats = print_stats
        self.msgs = list()
        self.max_depth = max_depth
        self.statistics = dict()
        self.total_states = 0
        self.branching = 0
        self.avg_states_per_move = 0.0
        self.avg_eval_func_time = 0.0
        self.total_eval_func_time = 0
        self.states = 0
        self.cur_branching = 0
        self.cur_move = 0
        self._eval_func_time = 0.0
        self.eval_func_count = 1
        self.leaf_states = 0
        self.board_id = board_id
        self.color = color
        if self.board_id is not None and self.color is not None:
            color = 'white' if self.color else 'black'
            self.agent_name = "{0}{1}".format(color, self.board_id)
            self.id_str = "Stats for Agent {}\n".format(self.agent_name)
        else:
            self.agent_name = None
            self.id_str = None

    def append_stats(self, filename):
        """
        Appends all the stats stored in self.msgs to the end of filename
        with a header identifying this AI.
        """
        with open(filename, "a") as f:
            f.write(self.return_stats())

    def return_stats(self):
        builder = list()
        if self.id_str is not None:
            builder.append(self.id_str)
        else:
            builder.append("Unidentified agent divider \n")
        for m in self.msgs:
            builder.append(m)
            builder.append("\n")
        return "".join(builder)

    def single_move_reset(self):
        self.states = 0
        self.leaf_states = 0
        self.cur_branching = 0
        self.cur_move += 1
        self._eval_func_time = 0.0
        self.eval_func_count = 1

    def iter_deep_reset(self):
        self.states = 0
        self.leaf_states = 0
        self.cur_branching = 0
        self._eval_func_time = 0.0
        self.eval_func_count = 1

    def update(self):
        # self.cur_branching = self.states ** (1.0 / (self.max_depth - 1))
        # self.cur_branching = self.leaf_states ** (1.0 / self.max_depth)
        self.cur_branching = self.eval_func_count ** (1.0 / self.max_depth)
        self.total_states += self.states
        self.avg_states_per_move = self.total_states / self.cur_move
        self.branching = max(self.cur_branching, self.branching)
        new_eval_count = self.total_eval_func_time + self.eval_func_count
        self.avg_eval_func_time = (self.avg_eval_func_time * self.total_eval_func_time +
             self._eval_func_time) / new_eval_count
        self.total_eval_func_time = new_eval_count

    def log(self):
        builder = list()
        builder.append("Move number {} \n".format(self.cur_move))
        builder.append("Total States for game: {}\n".format(self.total_states))
        builder.append("Max branching factor for game: {}\n".format(self.branching))
        builder.append("Average states per move for game: {}\n".format(self.avg_states_per_move))
        builder.append("Average eval function execution time for game: {}\n".format(self.avg_eval_func_time))
        builder.append("Eval function execution count: {}\n".format(self.total_eval_func_time))
        builder.append("States for current turn: {}\n".format(self.states))
        builder.append("Current turn branching factor: {}\n".format(self.cur_branching))
        builder.append("Current turn eval function time: {}\n".format(self._eval_func_time))
        builder.append("Current turn eval function count: {}\n".format(self.eval_func_count))
        cur_turn_avg_eval = self._eval_func_time / self.eval_func_count
        builder.append("Current turn eval function average time: {}\n".format(cur_turn_avg_eval))
        built = "".join(builder)
        self.msgs.append(built)

        if not self.print_stats:
            return
        print("logging" + str(self.cur_move))
        if self.agent_name is not None:
            filename = "stats_{1}_{2}_{0}.txt".format(int(time.time()), self.agent_name, self.cur_move)
        else:
            filename = "stats_{0}_{1}.txt".format(int(time.time()), self.cur_move)
        with open(filename, "w+") as f:
            if self.id_str is not None:
                f.write(self.id_str)
            f.write(built)

    def inc_states(self):
        self.states += 1

    def eval_func_count_inc(self):
        self.eval_func_count += 1

    def eval_func_time(self, t):
        self._eval_func_time += time.time() - t

    def current_branching_max(self, branching):
        self.cur_branching = max(self.cur_branching, branching)

    def get_states_evaluated(self):
        return self.states

    def inc_leaf(self):
        self.leaf_states += 1
