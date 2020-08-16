import pychess
from pychess import chess as chess
from pychess.chess import variant as variant
from pychess.chess import ai as ai
from pychess.chess.ai import CommChannel as CommChannel
import logging
import pickle
import random
import time


class PrescribedAgent:
    """
    Plays the moves in the order they are prescribed in a list of moves given
    at initialization. Not responsible for damages caused by prescription of
    invalid moves. Once run out of moves, throws error.
    """
    def __init__(self, name: str, board: variant.BughouseSuperBoard, board_id: str, color: chess.Color, moves):
        """
        :param moves: list of moves (as strings) to make in chronological order
        """
        self.name = name + " prescribed"
        self.board_id = board_id
        self.color = color
        self.board = board
        moves.reverse()
        self.moves = moves
        class Stats:
            """
            This class only exists to keep errors from occuring
            """
            def __init__(self):
                pass

            def return_stats(self):
                return ""
        self.statistics = Stats()

    def choose_move(self):
        return chess.Move.from_uci(self.moves.pop())

    def partners_advice(self, comm):
        """
        I'm pretty sure nothing needs to be done here.
        """
        pass

    def give_advice(self):
        """
        I think sending a dummy communication will suffice
        """
        return ai.CommChannel()


class RandomAgent:
    """
    Plays a random available move.
    """
    def __init__(self, name: str, board: variant.BughouseSuperBoard, board_id: str, color: chess.Color):
        """
        """
        self.name = name + " random"
        self.board_id = board_id
        self.color = color
        self.board = board
        class Stats:
            """
            This class only exists to keep errors from occuring
            """
            def __init__(self):
                pass

            def return_stats(self):
                return ""
        self.statistics = Stats()

    def choose_move(self) -> chess.Move:
        moves = list()
        for mv in self.board.get_base_board(self.board_id).generate_legal_moves():
            moves.append(mv)
        return random.choice(moves)

    def partners_advice(self, comm):
        """
        I'm pretty sure nothing needs to be done here.
        """
        pass

    def give_advice(self):
        """
        I think sending a dummy communication will suffice
        """
        return ai.CommChannel()


class HumanAgent:
    """
    This class enables a human agent to play against the computer agents.

    Currently achieved only through the command-line.

    Maybe some day this can be done using a webpage?
    """
    HELP_STRING = "Not sure what to put in here yet."

    def __init__(self, name: str, board: variant.BughouseSuperBoard, board_id: str, color: chess.Color, label_pref:bool=True, border_pref:bool=True, move_hint_pref:bool=False):
        """
        :param board_id: this player's board_id
        :param color: this player's color
        :param board: the shared super board copy
        :param label_pref: preference for whether board labels should be printed when
            printing the boards
        :param border_pref: preference for whether board borders should be printed when
            printing the boards
        :param move_hint_pref: preference for whether legal moves should be printed
            when choosing a move; a choice for false will be ignore after 3 invalid move attempts
        """
        self.name = name
        self.board_id = board_id
        self.color = color
        self.board = board
        self.label_pref = label_pref
        self.border_pref = border_pref
        self.move_hint_pref = move_hint_pref
        class Stats:
            """
            This class only exists to keep errors from occuring
            """
            def __init__(self):
                pass

            def return_stats(self):
                return ""
        self.statistics = Stats()

    def choose_move(self) -> chess.Move:
        color = "white" if self.color else "black"
        print("Player {} {}, it's your turn to make a move!".format(color, self.board_id))
        print_moves = self.move_hint_pref
        tries = 0
        while True:
            if tries > 3:
                print_moves = True
            moves = list()
            for mv in self.board.get_base_board(self.board_id).generate_legal_moves():
                moves.append(mv.uci())
            if print_moves:
                builder = list()
                builder.append("Here are the available moves: ")
                comma = False
                for mv in moves:
                    if comma:
                        builder.append(',')
                    else:
                        comma = True
                    builder.append(mv)
                print("".join(builder))
            choice = input()
            if choice in moves:
                return chess.Move.from_uci(choice)
            elif choice == 'help' or choice == 'h':
                return "Implement me"
            elif choice[:4] == 'view':
                try:
                    move = chess.Move.from_uci(choice[5:])
                except:
                    print("{} is not a valid uci move to try".format(choice[5:]))
                boardc = self.board.copy()
                boardc.push(move)
                print(self.board.unicode_ext(borders=self.border_pref, labels=self.label_pref))
                boardc.pop()
            elif choice == "quit":
                exit(1)
            else:
                print("I'm sorry, I didn't understand that. Please try again or type 'help'.")
            tries += 1

    def partners_advice(self, comm):
        """
        I'm pretty sure nothing needs to be done here.
        """
        pass

    def give_advice(self):
        """
        I think sending a dummy communication will suffice
        """
        return ai.CommChannel()


class Runner:
    """
    This class is a simple setup (without all of the engine.py nastiness)
    for testing agents against each other.
    """

    @staticmethod
    def play(board, players, max_moves=200, log_moves=True, log_stats_after=False):
        """
        :param players: a list of the agents in the order [whiteA, whiteB, blackA, blackB]
        """
        [whiteA, whiteB, blackA, blackB] = players
        total_moves = 0
        try:
            while not board.is_game_over() and total_moves < max_moves:
                p = players[total_moves % 4]
                move = p.choose_move()
                if log_moves:
                    logging.info("move: {name} moved {move}".format(name=p.name, move=move))
                board.push(move, p.board_id)
                # push advice to partner
                if p is whiteA:
                    blackB.partners_advice(p.give_advice())
                elif p is whiteB:
                    blackA.partners_advice(p.give_advice())
                elif p is blackA:
                    whiteB.partners_advice(p.give_advice())
                elif p is blackB:
                    whiteA.partners_advice(p.give_advice())
                else:
                    # if this happens, we've got a problem
                    raise NotImplementedError
                print(board.unicode_ext(borders=True, labels=True, play_info=(p.color, p.board_id, move), pockets=True))
                total_moves += 1
            is_over = board.is_game_over()
            if is_over:
                # print(board.status())
                print("Game over! A status:{}, B status:{}".format(is_over[0], is_over[1]))
                logging.info("Game over! A status:{}, B status:{}".format(is_over[0], is_over[1]))
            print(board.unicode_ext(borders=True, labels=True))
        finally:
            if log_stats_after:
                for p in players:
                    logging.info(p.statistics.return_stats())
                    logging.info("\n")

    @staticmethod
    def play_solitary(board, players, max_moves=200, log_moves=True, log_stats_after=False):
        """
        :param players: two single ai agents
        """
        #[agent1, agent2] = players
        total_moves = 0
        board_id = 'A'
        while not board.is_game_over() and total_moves < max_moves:
            p = None
            if total_moves % 4 == 0:
                p = players[0]
                move = p.choose_move(board_id, chess.WHITE)
            elif total_moves % 4 == 1:
                p = players[1]
                move = p.choose_move(board_id, chess.WHITE)
            elif total_moves % 4 == 2:
                p = players[1]
                move = p.choose_move(board_id, chess.BLACK)
            elif total_moves % 4 == 3:
                p = players[0]
                move = p.choose_move(board_id, chess.BLACK)

            #p = players[total_moves % 2]

            if log_moves:
                logging.info("move: {name} moved {move}".format(name=p.name, move=move))
            board.push(move, board_id)

            if board_id == 'A':
                board_id = 'B'
            else:
                board_id = 'A'

            #print(board.unicode_ext(borders=True, labels=True, play_info=(p.color, p.board_id, move), pockets=True))
            print(board.unicode_ext(borders=True, labels=True, pockets=True))
            total_moves += 1
        is_over = board.is_game_over()
        if is_over:
            # print(board.status())
            print("Game over! A status:{}, B status:{}".format(is_over[0], is_over[1]))
        print(board.unicode_ext(borders=True, labels=True))

        #TODO: implement this:
        # if log_stats_after:
        #     for p in players:
        #         logging.info(p.statistics.return_stats())
        #         logging.info("\n")

    @staticmethod
    def play_comm(max_moves: int = 500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        eval_class2 = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class2, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class2, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_comm: all players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_half_comm(max_moves: int = 500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_1: all players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves)

    @staticmethod
    def play_1(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_1: all players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_2(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners. There are no special next depth functions
        or move ordering functions.

        Expect position evaluation partners to win most games

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class_1 = chess.utility.BasicMaterialEvaluationBughouseBase()
        eval_class_2 = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_2: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation; team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with position evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_3(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners. There are no special next depth functions. Uses random move reordering.

        Expect position evaluation partners to win most games

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class_1 = chess.utility.BasicMaterialEvaluationBughouseBase()
        eval_class_2 = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_3: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation and random move reordering; team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with position evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_4(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class, max_depth=depth, print_stats=log_stats_during)
        team2 = ai.SolitaryAI('Team2', board, False, chess.BLACK, chess.WHITE, eval_class, max_depth=depth, print_stats=log_stats_during)
        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        whiteB = ai.SolitaryAIHandler("whiteB", team2, chess.B, chess.WHITE)
        blackA = ai.SolitaryAIHandler("blackA", team2, chess.A, chess.BLACK)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_4: all players are SingularAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_4_old(max_moves:int=500, depth=6, max_states=1000000, log_moves=False, log_stats=False):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.
        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class1 = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        eval_class2 = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        one_dic = {}
        one_dic[chess.A] = chess.WHITE
        one_dic[chess.B] = chess.BLACK

        two_dic = {}
        two_dic[chess.B] = chess.WHITE
        two_dic[chess.A] = chess.BLACK

        one = ai.SolitaryAI('WhiteOnA', board, True, chess.WHITE, chess.BLACK, eval_class1, max_depth=depth)
        two = ai.SolitaryAI('WhiteOnB', board, False, chess.BLACK, chess.WHITE, eval_class2, max_depth=depth)
        players = [one, two]

        # logging
        logging.info("play_4: all players are SolitaryAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play_solitary(board, players, max_moves, log_moves=log_moves)

    @staticmethod
    def play_5(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners vs. the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_5: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " position evaluation; team 2 players are the same ".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_6(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners vs the same. There are no special next depth functions. Uses random move reordering.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_6: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " position evaluation and random move reordering; team 2 players are the same".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_7(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners vs the same. Uses random move reordering. Team 2 (whiteB/blackA) use
        piece_drop_nxt_depth for depth argument.

        Expect Team 2 to win at sufficiently deep depth because of the trimming of branching factors.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_7: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " position evaluation and random move reordering; team 2 players are the same"
                     " but team 2 uses piece_drop_nxt_depth depth function".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_8(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a game of a Singlular/IndependentAI with Basic Evaluation, Iterative Deepening to depth, max_states,
        vs a Singular/IndependentAI with Position Evaluation, Interative Deepening to depth,
        max_states. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class_1 = chess.utility.BasicMaterialEvaluationBughouseBase()
        eval_class_2 = chess.utility.BasicPlusPositionEvalBughouseBase()
        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class_1, max_depth=depth, print_stats=log_stats_during)
        team2 = ai.SolitaryAI('Team2', board, False, chess.BLACK, chess.WHITE, eval_class_2, max_depth=depth, print_stats=log_stats_during)
        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        whiteB = ai.SolitaryAIHandler("whiteB", team2, chess.B, chess.WHITE)
        blackA = ai.SolitaryAIHandler("blackA", team2, chess.A, chess.BLACK)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_8: all players are SingularAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " team1 using basic material evaluation and team2 using"
                     " position evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_9(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Plus Position Plus Pocket Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners. There are no special next depth functions. Uses random move reordering.

        Expect position plus pocket value evaluation partners to win most games

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class_1 = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        eval_class_2 = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_9: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material plus position plus pocket value  evaluation and "
                     "random move reordering; team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with position evaluation, and random move reordering".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_10(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Plus Position Plus Pocket Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs Position Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, with drop piece next depth function. Uses random move reordering.

        Unsure of which team should win.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class_1 = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        eval_class_2 = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class_2, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class_1, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_10: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material plus position plus pocket value  evaluation and "
                     "random move reordering; team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with position evaluation, random move "
                     "reordering, and piece drop next depth function".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_11(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Material Evaluation with Iterative Deepening to depth, max_states,
        communicating partners, vs Position Evaluation with Iterative Deepening to depth, max_states,
        communicating partners.

        Team 2 should win because of Position Evaluation.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class1 = chess.utility.BasicMaterialEvaluationBughouseBase()
        eval_class2 = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class1, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class2, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class2, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class1, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_11: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation; "
                     " team 2 players are PartneredAI, "
                     "communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with position evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_12(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Position Evaluation with Iterative Deepening to depth, max_states,
        communicating partners, vs Basic Plus Position Plus Pocket Value Evaluation with Iterative Deepening to depth, max_states,
        communicating partners.

        Team 2 should have an advantage with Basic Material Plus Position Plus Pocket Evaluation.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class1 = chess.utility.BasicPlusPositionEvalBughouseBase()
        eval_class2 = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class1, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class2, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class2, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class1, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_12: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " position evaluation; "
                     " team 2 players are PartneredAI, "
                     "communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with basic plus position plus pocket value evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_13(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Plus Position Plus Pocket Value with Iterative Deepening to depth, max_states,
        communicating partners, vs Basic Plus Position Plus Pocket Value Evaluation with Iterative Deepening to depth, max_states,
        communicating partners, with drop piece next depth function.

        Unsure of which team should win.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_13: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic plus position plus pocket value evaluation; "
                     " team 2 players are PartneredAI, "
                     "communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with basic plus position plus pocket value evaluation, and with piece drop next depth".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_14(eval_class_num, max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of communicating partnered AIs using the given evaluation class with Iterative Deepening to depth, max_states,
        communicating partners, vs non-communicating partnerd AIs using the same given evaulation class with Iterative Deepening to depth, max_states,
        communicating partners, with drop piece next depth function.

        Unsure of which team should win.

        Eval classes:
        0. BasicMaterialEvaluation
        1. BasicPlusPositionEval
        2. BasicPlusPositionPlusPocketVal

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(), # don't use, oscillates
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        ]
        i = eval_class_num

        eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, evals[i], communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, evals[i], communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, evals[i], communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, evals[i], communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_14: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " eval class {ev}; "
                     " team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with eval class {ev}".format(md=depth, ms=max_states, ev=eval_class_num))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_15(eval_class_num, max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of communicating partnered AIs using the given evaluation class with Iterative Deepening to depth, max_states,
        communicating partners, vs non-communicating partnerd AIs using the same given evaulation class with Iterative Deepening to depth, max_states,
        communicating partners, with drop piece next depth function.

        Unsure of which team should win.

        Eval classes:
        0. BasicMaterialEvaluation
        1. BasicPlusPositionEval
        2. BasicPlusPositionPlusPocketVal

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(),
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        ]
        i = eval_class_num

        eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, evals[i], communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, evals[i], communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, evals[i], communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, evals[i], communicating=True, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_15: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " eval class {ev}; "
                     " team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with eval class {ev}".format(md=depth, ms=max_states, ev=eval_class_num))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_16(eval_class_num, pocket_val, diff_pos, comm, base_first, max_moves: int = 500, depth=4,
                max_states=1000000, log_moves=True,
                log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of communicating partnered AIs using the given evaluation class with Iterative Deepening to depth, max_states,
        communicating partners, vs non-communicating partnerd AIs using the same given evaulation class with Iterative Deepening to depth, max_states,
        communicating partners, with drop piece next depth function.
        Unsure of which team should win.
        Eval classes:
        0. BasicMaterialEvaluation
        1. BasicPlusPositionEval
        2. BasicPlusPositionPlusPocketVal
        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        base_eval = chess.utility.BasicPlusPositionEvalBughouseBase_Copy()
        evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(),  # don't use, oscillates
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
        ]
        evals[2].set_pocket_val(pocket_val)
        evals[3].set_pocket_val(pocket_val)

        if diff_pos:
            evals[1].set_diff_positions(diff_pos)
            evals[2].set_diff_positions(diff_pos)
            evals[4].set_diff_positions(diff_pos)

        i = eval_class_num

        if base_first:
            feval = base_eval
            seval = evals[i]
        else:
            feval = evals[i]
            seval = base_eval

        #eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, feval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, seval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, seval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, feval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_14: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " eval class {ev}; "
                     " team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with eval class {ev}".format(md=depth, ms=max_states, ev=eval_class_num))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_17(pocket_val, diff_pos, comm, base_first, max_moves: int = 500, depth=4,
                max_states=1000000, log_moves=True,
                log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of communicating partnered AIs using the given evaluation class with Iterative Deepening to depth, max_states,
        communicating partners, vs non-communicating partnerd AIs using the same given evaulation class with Iterative Deepening to depth, max_states,
        communicating partners, with drop piece next depth function.

        Unsure of which team should win.

        Eval classes:
        0. BasicMaterialEvaluation
        1. BasicPlusPositionEval
        2. BasicPlusPositionPlusPocketVal
        3. BasicPlusMobilityEvalBughouseBase
        4. BasicPlusPositionPlusMobilityEvalBughouseBase

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        # base_eval = chess.utility.BasicPlusPositionEvalBughouseBase_Copy()
        evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(),  # don't use, oscillates
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
        ]
        evals[2].set_pocket_val(pocket_val)
        evals[3].set_pocket_val(pocket_val)
        base_eval = evals[2]

        if diff_pos:
            evals[1].set_diff_positions(diff_pos)
            evals[2].set_diff_positions(diff_pos)
            evals[4].set_diff_positions(diff_pos)

        i = 3

        if base_first:
            feval = base_eval
            seval = evals[i]
            feval_str = "base_eval with pocket val " + pocket_val
            seval_str = "eval_class " + i
        else:
            feval = evals[i]
            seval = base_eval
            seval_str = "base_eval with pocket val " + pocket_val
            feval_str = "eval_class " + i

        eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, feval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=ai.AI.capture_drop_reorder)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, seval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=ai.AI.capture_drop_reorder)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, seval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=ai.AI.capture_drop_reorder)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, feval, communicating=comm, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=ai.AI.capture_drop_reorder)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_17: team 1 players are PartneredAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " capture_drop_reorder and eval [{fev_s}]; "
                     " team 2 players are PartneredAI,"
                     " using iterative deepening to max_depth"
                     " {md}/max_states {ms}, with capture_drop_reorder and eval [{sev_s}]. "
                     " both teams are either communicating or non-communicating according to "
                     " {comm}".format(md=depth, ms=max_states, comm=comm, fev_s=feval_str, sev_s=seval_str))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_18(diff_pos, base_first, smart_order, max_moves: int = 500, depth=4,
                max_states=1000000, log_moves=True,
                log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of communicating partnered AIs using the given evaluation class with Iterative Deepening to depth, max_states,
        communicating partners, vs non-communicating partnerd AIs using the same given evaulation class with Iterative Deepening to depth, max_states,
        communicating partners, with drop piece next depth function.

        Unsure of which team should win.

        Eval classes:
        0. BasicMaterialEvaluation
        1. BasicPlusPositionEval
        2. BasicPlusPositionPlusPocketVal

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        # base_eval = chess.utility.BasicPlusPositionEvalBughouseBase_Copy()
        evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(),  # don't use, oscillates
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
        ]
        base_eval = evals[2]

        if diff_pos:
            evals[1].set_diff_positions(diff_pos)
            evals[2].set_diff_positions(diff_pos)
            evals[4].set_diff_positions(diff_pos)

        i = 2

        if base_first:
            feval = base_eval
            seval = evals[i]
        else:
            feval = evals[i]
            seval = base_eval

        if smart_order:
            order = ai.AI.capture_drop_reorder
        else:
            order = ai.AI.rand_move_reorder

        eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, feval, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=order)
        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, seval, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=order)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, seval, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=order)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, feval, communicating=True, max_depth=depth,
                                iter_deep=True, max_states=max_states, print_stats=log_stats_during,
                                move_order_fn=order)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_14: team 1 players are PartneredAI, communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " eval class {ev}; "
                     " team 2 players are PartneredAI, "
                     "non-communicating, using iterative deepening to max_depth "
                     "{md}/max_states {ms}, with eval class {ev}".format(md=depth, ms=max_states, ev=i))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_humans(communicating:bool=False):
        """
        Play a synchronous game. Currently hard coded.

        :param max_moves: the maximum number of moves you would like to allow played
        :param communicating: if you would like to allow the agents to communicate with their partners
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicMaterialEvaluationBughouseBase()

        msg = ("Hello humans! You will be playing a game against to synchronous,\n"
            "non-communicating, partnered AIs. What does this mean? It means that\n"
            "this game will be played in a synchronous fashion, where, even though\n"
            "normally each board in bughouse can be played independently of the\n"
            "other, each player takes turns. The order of these turns is White-A,\n"
            "White-B, Black-A, and then Black-B. We understand that this can change\n"
            "how strategy in bughouse, and for that we apologize. This method is\n"
            "is necessary for more basic AIs to be able to play. We hope to have\n"
            "an asynchronous version in the future. Additionally, each non-human\n"
            "player is represented by an its own AI. And these AIs will not have\n"
            "the advantage of communicating amongst themselves like you will.\n"
        )
        print(msg)
        print("Human playing board B white, please enter you name:")
        human_white_B = input()
        print("Human playing board A black, please enter you name:")
        human_black_A = input()

        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating, max_depth=4)
        whiteB = HumanAgent("whiteB "+human_white_B, board, chess.B, chess.WHITE)
        blackA = HumanAgent("blackA "+human_black_A, board, chess.A, chess.BLACK)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating, max_depth=4)

        # logging
        logging.info("new game: synchronous, comm {comm}; whiteA {wA}, whiteB {wB}, blackA {bA}, blackB {bB}".format(comm=communicating,wA="PartneredAI",wB="human "+human_white_B,bA="human "+human_black_A,bB="PartneredAI"))

        players = [whiteA, whiteB, blackA, blackB]
        Runner.play(board, players)

    @staticmethod
    def play_humans_2(communicating:bool=False, depth: int=5, max_moves=500, log_moves=True, max_states: int=1000000, log_stats_during=False, log_stats_after=False):
        """
        Play a synchronous game. Currently hard coded.

        :param max_moves: the maximum number of moves you would like to allow played
        :param communicating: if you would like to allow the agents to communicate with their partners
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()

        msg = ("Hello humans! You will be playing a game against to synchronous\n"
            "non-communicating, partnered AIs. What does this mean? It means that\n"
            "this game will be played in a synchronous fashion, where, even though\n"
            "normally each board in bughouse can be played independently of the\n"
            "other, each player takes turns. The order of these turns is White-A,\n"
            "White-B, Black-A, and then Black-B. We understand that this can change\n"
            "how strategy in bughouse, and for that we apologize. This method is\n"
            "is necessary for more basic AIs to be able to play. We hope to have\n"
            "an asynchronous version in the future. Additionally, each non-human\n"
            "player is represented by an its own AI. And these AIs will not have\n"
            "the advantage of communicating amongst themselves like you will.\n"
        )
        print(msg)
        print("Human playing board B white, please enter you name:")
        human_white_B = input()
        print("Human playing board A black, please enter you name:")
        human_black_A = input()

        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        whiteB = HumanAgent("whiteB "+human_white_B, board, chess.B, chess.WHITE)
        blackA = HumanAgent("blackA "+human_black_A, board, chess.A, chess.BLACK)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)

        # logging
        logging.info("new game: comm {comm}; whiteA {wA}, whiteB {wB}, blackA {bA}, blackB {bB}"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " position evaluation, random move reordering, and piece_drop_nxt_depth depth function".format(comm=communicating,wA="PartneredAI",wB="human "+human_white_B,bA="human "+human_black_A,bB="PartneredAI", md=depth, ms=max_states))

        players = [whiteA, whiteB, blackA, blackB]
        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_rand_1(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs random agents as partners. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        # eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        eval_class = chess.utility.BasicMaterialEvaluationBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        whiteB = RandomAgent("whiteB", board, chess.B, chess.WHITE)
        blackA = RandomAgent("blackA", board, chess.A, chess.BLACK)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during, move_order_fn=ai.AI.rand_move_reorder, nxt_dep_func=ai.AI.piece_drop_nxt_depth)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_1: whiteA and blackB are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation vs whiteB and blackA that are random agents".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_rand_2(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs random agents as partners.
        There are no special next depth functions
        or move ordering functions.

        Expect position evaluation partners to win most games

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicMaterialEvaluationBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = RandomAgent("whiteB", board, chess.B, chess.WHITE)
        blackA = RandomAgent("blackA", board, chess.A, chess.BLACK)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_2: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation; team 2 players are Random Agent"
                     "".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_rand_3(max_moves: int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Postion Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs random agents as partners.
        There are no special next depth functions
        or move ordering functions.

        Expect position evaluation partners to win most games

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        whiteB = RandomAgent("whiteB", board, chess.B, chess.WHITE)
        blackA = RandomAgent("blackA", board, chess.A, chess.BLACK)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_2: team 1 players are PartneredAI, non-communicating, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " position evaluation; team 2 players are Random Agent"
                     "".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def sync_play_prescribed(wB_moves, bA_moves, max_moves: int=75, communicating: bool=False):
        """
        Play a synchronous game. Currently hard coded.

        The agents for whiteB and blackA have prescribed move orders, given by params
        wB_moves and bA_moves

        :param max_moves: the maximum number of moves you would like to allow played
        :param communicating: if you would like to allow the agents to communicate with their partners
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicMaterialEvaluationBughouseBase()
        whiteA = ai.PartneredAI("whiteA", board, chess.A, chess.WHITE, eval_class, communicating, max_depth=4)
        whiteB = PrescribedAgent("whiteB", board, chess.B, chess.WHITE, wB_moves)
        blackA = PrescribedAgent("blackA", board, chess.A, chess.BLACK, bA_moves)
        blackB = ai.PartneredAI("blackB", board, chess.B, chess.BLACK, eval_class, communicating, max_depth=4)
        players = [whiteA, whiteB, blackA, blackB]
        Runner.play(board, players, max_moves)


    @staticmethod
    def multirunner_1():
        """
        This was set up by Bryce for the explicit purpose of running multiple
        play functions one after the other in order to speed up and automate testing.
        Because of how logging works, need to split the log file afterwards.
        """
        logging.info("Running multirunner_1")
        # logging.info("Only running play_14() for utility evals "
        #              "BasicPlusPositionEvalBughouseBase, "
        #              "BasicPlusPositionPlusPocketValEvalBughouseBase, "
        #              "BasicPlusMobilityEvalBughouseBase, "
        #              "BasicPlusPositionPlusMobilityEvalBughouseBase")
        # logging.info("Running play_11()")
        # Runner.play_11()
        # logging.info("###########################################")
        # logging.info("Running play_12()")
        # Runner.play_12()
        # logging.info("###########################################")
        # logging.info("Running play_13()")
        # Runner.play_13()
        # logging.info("###########################################")
        # logging.info("Running play_14() with basic material evaluation")
        # Runner.play_14(0)
        logging.info("###########################################")
        # logging.info("Running play_14() with BasicPlusPositionEvalBughouseBase")
        # Runner.play_14(1)
        # logging.info("###########################################")
        # logging.info("Running play_14() with BasicPlusPositionPlusPocketValEvalBughouseBase")
        # Runner.play_14(2)
        # logging.info("###########################################")
        # logging.info("Running play_14() with BasicPlusMobilityEvalBughouseBase")
        # Runner.play_14(3)
        # logging.info("###########################################")
        logging.info("multirunner1_5: Only running play_14() for utility eval "
                    "BasicPlusPositionPlusMobilityEvalBughouseBaseBeale")
        logging.info("Running play_14() with BasicPlusPositionPlusMobilityEvalBughouseBase")
        Runner.play_14(4)
        # logging.info("###########################################")
        # logging.info("Only running play_14() for utility eval "
        #             "BasicPlusPositionPlusMobilityEvalBughouseBaseBeale")
        logging.info("###########################################")
        # logging.info("Running play_14() with BasicPlusPositionPlusMobilityEvalBughouseBaseBeale")
        # Runner.play_14(5)
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")

    @staticmethod
    def multirunner_2():
        """
        This was set up by Bryce for the explicit purpose of running multiple
        play functions one after the other in order to speed up and automate testing.
        Because of how logging works, need to split the log file afterwards.
        """
        logging.info("Running multirunner_2")
        logging.info("Running play_15() with basic material evaluation")
        Runner.play_15(0)
        logging.info("###########################################")
        logging.info("Running play_15() with basic plus position evaluation")
        Runner.play_15(1)
        logging.info("###########################################")
        logging.info("Running play_15() with basic plus position plus pocket value evaluation")
        Runner.play_15(2)
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")

    @staticmethod
    def multirunner_3(comm):
        """
        This was set up by Bryce for the explicit purpose of running multiple
        play functions one after the other in order to speed up and automate testing.
        Because of how logging works, need to split the log file afterwards.
        """
        logging.info("Running multirunner_3")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = .25, base first")
        Runner.play_16(2, 0.25, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = 0.5, base first")
        Runner.play_16(2, 0.5, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = 0.75, base first")
        Runner.play_16(2, 0.75, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = 1.5, base first")
        Runner.play_16(2, 1.5, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = .25, base second")
        #Runner.play_16(2, 0.25, False, comm, False)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = 0.5, base second")
        #Runner.play_16(2, 0.5, False, comm, False)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = 0.75, base second")
        #Runner.play_16(2, 0.75, False, comm, False)
        logging.info("###########################################")
        logging.info("Running play_16() communication=" + str(comm) + ", pocket_val = 1.5, base second")
        #Runner.play_16(2, 1.5, False, comm, False)
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")

    @staticmethod
    def multirunner_4(comm):
        """
        This was set up by Bryce for the explicit purpose of running multiple
        play functions one after the other in order to speed up and automate testing.
        Because of how logging works, need to split the log file afterwards.
        """
        logging.info("Running multirunner_4")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = .25, base first")
        Runner.play_17(0.25, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 0.5, base first")
        Runner.play_17(0.5, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 0.75, base first")
        Runner.play_17(0.75, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 1.5, base first")
        Runner.play_17(1.5, False, comm, True)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = .25, base second")
        Runner.play_17(0.25, False, comm, False)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 0.5, base second")
        Runner.play_17(0.5, False, comm, False)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 0.75, base second")
        Runner.play_17(0.75, False, comm, False)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 1.5, base second")
        Runner.play_17(1.5, False, comm, False)
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")

    @staticmethod
    def multirunner_5(comm):
        """
        This was set up by Bryce for the explicit purpose of running multiple
        play functions one after the other in order to speed up and automate testing.
        Because of how logging works, need to split the log file afterwards.
        """
        logging.info("Running multirunner_4")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = .25, base first smart reordering")
        Runner.play_18(False, False, True)
        logging.info("###########################################")
        logging.info("Running play_17() communication=" + str(comm) + ", pocket_val = 0.5, base first rand reordering")
        Runner.play_18(False, False, False)
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")


    @staticmethod
    def play_solitary_v_partner_beale(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class, max_depth=depth, print_stats=log_stats_during)

        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)

        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)

        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_4: all players are SingularAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_solitary_v_partner_basic(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionEvalBughouseBase()
        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class, max_depth=depth, print_stats=log_stats_during)

        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)

        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)

        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_4: all players are SingularAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_solitary_v_partner_pocket(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase()
        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class, max_depth=depth, print_stats=log_stats_during)

        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)

        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)

        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_4: all players are SingularAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_solitary_v_partner_mobility(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class = chess.utility.BasicPlusMobilityEvalBughouseBase()
        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class, max_depth=depth, print_stats=log_stats_during)

        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)

        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, eval_class, communicating=False, max_depth=depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)

        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_4: all players are SingularAI, using"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def play_solitary_v_solitary_beale_v_nonbeale(max_moves:int=500, depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of Basic Evaluation with Iterative Deepening to depth, max_states,
        non-communicating partners, vs the same. There are no special next depth functions
        or move ordering functions.

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        eval_class1 = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        eval_class2 = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase()

        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, eval_class1, max_depth=depth, print_stats=log_stats_during)
        team2 = ai.SolitaryAI('Team2', board, False, chess.BLACK, chess.WHITE, eval_class2, max_depth=depth, print_stats=log_stats_during)
        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        whiteB = ai.SolitaryAIHandler("whiteB", team2, chess.B, chess.WHITE)
        blackA = ai.SolitaryAIHandler("blackA", team2, chess.A, chess.BLACK)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)

        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("playing solitary v solitary with beale and nonbeale"
                     " iterative deepening to max_depth {md}/max_states {ms}, with"
                     " basic material evaluation".format(md=depth, ms=max_states))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def run_tests():
        Runner.play_solitary_v_partner_beale()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_partner_basic()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_partner_pocket()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_partner_mobility()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")

    @staticmethod
    def run_tests_solitary():
        Runner.play_solitary_v_solitary_beale_v_nonbeale()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_solitary_beale_v_nonbeale()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_solitary_beale_v_nonbeale()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_solitary_beale_v_nonbeale()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        Runner.play_solitary_v_solitary_beale_v_nonbeale()
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")

    @staticmethod
    def play_solitary_v_partner_2(solitary_eval_num, partner_eval_num, comm, max_moves:int=500, sol_depth=5, partner_depth=4, max_states=1000000, log_moves=True, log_stats_during=False, log_stats_after=True):
        """
        Plays a synchronous game of a solitary AI against partnered AIs that are communicating
        according to the value of {comm}. All AIs use iterative Deepening. The solitary AI
        goes to the depth prescribed by sol_depth/max_states. The partnered AIs go to the depth
        prescribed by partner_depth/max_states. There no special next depth or move ordering
        functions.

        0. BasicMaterialEvaluation
        1. BasicPlusPositionEval
        2. BasicPlusPositionPlusPocketVal
        3. BasicPlusMobilityEvalBughouseBase
        4. BasicPlusPositionPlusMobilityEvalBughouseBase
        5. BasicPlusPositionPlusMobilityEvalBughouseBaseBeale

        :param max_moves: the maximum number of moves you would like to allow played; default 500
        :param depth: the maximum depth to allow iterative deepening
        :param max_states: the number of states at which to quit iterative deepening search
        """
        board = variant.BughouseSuperBoard()
        # eval_class = chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()

        # evals for the solitary AI
        s_evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(),  # don't use, oscillates
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        ]
        # evals for partnered AIs
        p_evals = [
            chess.utility.BasicMaterialEvaluationBughouseBase(),  # don't use, oscillates
            chess.utility.BasicPlusPositionEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusPocketValEvalBughouseBase(),
            chess.utility.BasicPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBase(),
            chess.utility.BasicPlusPositionPlusMobilityEvalBughouseBaseBeale()
        ]
        i = solitary_eval_num
        j = partner_eval_num


        team1 = ai.SolitaryAI('Team1', board, True, chess.WHITE, chess.BLACK, s_evals[i], max_depth=sol_depth, print_stats=log_stats_during)

        whiteA = ai.SolitaryAIHandler("whiteA", team1, chess.A, chess.WHITE)
        blackB = ai.SolitaryAIHandler("blackB", team1, chess.B, chess.BLACK)

        whiteB = ai.PartneredAI("whiteB", board, chess.B, chess.WHITE, p_evals[j], communicating=True, max_depth=partner_depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)
        blackA = ai.PartneredAI("blackA", board, chess.A, chess.BLACK, p_evals[j], communicating=True, max_depth=partner_depth, iter_deep=True, max_states=max_states, print_stats=log_stats_during)

        players = [whiteA, whiteB, blackA, blackB]

        # logging
        logging.info("play_solitary_v_partner_2: team1 is a solitary AI, using iterative "
                     " deepening to max_depth {smd}/max_states {ms}, with eval [{fev_s}]. "
                     " team 2 players are partnered AIs using iterative deepening to "
                     " max_depth {pmd}/max_states {ms}, with eval [{sev_s}], and communicating "
                     " is {comm}.".format(smd=sol_depth, pmd=partner_depth, ms=max_states, fev_s=i, sev_s=j, comm=comm))

        Runner.play(board, players, max_moves, log_moves=log_moves, log_stats_after=log_stats_after)

    @staticmethod
    def multirunner_6():
        """
        This was set up by Bryce for the explicit purpose of running multiple
        play functions one after the other in order to speed up and automate testing.
        Because of how logging works, need to split the log file afterwards.
        """
        logging.info("Running multirunner_6")
        logging.info("Only running play_solitary_v_partner_2() with communicating "
                     "partnered AIs, depth of 4 for all players, and for utility evals "
                     "BasicPlusPositionEvalBughouseBase, "
                     "BasicPlusPositionPlusPocketValEvalBughouseBase, "
                     "BasicPlusMobilityEvalBughouseBase, "
                     "BasicPlusPositionPlusMobilityEvalBughouseBase, "
                     "BasicPlusPositionPlusMobilityEvalBughouseBaseBeale")
        logging.info("###########################################")
        logging.info("Running play_solitary_v_partner_2() with BasicPlusPositionEvalBughouseBase")
        Runner.play_solitary_v_partner_2(1, 1, True, sol_depth=4)
        logging.info("###########################################")
        logging.info("Running play_solitary_v_partner_2() with BasicPlusPositionPlusPocketValEvalBughouseBase")
        Runner.play_solitary_v_partner_2(2, 2, True, sol_depth=4)
        logging.info("###########################################")
        logging.info("Running play_solitary_v_partner_2() with BasicPlusMobilityEvalBughouseBase")
        Runner.play_solitary_v_partner_2(3, 3, True, sol_depth=4)
        logging.info("###########################################")
        logging.info("Running play_solitary_v_partner_2() with BasicPlusPositionPlusMobilityEvalBughouseBase")
        Runner.play_solitary_v_partner_2(4, 4, True, sol_depth=4)
        logging.info("###########################################")
        logging.info("Running play_solitary_v_partner_2() with BasicPlusPositionPlusMobilityEvalBughouseBaseBeale")
        Runner.play_solitary_v_partner_2(5, 5, True, sol_depth=4)
        logging.info("###########################################")
        logging.info("###########################################")
        logging.info("###########################################")


if __name__ == "__main__":
    # set the logging file
    logging.basicConfig(filename="logs/multirunner1_5.txt", level=logging.INFO)
    logging.info("Bryce's Linux Server Acct| Pypy v7.2.0")
    # logging.basicConfig(filename="logs/test/multirunner1_2.txt", level=logging.INFO)
    # logging.info("Bryce's Linux Server Acct | Pypy v7.2.0")
    # logging.basicConfig(filename="logs/test/play_compete.txt", level=logging.INFO)
    # logging.info("Liam's Computer | Pypy v7.2.0")
    # logging.basicConfig(filename="logs/multirunner5_1.txt", level=logging.INFO)
    # logging.info("Bryce's Linux Server Acct | Pypy v7.2.0")
    # set the random seed
    seed = int(time.time()) # want an integer
    # seed = 1575756777
    random.seed(seed)
    logging.info("random seed is {}".format(seed))
    Runner.multirunner_3(True)
    #Runner.run_tests_solitary()
    # s.sync_play()
    # s.play_humans()
    # s.sync_play_random()
    # Runner.play_1(log_moves=True, log_stats_during=False, depth=2, log_stats_after=True)
    # Runner.play_rand_1(log_moves=True, log_stats_during=True, depth=5, log_stats_after=True)
    # Runner.play_3(log_moves=True, log_stats_during=True)
    # Runner.play_comm(log_moves=False, log_stats_during=False)
    # Runner.play_half_comm(log_moves=False, log_stats_during=False)
    #Runner.play_compete(depth=4, log_moves=True, log_stats_during=True, log_stats_after=True)
    #Runner.play_4(log_moves=False, log_stats_during=False)
    # Runner.play_compete(depth=4, log_moves=True, log_stats_during=True, log_stats_after=True)
    # Runner.play_4(log_moves=False, log_stats_during=False)
    # Runner.play_compete(depth=4, log_moves=True, log_stats_during=True, log_stats_after=True)
    # Runner.play_4(log_moves=False, log_stats_during=False)
    #Runner.play_compete(depth=4, log_moves=True, log_stats_during=True, log_stats_after=True)
    #Runner.play_4(log_moves=False, log_stats_during=False)
    # Runner.play_comm(log_moves=True, log_stats_during=True)
    # Runner.play_half_comm(log_moves=True, log_stats_during=True)
    # Runner.sync_play_random(max_moves=500, max_depth=3)
    #Runner.play_4_old(depth=4)
    # Runner.play_6(log_moves=True, log_stats_during=False, log_stats_after=True, depth=2)
    # Runner.play_7(depth=4, log_stats_after=True, log_moves=True, log_stats_during=False)
    # Runner.play_humans_2(depth=5, log_stats_after=True)
    # Runner.play_8(depth=4, log_stats_after=True, log_stats_during=False, log_moves=True)
    # Runner.play_9(depth=4, log_stats_after=True, log_stats_during=False, log_moves=True)
    # Runner.play_10(depth=5, log_stats_after=True, log_stats_during=False, log_moves=True)
    # Runner.multirunner_5(True)
    # Runner.multirunner_1()
    # Runner.play_rand_1()
    # Runner.multirunner_4(False)
    # Runner.play_rand_1()
    # Runner.multirunner_1()
    # Runner.multirunner_5(True)
    # Runner.play_rand_1()
    # Runner.run_tests()
    # Runner.multirunner_6()
    Runner.multirunner_1()
