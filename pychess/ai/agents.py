#! /Users/bryce/bughouse-chess/bugenv/bin/python
# ../../bugenv/bin/python

import pychess
from pychess import ai as ai
from pychess import chess as chess
from chess import variant

# https://code.visualstudio.com/docs/python/debugging#_attach-to-a-local-script
import ptvsd

# 5678 is the default attach port in the VS Code debug configurations
print("Waiting for debugger attach")
ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
ptvsd.wait_for_attach()
breakpoint()

from typing import ClassVar, Callable, Dict, Generic, Hashable, Iterable, Iterator, List, Mapping, MutableSet, Optional, SupportsInt, Tuple, Type, TypeVar, Union

import asyncio
import sys
import threading
import re
import math

DEFAULT_DEPTH = 10
DEFAULT_MOVETIME = 1000 # in msecs

class SearchState:
    """
    Holds information about the state of Search according to the GUI and possibly the agent. What this all holds has not yet been decided. 

    This should be protected by a lock.

    As of right now, I think each player should get their own state.
    """

    def __init__(self, board_id: str, color: chess.Color):
        self.board_id = board_id
        self.color = color
        # defaults
        self.depth = DEFAULT_DEPTH
        self.ponder = False
        self.searchmoves = None
        self.wtime = math.inf
        self.btime = math.inf
        self.winc = 0 # maybe?
        self.binc = 0 # maybe?
        self.nodes = math.inf
        self.mate_in_moves = math.inf
        self.movetime = DEFAULT_MOVETIME
        self.infinite = True # if True, go until a stop command
        # has been issued; when a stop command is issued, set to False
        self.stop = False

    def set_ponder(self, ponder: bool):
        self.ponder = ponder

    def set_searchmoves(self, searchmoves: List[chess.Moves]):
        self.searchmoves = searchmoves.copy()
    
    def set_wtime(self, wtime: int):
        self.wtime = wtime

    def set_btime(self, btime: int):
        self.btime = btime

    def set_winc(self, winc: int):
        self.winc = winc

    def set_movestogo(self, movestogo: int):
        self.movestogo = movestogo
    
    def set_depth(self, depth: int):
        self.depth = depth

    def set_nodes(self, nodes: int):
        self.nodes = nodes

    def set_mate(self, moves: int):
        self.mate_in_moves = moves

    def set_movetime(self, movetime: int):
        self.movetime = movetime

    def set_infinite(self, infinite: bool):
        self.infinite = bool

    def stop(self):
        self.stop = True

class EngineHandler:
    """
    """

    def __init__(self, name: str, agents: List[str], author: str):
        """
        If there is only one agent in 'agents', we assume that it is an agent
        that will be playing as its own partner. If there are two agents, 
        an error will be thrown.
        """
        if len(agents) > 2 or len(agents) < 0:
            raise ValueError("Only one or two agents allowed")
        self.agent_aliases = agents
        self.name = name
        # self.lockA = threading.Lock()
        # self.lockB = threading.Lock()
        # self.boardA_CV = threading.Condition(self.lockA)
        # self.boardB_CV = threading.Condition(self.lockB)
        self.lock = threading.Lock()
        self.boardA_CV = threading.Condition(self.lock)
        self.boardB_CV = threading.Condition(self.lock)
        # self.b
        self.ais = ais
        self.author = author
        self.go = False # This defines whether 'go' has been communicated; set to True after 'go' has been communicated; reset to False after 'stop' has been communicated
        self.engine_state_a = SearchState("A", color) # TODO: figure this out
        self.engine_state_b = SearchState("B", not color)
        # self.engine_state 

        # other stuff
        self.generate_agents()

    def generate_agents(self):
        self.agents = list()
        for alias in self.agent_aliases:
            self.agents.append(find_agent(alias)(self.lock, self.engine_state)) # TODO: check for additional required initialization params
        pass

    @staticmethod
    def logandprint(msg, logfile):
        logfile.write(msg + '\n')
        print(msg, file=sys.stdout)

    def c_quit(self, *args):
        sys.exit(0)


    # def parse_xboard_commands(self):
    #     """
    #     parses xboard commands when received
    #     """
    #     filename = "mylog.txt"
    #     # TODO: fix broken regex strings; many are incomplete
    #     xboard_regex_patterns = [
    #         (r'xboard',self.c_xboard)
    #     ]
    #     compiled_patterns = [(re.compile(r),m) for (r,m) in xboard_regex_patterns]

    #     with open(filename, 'w') as mylog:
    #         while True:
    #             cmd = input()
    #             for (r,m) in compiled_patterns:
    #                 res = r.match(cmd)
    #                 if res:
    #                     m()

    def parse_xboard_commands(self, logfile="mylog.txt"):
        """
        xboard commands, especially the ones relating to bughouse are listed
        at http://home.hccnet.nl/h.g.muller/engine-intf.html
        """

        with open(logfile, 'w') as mylog:
            while True:
                cmd = input()
                mylog.write(cmd + '\n')
                if cmd == 'xboard':
                    pass
                elif cmd[:8] == 'protover':
                    EngineHandler.logandprint('feature myname="Liam"', mylog)
                    EngineHandler.logandprint('feature ping=1', mylog)
                    EngineHandler.logandprint('feature setboard=1', mylog)
                    #EngineHandler.logandprint('feature san=1', mylog)
                elif cmd[:4] == 'ping':
                    EngineHandler.logandprint('pong' + cmd[4:], mylog)
                elif cmd[:7] == 'variant':
                    self.variant = cmd[8:]
                    self.fen = EngineHandler.getFen(self.variant)
                # elif cmd[:8] == 'usermove':
                #     self.board.push(cmd[9:], )
                elif cmd == 'go':
                    move = self.minimax(self.board, 0, float('-Inf'), float('Inf'))[1]
                    self.board.push(move)
                    #self.board.push_san(move, myengine.get_board())
                    EngineHandler.logandprint('move ' + move.__str__(), mylog)
                    #EngineHandler.logandprint('move e2e4', mylog)
                elif cmd == 'quit':
                    sys.exit(0)
                elif cmd == 'random':
                    # according to the xboard documentation, this is a noop
                    pass 
                elif cmd == 'force':
                    # we're going to ignore this command
                    pass
                elif cmd == 'go':
                    pass
                elif cmd == 'playother':
                    pass
                elif cmd == 'white' or cmd == 'black':
                    # deprecated
                    pass
                elif cmd[:5] == 'level':
                    # to set time controls
                    pass
                elif cmd[:2] == 'st':
                    # to set time controls
                    pass
                elif cmd[:2] == 'sd':
                    # limit thinking to DEPTH ply, of the form 'sd DEPTH'
                    pass
                elif cmd[:3] == 'nps':
                    # something about not using wall-clock timing, but 
                    # counting the number of nodes it searches
                    pass
                elif cmd[:4] == 'time':
                    # a time thing
                    pass
                elif cmd[:4] == 'otim':
                    # an opponent time thing
                    pass
                elif is_move(cmd):
                    # if the command is a valid move, add that move
                    # TODO: make this method
                    pass
                elif cmd[:8] == 'usermove':
                    # I really don't understand what is going on in this one
                    pass
                elif cmd == '?':
                    # move immediately, if the engine is thinking it should
                    # move immediately; otherwise a no-op; permissible to ignore
                    pass
                elif cmd == 'draw':
                    # a draw has been offered, can except or ignore
                    pass
                elif cmd[:6] == 'result':
                    # sends a result at the end of the game that can be used for 
                    # learning
                    pass
                elif cmd[:8] == 'setboard':
                    # sets the board using a FEN
                    pass
                elif cmd == 'edit':
                    # deprecated
                    pass
                elif cmd == 'hint':
                    # we don't want to suggest a move to user
                    pass
                elif cmd == 'bk':
                    # user information; can ignore
                    pass 
                elif cmd == 'remove':
                    # user wants to undo a move
                    pass
                elif cmd == 'hard':
                    # turn on pondering; probably can ignore
                    pass
                elif cmd == 'easy':
                    # turn off pondering; probably can ignore
                    pass
                elif cmd == 'post':
                    # turn on thinking/pondering output
                    pass
                elif cmd == 'nopost':
                    # turn off thinking/pondering output
                    pass
                elif cmd == 'analyse':
                    # turn on analyze mode
                    pass
                elif cmd[:4] == 'name':
                    # informs engine of user name
                    pass
                elif cmd[:6] == 'rating':
                    pass
                elif cmd[:3] == 'ics':
                    # where the engine is playing
                    pass
                elif cmd == 'computer': 
                    # the opponent is also a computer chess engine
                    pass
                elif cmd == 'pause':
                    pass
                elif cmd == 'resume':
                    pass
                elif cmd[:6] == 'memory':
                    pass
                elif cmd[:5] == 'cores':
                    pass
                elif cmd[:7] == 'egtpath':
                    pass
                elif cmd[:6] == 'option':
                    pass
                elif cmd[:7] == 'exclude':
                    # excluding moves from root search
                    pass
                elif cmd[:7] == 'include':
                    # explicitly include moves in root search
                    pass
                elif cmd[:8] == 'setscore':
                    # I don't understand the manual on this one
                    pass
                elif cmd[:7] == 'partner':
                    # name of partner for future games
                    # if blank, no longer have a partner
                    pass
                elif cmd[:5] == 'ptell':
                    # partner told us something
                    pass 
                elif cmd[:7] == 'holding':
                    # what each player holds
                    pass





class CommChannel:
    """
    Objects of this class are to be used to communicate between partnered 
    AIs the pieces they wish to see captured (to benefit themselves) as well as 
    pieces they want protected... as well as the value or cost to them.

    This should be secured with a lock, as it is not threadsafe.

    self.please_capture: a dictionary of piece types with
    the value of their capture by the partner to the player.

    self.please_protect: a dictionary of piece types with the harm that would be done to the player if caught by the partner's opponent.
    """

    def __init__(self):
        pass

    def update_whole(self, _from: CommChannel):
        pass

    def set_please_capture(self, pairs: dict):
        for key in pairs:
            if not key in chess.PIECETYPES:
                raise ValueError("The provided key is not a valid piece type.")
            self.please_capture[key] = pairs[key]

    def set_please_protect(self, pairs: dict):
        for key in pairs:
            if not key in chess.PIECETYPES:
                raise ValueError("The provided key is not a valid piece type.")
            self.please_protect[key] = pairs[key]

    def get_please_capture(self):
        return self.please_capture.copy()

    def get_please_protect(self):
        return self.please_protect.copy()


class Agent(threading.Thread):
    """
    Acts as the agent for an AI.

    """

    def __init__(self, lock: threading.Lock, engine_state: EngineState, find_moves_event: threading.Event, board_id: str, color: chess.Color):
        """
        Assumption is that each agent is an individual player; agents
        handling both players should override this init.

        @params:
            - lock: the lock used to control access to the shared information (engine_state)
            - engine_state: a reference to the shared information
            - find_moves_event: an Event that signals when to search for moves on the board
            this agent plays on 
            - board_id: the string id of the board this agent will play on
            - color: the color of the player on the board represented by board_id
        """
        super().__init__()
        self.lock = lock
        self.engine_state = engine_state
        self.find_moves_event = find_moves_event
        self.board_id = board_id
        self.color = color
        # self.boardCV = boardCV
        
    def run(self):
        """
        Waits for the all-clear to make a play.
        """
        while True:
            self.find_moves_event.wait()
            pass
        # with :
        #     pass


class RandomAgent(Agent):
    """
    This is an agent that chooses the next move randomly.
    """
    alias = "random"

    pass

    def run(self):
        """
        Waits for the all-clear to make a play.
        """
        while True:
            self.find_moves_event.wait()
            pass
        # with :
        #     pass


class IndependentAgentSuper(Agent):

    def __init__(self, lock: threading.Lock, engine_state: EngineState, find_moves_event_A: threading.Event, find_moves_event_B: threading.Event, white_board_id: str):
        """
        Assumption is that each agent is both players

        @params:
            - lock: the lock used to control access to the shared information (engine_state)
            - engine_state: a reference to the shared information
            - find_moves_event_A: an Event that signals when to search for moves on board A
            - find_moves_event_B: an Event that signals when to search for moves on board B
            - white_board_id: the board id that this agent plays as white on (since each partnership 
            of one playing white and the other playing black)
        """
        super().__init__()
        self.lock = lock
        self.engine_state = engine_state
        self.find_moves_event_A = find_moves_event_A 
        self.find_moves_event_B = find_moves_event_B
        self.white_board_id = white_board_id
        # self.boardCV = boardCV


class IndependentSyncAgent(IndependentAgentSuper):
    alias = "ind_sync"
    pass


class IndependentAsyncAgent(IndependentAgentSuper):
    alias = "ind_async"
    pass 


class PartneredSyncQuietAgent(Agent):
    alias = "partnered_sync_quiet"
    pass 


class PartneredAsyncQuietAgent(Agent):
    alias = "partnered_async_quiet"
    pass 


class CommSuperAgent(Agent):
    """
    This super class handles the communication between two partner AIs.
    
    Each partner should instantiate a subclass of this class.

    self.board_id represents which board an instance of this class
        is playing on
    self.partner_board_id represents their partner's board id

    After instantiation, two threadsafe communication channels should be established.
    Each should be secured by the same lock. One communication channel should be 
    to communicate from this instance to our partner, "these are the pieces you should/should
    not capture and the pieces you should/should not allow your opponent to capture
    with weights". The other communication channel should be our partner communicating
    their preferences to us.
    """
    pass




class PartneredSyncCommAgent(CommSuperAgent):
    alias = "partnered_sync_comm"
    pass 


class PartneredAsyncCommAgent(CommSuperAgent):
    alias = "partnered_async_comm"
    pass


AGENTS = [
    RandomAgent,
    IndependentSyncAgent,
    IndependentAsyncAgent,
    PartneredSyncQuietAgent,
    PartneredAsyncQuietAgent,
    PartneredSyncCommAgent,
    PartneredAsyncCommAgent
]

def find_agent(name: str) -> Type[Agent]:
    for agent in AGENTS:
        if name == agent.alias:
            return agent
    raise ValueError("unsupported agent: {}".format(name))


"""
If we run this file, the __name__ becomes "__main__", and so this portion of 
code will run. This is useful for running an agent.

This bit of code might need to be abstracted to a different spot, but I am 
just messing around for the moment.

https://docs.python.org/3.7/tutorial/modules.html#executing-modules-as-scripts
"""
if __name__ == "__main__":
    # parse sys.argv to get the AIs that should be playing.
    # sys.argv
    name = "agent"
    agent1 = "random"
    agent2 = "random"
    eh = EngineHandler("agent", [agent1, agent2], "Bryce,Liam,Nathaniel")
    eh.parse_uci_commands()
