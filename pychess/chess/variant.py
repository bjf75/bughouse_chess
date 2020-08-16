# -*- coding: utf-8 -*-
#
# This file is part of the python-chess library.
# Copyright (C) 2016-2019 Niklas Fiekas <niklas.fiekas@backscattering.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Bryce's import
from pychess import chess as chess

import copy
import itertools
import traceback

from typing import Dict, Generic, Hashable, Iterable, Iterator, List, Optional, Tuple, Type, TypeVar, Union


class SuicideBoard(chess.Board):
    aliases = ["Suicide", "Suicide chess"]
    uci_variant = "suicide"
    xboard_variant = "suicide"

    tbw_suffix = ".stbw"
    tbz_suffix = ".stbz"
    tbw_magic = b"\x7b\xf6\x93\x15"
    tbz_magic = b"\xe4\xcf\xe7\x23"
    pawnless_tbw_suffix = ".gtbw"
    pawnless_tbz_suffix = ".gtbz"
    pawnless_tbw_magic = b"\xbc\x55\xbc\x21"
    pawnless_tbz_magic = b"\xd6\xf5\x1b\x50"
    connected_kings = True
    one_king = False
    captures_compulsory = True

    def pin_mask(self, color: chess.Color, square: chess.Square) -> chess.Bitboard:
        return chess.BB_ALL

    def _attacked_for_king(self, path: chess.Bitboard, occupied: chess.Bitboard) -> bool:
        return False

    def is_check(self) -> bool:
        return False

    def is_into_check(self, move: chess.Move) -> bool:
        return False

    def was_into_check(self) -> bool:
        return False

    def _material_balance(self) -> int:
        return (chess.popcount(self.occupied_co[self.turn]) -
                chess.popcount(self.occupied_co[not self.turn]))

    def is_variant_end(self) -> bool:
        return not all(has_pieces for has_pieces in self.occupied_co)

    def is_variant_win(self) -> bool:
        if not self.occupied_co[self.turn]:
            return True
        else:
            return self.is_stalemate() and self._material_balance() < 0

    def is_variant_loss(self) -> bool:
        if not self.occupied_co[self.turn]:
            return False
        else:
            return self.is_stalemate() and self._material_balance() > 0

    def is_variant_draw(self) -> bool:
        if not self.occupied_co[self.turn]:
            return False
        else:
            return self.is_stalemate() and self._material_balance() == 0

    def has_insufficient_material(self, color: chess.Color) -> bool:
        if self.occupied != self.bishops:
            return False

        # In a position with only bishops, check if all our bishops can be
        # captured.
        we_some_on_light = bool(self.occupied_co[color] & chess.BB_LIGHT_SQUARES)
        we_some_on_dark = bool(self.occupied_co[color] & chess.BB_DARK_SQUARES)
        they_all_on_dark = not (self.occupied_co[not color] & chess.BB_LIGHT_SQUARES)
        they_all_on_light = not (self.occupied_co[not color] & chess.BB_DARK_SQUARES)
        return (we_some_on_light and they_all_on_dark) or (we_some_on_dark and they_all_on_light)

    def generate_pseudo_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL,
                                    to_mask: chess.Bitboard = chess.BB_ALL) -> Iterator[chess.Move]:
        for move in super().generate_pseudo_legal_moves(from_mask, to_mask):
            # Add king promotions.
            if move.promotion == chess.QUEEN:
                yield chess.Move(move.from_square, move.to_square, chess.KING)

            yield move

    def generate_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL, to_mask: chess.Bitboard = chess.BB_ALL) -> \
    Iterator[chess.Move]:
        if self.is_variant_end():
            return

        # Generate captures first.
        found_capture = False
        for move in self.generate_pseudo_legal_captures():
            if chess.BB_SQUARES[move.from_square] & from_mask and chess.BB_SQUARES[move.to_square] & to_mask:
                yield move
            found_capture = True

        # Captures are mandatory. Stop here if any were found.
        if not found_capture:
            not_them = to_mask & ~self.occupied_co[not self.turn]
            for move in self.generate_pseudo_legal_moves(from_mask, not_them):
                if not self.is_en_passant(move):
                    yield move

    def is_legal(self, move: chess.Move) -> bool:
        if not super().is_legal(move):
            return False

        if self.is_capture(move):
            return True
        else:
            return not any(self.generate_pseudo_legal_captures())

    def _transposition_key(self) -> Hashable:
        if self.has_chess960_castling_rights():
            return (super()._transposition_key(), self.kings & self.promoted)
        else:
            return super()._transposition_key()

    def board_fen(self, promoted: Optional[bool] = None) -> str:
        if promoted is None:
            promoted = self.has_chess960_castling_rights()
        return super().board_fen(promoted=promoted)

    def status(self) -> chess.Status:
        status = super().status()
        status &= ~chess.STATUS_NO_WHITE_KING
        status &= ~chess.STATUS_NO_BLACK_KING
        status &= ~chess.STATUS_TOO_MANY_KINGS
        status &= ~chess.STATUS_OPPOSITE_CHECK
        return status


class GiveawayBoard(SuicideBoard):
    aliases = ["Giveaway", "Giveaway chess", "Give away", "Give away chess"]
    uci_variant = "giveaway"
    xboard_variant = "giveaway"

    tbw_suffix = ".gtbw"
    tbz_suffix = ".gtbz"
    tbw_magic = b"\xbc\x55\xbc\x21"
    tbz_magic = b"\xd6\xf5\x1b\x50"
    pawnless_tbw_suffix = ".stbw"
    pawnless_tbz_suffix = ".stbz"
    pawnless_tbw_magic = b"\x7b\xf6\x93\x15"
    pawnless_tbz_magic = b"\xe4\xcf\xe7\x23"

    def is_variant_win(self) -> bool:
        return not self.occupied_co[self.turn] or self.is_stalemate()

    def is_variant_loss(self) -> bool:
        return False

    def is_variant_draw(self) -> bool:
        return False


class AntichessBoard(GiveawayBoard):
    aliases = ["Antichess", "Anti chess", "Anti"]
    uci_variant = "antichess"  # Unofficial
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"

    def __init__(self, fen: Optional[str] = starting_fen, chess960: bool = False) -> None:
        super().__init__(fen, chess960=chess960)

    def reset(self) -> None:
        super().reset()
        self.castling_rights = chess.BB_EMPTY


class AtomicBoard(chess.Board):
    aliases = ["Atomic", "Atom", "Atomic chess"]
    uci_variant = "atomic"
    xboard_variant = "atomic"

    tbw_suffix = ".atbw"
    tbz_suffix = ".atbz"
    tbw_magic = b"\x55\x8d\xa4\x49"
    tbz_magic = b"\x91\xa9\x5e\xeb"
    connected_kings = True
    one_king = True

    def is_variant_end(self) -> bool:
        return not all(self.kings & side for side in self.occupied_co)

    def is_variant_win(self) -> bool:
        return bool(self.kings and not self.kings & self.occupied_co[not self.turn])

    def is_variant_loss(self) -> bool:
        return bool(self.kings and not self.kings & self.occupied_co[self.turn])

    def has_insufficient_material(self, color: chess.Color) -> bool:
        # Remaining material does not matter if opponent's king is already
        # exploded.
        if not (self.occupied_co[not color] & self.kings):
            return False

        # Bare king can not mate.
        if not (self.occupied_co[color] & ~self.kings):
            return True

        # As long as the opponent's king is not alone, there is always a chance
        # their own pieces explode next to it.
        if self.occupied_co[not color] & ~self.kings:
            # Unless there are only bishops that cannot explode each other.
            if self.occupied == self.bishops | self.kings:
                if not (self.bishops & self.occupied_co[chess.WHITE] & chess.BB_DARK_SQUARES):
                    return not (self.bishops & self.occupied_co[chess.BLACK] & chess.BB_LIGHT_SQUARES)
                if not (self.bishops & self.occupied_co[chess.WHITE] & chess.BB_LIGHT_SQUARES):
                    return not (self.bishops & self.occupied_co[chess.BLACK] & chess.BB_DARK_SQUARES)
            return False

        # Queen or pawn (future queen) can give mate against bare king.
        if self.queens or self.pawns:
            return False

        # Single knight, bishop or rook cannot mate against bare king.
        if chess.popcount(self.knights | self.bishops | self.rooks) == 1:
            return True

        # Two knights cannot mate against bare king.
        if self.occupied == self.knights | self.kings:
            return chess.popcount(self.knights) <= 2

        return False

    def _attacked_for_king(self, path: chess.Bitboard, occupied: chess.Bitboard) -> bool:
        # Can castle onto attacked squares if they are connected to the
        # enemy king.
        enemy_kings = self.kings & self.occupied_co[not self.turn]
        for enemy_king in chess.scan_forward(enemy_kings):
            path &= ~chess.BB_KING_ATTACKS[enemy_king]

        return super()._attacked_for_king(path, occupied)

    def _kings_connected(self) -> bool:
        white_kings = self.kings & self.occupied_co[chess.WHITE]
        black_kings = self.kings & self.occupied_co[chess.BLACK]
        return any(chess.BB_KING_ATTACKS[sq] & black_kings for sq in chess.scan_forward(white_kings))

    def _push_capture(self, move: chess.Move, capture_square: chess.Square, piece_type: chess.PieceType,
                      was_promoted: bool) -> None:
        # Explode the capturing piece.
        self._remove_piece_at(move.to_square)

        # Explode all non pawns around.
        explosion_radius = chess.BB_KING_ATTACKS[move.to_square] & ~self.pawns
        for explosion in chess.scan_forward(explosion_radius):
            self._remove_piece_at(explosion)

        # Destroy castling rights.
        self.castling_rights &= ~explosion_radius

    def is_check(self) -> bool:
        return not self._kings_connected() and super().is_check()

    def was_into_check(self) -> bool:
        return not self._kings_connected() and super().was_into_check()

    def is_into_check(self, move: chess.Move) -> bool:
        self.push(move)
        was_into_check = self.was_into_check()
        self.pop()
        return was_into_check

    def is_legal(self, move: chess.Move) -> bool:
        if self.is_variant_end():
            return False

        if not self.is_pseudo_legal(move):
            return False

        self.push(move)
        legal = bool(self.kings) and not self.is_variant_win() and (self.is_variant_loss() or not self.was_into_check())
        self.pop()

        return legal

    def is_stalemate(self) -> bool:
        return not self.is_variant_loss() and super().is_stalemate()

    def generate_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL, to_mask: chess.Bitboard = chess.BB_ALL) -> \
    Iterator[chess.Move]:
        for move in self.generate_pseudo_legal_moves(from_mask, to_mask):
            if self.is_legal(move):
                yield move

    def status(self) -> chess.Status:
        status = super().status()
        status &= ~chess.STATUS_OPPOSITE_CHECK
        if self.turn == chess.WHITE:
            status &= ~chess.STATUS_NO_WHITE_KING
        else:
            status &= ~chess.STATUS_NO_BLACK_KING
        return status


class KingOfTheHillBoard(chess.Board):
    aliases = ["King of the Hill", "KOTH"]
    uci_variant = "kingofthehill"
    xboard_variant = "kingofthehill"  # Unofficial

    tbw_suffix = None
    tbz_suffix = None
    tbw_magic = None
    tbz_magic = None

    def is_variant_end(self) -> bool:
        return bool(self.kings & chess.BB_CENTER)

    def is_variant_win(self) -> bool:
        return bool(self.kings & self.occupied_co[self.turn] & chess.BB_CENTER)

    def is_variant_loss(self) -> bool:
        return bool(self.kings & self.occupied_co[not self.turn] & chess.BB_CENTER)

    def has_insufficient_material(self, color: chess.Color) -> bool:
        return False


class RacingKingsBoard(chess.Board):
    aliases = ["Racing Kings", "Racing", "Race", "racingkings"]
    uci_variant = "racingkings"
    xboard_variant = "racingkings"  # Unofficial
    starting_fen = "8/8/8/8/8/8/krbnNBRK/qrbnNBRQ w - - 0 1"

    tbw_suffix = None
    tbz_suffix = None
    tbw_magic = None
    tbz_magic = None

    def __init__(self, fen: Optional[str] = starting_fen, chess960: bool = False) -> None:
        super().__init__(fen, chess960=chess960)

    def reset(self) -> None:
        self.set_fen(type(self).starting_fen)

    def _gives_check(self, move: chess.Move) -> bool:
        self.push(move)
        gives_check = self.is_check()
        self.pop()
        return gives_check

    def is_legal(self, move: chess.Move) -> bool:
        return super().is_legal(move) and not self._gives_check(move)

    def generate_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL, to_mask: chess.Bitboard = chess.BB_ALL) -> \
    Iterator[chess.Move]:
        for move in super().generate_legal_moves(from_mask, to_mask):
            if not self._gives_check(move):
                yield move

    def is_variant_end(self) -> bool:
        if not self.kings & chess.BB_RANK_8:
            return False

        if self.turn == chess.WHITE or self.kings & self.occupied_co[chess.BLACK] & chess.BB_RANK_8:
            return True

        black_kings = self.kings & self.occupied_co[chess.BLACK]
        if not black_kings:
            return True

        black_king = chess.msb(black_kings)

        # White has reached the backrank. The game is over if black can not
        # also reach the backrank on the next move. Check if there are any
        # safe squares for the king.
        targets = chess.BB_KING_ATTACKS[black_king] & chess.BB_RANK_8
        return all(self.attackers_mask(chess.WHITE, target) for target in chess.scan_forward(targets))

    def is_variant_draw(self) -> bool:
        in_goal = self.kings & chess.BB_RANK_8
        return all(in_goal & side for side in self.occupied_co)

    def is_variant_loss(self) -> bool:
        return self.is_variant_end() and not self.kings & self.occupied_co[self.turn] & chess.BB_RANK_8

    def is_variant_win(self) -> bool:
        return self.is_variant_end() and bool(self.kings & self.occupied_co[self.turn] & chess.BB_RANK_8)

    def has_insufficient_material(self, color: chess.Color) -> bool:
        return False

    def status(self) -> chess.Status:
        status = super().status()
        if self.is_check():
            status |= chess.STATUS_RACE_CHECK
        if self.turn == chess.BLACK and all(self.occupied_co[co] & self.kings & chess.BB_RANK_8 for co in chess.COLORS):
            status |= chess.STATUS_RACE_OVER
        if self.pawns:
            status |= chess.STATUS_RACE_MATERIAL
        for color in chess.COLORS:
            if chess.popcount(self.occupied_co[color] & self.knights) > 2:
                status |= chess.STATUS_RACE_MATERIAL
            if chess.popcount(self.occupied_co[color] & self.bishops) > 2:
                status |= chess.STATUS_RACE_MATERIAL
            if chess.popcount(self.occupied_co[color] & self.rooks) > 2:
                status |= chess.STATUS_RACE_MATERIAL
            if chess.popcount(self.occupied_co[color] & self.queens) > 1:
                status |= chess.STATUS_RACE_MATERIAL
        return status


class HordeBoard(chess.Board):
    aliases = ["Horde", "Horde chess"]
    uci_variant = "horde"
    xboard_variant = "horde"  # Unofficial
    starting_fen = "rnbqkbnr/pppppppp/8/1PP2PP1/PPPPPPPP/PPPPPPPP/PPPPPPPP/PPPPPPPP w kq - 0 1"

    tbw_suffix = None
    tbz_suffix = None
    tbw_magic = None
    tbz_magic = None

    def __init__(self, fen: Optional[str] = starting_fen, chess960: bool = False) -> None:
        super().__init__(fen, chess960=chess960)

    def reset(self) -> None:
        self.set_fen(type(self).starting_fen)

    def is_variant_end(self) -> bool:
        return not all(has_pieces for has_pieces in self.occupied_co)

    def is_variant_draw(self) -> bool:
        return not self.occupied

    def is_variant_loss(self) -> bool:
        return bool(self.occupied) and not self.occupied_co[self.turn]

    def is_variant_win(self) -> bool:
        return bool(self.occupied) and not self.occupied_co[not self.turn]

    def has_insufficient_material(self, color: chess.Color) -> bool:
        # TODO: Could detect some cases where the Horde can no longer mate.
        return False

    def status(self) -> chess.Status:
        status = super().status()
        status &= ~chess.STATUS_NO_WHITE_KING

        if chess.popcount(self.occupied_co[chess.WHITE]) <= 36:
            status &= ~chess.STATUS_TOO_MANY_WHITE_PIECES
            status &= ~chess.STATUS_TOO_MANY_WHITE_PAWNS

        if not self.pawns & chess.BB_RANK_8 and not self.occupied_co[chess.BLACK] & self.pawns & chess.BB_RANK_1:
            status &= ~chess.STATUS_PAWNS_ON_BACKRANK

        if self.occupied_co[chess.WHITE] & self.kings:
            status |= chess.STATUS_TOO_MANY_KINGS

        return status


ThreeCheckBoardT = TypeVar("ThreeCheckBoardT", bound="ThreeCheckBoard")


class _ThreeCheckBoardState(Generic[ThreeCheckBoardT], chess._BoardState["ThreeCheckBoardT"]):
    def __init__(self, board: "ThreeCheckBoardT") -> None:
        super().__init__(board)
        self.remaining_checks_w = board.remaining_checks[chess.WHITE]
        self.remaining_checks_b = board.remaining_checks[chess.BLACK]

    def restore(self, board: "ThreeCheckBoardT") -> None:
        super().restore(board)
        board.remaining_checks[chess.WHITE] = self.remaining_checks_w
        board.remaining_checks[chess.BLACK] = self.remaining_checks_b


class ThreeCheckBoard(chess.Board):
    aliases = ["Three-check", "Three check", "Threecheck", "Three check chess", "3-check"]
    uci_variant = "3check"
    xboard_variant = "3check"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 3+3 0 1"

    tbw_suffix = None
    tbz_suffix = None
    tbw_magic = None
    tbz_magic = None

    def __init__(self, fen: Optional[str] = starting_fen, chess960: bool = False) -> None:
        self.remaining_checks = [3, 3]
        super().__init__(fen, chess960=chess960)

    def reset_board(self) -> None:
        super().reset_board()
        self.remaining_checks[chess.WHITE] = 3
        self.remaining_checks[chess.BLACK] = 3

    def clear_board(self) -> None:
        super().clear_board()
        self.remaining_checks[chess.WHITE] = 3
        self.remaining_checks[chess.BLACK] = 3

    def _board_state(self: ThreeCheckBoardT) -> _ThreeCheckBoardState[ThreeCheckBoardT]:
        return _ThreeCheckBoardState(self)

    def push(self, move: chess.Move) -> None:
        super().push(move)
        if self.is_check():
            self.remaining_checks[not self.turn] -= 1

    def has_insufficient_material(self, color: chess.Color) -> bool:
        # Any remaining piece can give check.
        return not (self.occupied_co[color] & ~self.kings)

    def set_epd(self, epd: str) -> Dict[str, Union[None, str, int, float, chess.Move, List[chess.Move]]]:
        parts = epd.strip().rstrip(";").split(None, 5)

        # Parse ops.
        if len(parts) > 5:
            operations = self._parse_epd_ops(parts.pop(), lambda: type(self)(" ".join(parts) + " 0 1"))
            parts.append(str(operations["hmvc"]) if "hmvc" in operations else "0")
            parts.append(str(operations["fmvn"]) if "fmvn" in operations else "1")
            self.set_fen(" ".join(parts))
            return operations
        else:
            self.set_fen(epd)
            return {}

    def set_fen(self, fen: str) -> None:
        parts = fen.split()

        # Extract check part.
        if len(parts) >= 7 and parts[6][0] == "+":
            check_part = parts.pop(6)
            try:
                w, b = check_part[1:].split("+", 1)
                wc, bc = 3 - int(w), 3 - int(b)
            except ValueError:
                raise ValueError("invalid check part in lichess three-check fen: {}".format(repr(check_part)))
        elif len(parts) >= 5 and "+" in parts[4]:
            check_part = parts.pop(4)
            try:
                w, b = check_part.split("+", 1)
                wc, bc = int(w), int(b)
            except ValueError:
                raise ValueError("invalid check part in three-check fen: {}".format(repr(check_part)))
        else:
            wc, bc = 3, 3

        # Set fen.
        super().set_fen(" ".join(parts))
        self.remaining_checks[chess.WHITE] = wc
        self.remaining_checks[chess.BLACK] = bc

    def epd(self, shredder: bool = False, en_passant: str = "legal", promoted: Optional[bool] = None,
            **operations: Union[None, str, int, float, chess.Move, Iterable[chess.Move]]) -> str:
        epd = [super().epd(shredder=shredder, en_passant=en_passant, promoted=promoted),
               "{:d}+{:d}".format(max(self.remaining_checks[chess.WHITE], 0),
                                  max(self.remaining_checks[chess.BLACK], 0))]
        if operations:
            epd.append(self._epd_operations(operations))
        return " ".join(epd)

    def is_variant_end(self) -> bool:
        return any(remaining_checks <= 0 for remaining_checks in self.remaining_checks)

    def is_variant_draw(self) -> bool:
        return self.remaining_checks[chess.WHITE] <= 0 and self.remaining_checks[chess.BLACK] <= 0

    def is_variant_loss(self) -> bool:
        return self.remaining_checks[not self.turn] <= 0 < self.remaining_checks[self.turn]

    def is_variant_win(self) -> bool:
        return self.remaining_checks[self.turn] <= 0 < self.remaining_checks[not self.turn]

    def is_irreversible(self, move: chess.Move) -> bool:
        if super().is_irreversible(move):
            return True

        self.push(move)
        gives_check = self.is_check()
        self.pop()
        return gives_check

    def _transposition_key(self) -> Hashable:
        return (super()._transposition_key(),
                self.remaining_checks[chess.WHITE], self.remaining_checks[chess.BLACK])

    def copy(self: ThreeCheckBoardT, stack: Union[bool, int] = True) -> ThreeCheckBoardT:
        board = super().copy(stack=stack)
        board.remaining_checks = self.remaining_checks.copy()
        return board

    def mirror(self: ThreeCheckBoardT) -> ThreeCheckBoardT:
        board = super().mirror()
        #board.remaining_checks[chess.WHITE] = self.remaining_checks[chess.BLACK]
        #board.remaining_checks[chess.BLACK] = self.remaining_checks[chess.WHITE]
        return board


CrazyhouseBoardT = TypeVar("CrazyhouseBoardT", bound="CrazyhouseBoard")


class _CrazyhouseBoardState(Generic[CrazyhouseBoardT], chess._BoardState["CrazyhouseBoardT"]):
    def __init__(self, board: "CrazyhouseBoardT") -> None:
        super().__init__(board)
        self.pockets_w = board.pockets[chess.WHITE].copy()
        self.pockets_b = board.pockets[chess.BLACK].copy()

    def restore(self, board: "CrazyhouseBoardT") -> None:
        super().restore(board)
        board.pockets[chess.WHITE] = self.pockets_w.copy()
        board.pockets[chess.BLACK] = self.pockets_b.copy()


CrazyhousePocketT = TypeVar("CrazyhousePocketT", bound="CrazyhousePocket")


class CrazyhousePocket:

    def __init__(self, symbols: Iterable[str] = "") -> None:
        self.pieces = {}  # type: Dict[chess.PieceType, int]
        for symbol in symbols:
            self.add(chess.PIECE_SYMBOLS.index(symbol))

    def add(self, pt: chess.PieceType) -> None:
        self.pieces[pt] = self.pieces.get(pt, 0) + 1

    def remove(self, pt: chess.PieceType) -> None:
        self.pieces[pt] -= 1

    def count(self, piece_type: chess.PieceType) -> int:
        return self.pieces.get(piece_type, 0)

    def reset(self) -> None:
        self.pieces.clear()

    def __str__(self) -> str:
        return "".join(chess.piece_symbol(pt) * self.count(pt) for pt in reversed(chess.PIECE_TYPES))

    def __len__(self) -> int:
        return sum(self.pieces.values())

    def __repr__(self) -> str:
        return "CrazyhousePocket('{}')".format(str(self))

    def copy(self: CrazyhousePocketT) -> CrazyhousePocketT:
        pocket = type(self)()
        pocket.pieces = copy.copy(self.pieces)
        return pocket


class CrazyhouseBoard(chess.Board):
    aliases = ["Crazyhouse", "Crazy House", "House", "ZH"]
    uci_variant = "crazyhouse"
    xboard_variant = "crazyhouse"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1"

    tbw_suffix = None
    tbz_suffix = None
    tbw_magic = None
    tbz_magic = None

    def __init__(self, fen: Optional[str] = starting_fen, chess960: bool = False) -> None:
        self.pockets = [CrazyhousePocket(), CrazyhousePocket()]
        super().__init__(fen, chess960=chess960)

    def reset_board(self) -> None:
        super().reset_board()
        self.pockets[chess.WHITE].reset()
        self.pockets[chess.BLACK].reset()

    def clear_board(self) -> None:
        super().clear_board()
        self.pockets[chess.WHITE].reset()
        self.pockets[chess.BLACK].reset()

    def _board_state(self: CrazyhouseBoardT) -> _CrazyhouseBoardState[CrazyhouseBoardT]:
        return _CrazyhouseBoardState(self)

    def push(self, move: chess.Move) -> None:
        super().push(move)
        if move.drop:
            self.pockets[not self.turn].remove(move.drop)

    def _push_capture(self, move: chess.Move, capture_square: chess.Square, piece_type: chess.PieceType,
                      was_promoted: bool) -> None:
        if was_promoted:
            self.pockets[self.turn].add(chess.PAWN)
        else:
            self.pockets[self.turn].add(piece_type)

    def can_claim_fifty_moves(self) -> bool:
        return False

    def is_seventyfive_moves(self) -> bool:
        return False

    def is_irreversible(self, move: chess.Move) -> bool:
        return self._reduces_castling_rights(move)

    def _transposition_key(self) -> Hashable:
        return (super()._transposition_key(),
                self.promoted,
                str(self.pockets[chess.WHITE]), str(self.pockets[chess.BLACK]))

    def legal_drop_squares_mask(self) -> chess.Bitboard:
        king = self.king(self.turn)
        if king is None:
            return ~self.occupied

        king_attackers = self.attackers_mask(not self.turn, king)

        if not king_attackers:
            return ~self.occupied
        elif chess.popcount(king_attackers) == 1:
            return chess.BB_BETWEEN[king][chess.msb(king_attackers)] & ~self.occupied
        else:
            return chess.BB_EMPTY

    def legal_drop_squares(self) -> chess.SquareSet:
        return chess.SquareSet(self.legal_drop_squares_mask())

    def is_pseudo_legal(self, move: chess.Move) -> bool:
        if move.drop and move.from_square == move.to_square:
            return (
                    move.drop != chess.KING and
                    not chess.BB_SQUARES[move.to_square] & self.occupied and
                    not (move.drop == chess.PAWN and chess.BB_SQUARES[move.to_square] & chess.BB_BACKRANKS) and
                    self.pockets[self.turn].count(move.drop) > 0)
        else:
            return super().is_pseudo_legal(move)

    def is_legal(self, move: chess.Move) -> bool:
        if move.drop:
            return self.is_pseudo_legal(move) and bool(
                self.legal_drop_squares_mask() & chess.BB_SQUARES[move.to_square])
        else:
            return super().is_legal(move)

    def generate_pseudo_legal_drops(self, to_mask: chess.Bitboard = chess.BB_ALL) -> Iterator[chess.Move]:
        for to_square in chess.scan_forward(to_mask & ~self.occupied):
            for pt, count in self.pockets[self.turn].pieces.items():
                if count and (pt != chess.PAWN or not chess.BB_BACKRANKS & chess.BB_SQUARES[to_square]):
                    yield chess.Move(to_square, to_square, drop=pt)

    def generate_legal_drops(self, to_mask: chess.Bitboard = chess.BB_ALL) -> Iterator[chess.Move]:
        return self.generate_pseudo_legal_drops(to_mask=self.legal_drop_squares_mask() & to_mask)

    def generate_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL, to_mask: chess.Bitboard = chess.BB_ALL) -> \
    Iterator[chess.Move]:
        return itertools.chain(
            super().generate_legal_moves(from_mask, to_mask),
            self.generate_legal_drops(from_mask & to_mask))

    def parse_san(self, san: str) -> chess.Move:
        if "@" in san:
            uci = san.rstrip("+# ")
            if uci[0] == "@":
                uci = "P" + uci
            move = chess.Move.from_uci(uci)
            if not self.is_legal(move):
                raise ValueError("illegal drop san: {} in {}".format(repr(san), self.fen()))
            return move
        else:
            return super().parse_san(san)

    def has_insufficient_material(self, color: chess.Color) -> bool:
        # In practise no material can leave the game, but this is easy to
        # implement anyway. Note that bishops can be captured and put onto
        # a different color complex.
        return (
                chess.popcount(self.occupied) + sum(len(pocket) for pocket in self.pockets) <= 3 and
                not self.pawns and
                not self.rooks and
                not self.queens and
                not any(pocket.count(chess.PAWN) for pocket in self.pockets) and
                not any(pocket.count(chess.ROOK) for pocket in self.pockets) and
                not any(pocket.count(chess.QUEEN) for pocket in self.pockets))

    def set_fen(self, fen: str) -> None:
        position_part, info_part = fen.split(None, 1)

        # Transform to lichess-style ZH FEN.
        if position_part.endswith("]"):
            if position_part.count("/") != 7:
                raise ValueError("expected 8 rows in position part of zh fen: {}", format(repr(fen)))
            position_part = position_part[:-1].replace("[", "/", 1)

        # Split off pocket part.
        if position_part.count("/") == 8:
            position_part, pocket_part = position_part.rsplit("/", 1)
        else:
            pocket_part = ""

        # Parse pocket.
        white_pocket = CrazyhousePocket(c.lower() for c in pocket_part if c.isupper())
        black_pocket = CrazyhousePocket(c for c in pocket_part if not c.isupper())

        # Set FEN and pockets.
        super().set_fen(position_part + " " + info_part)
        self.pockets[chess.WHITE] = white_pocket
        self.pockets[chess.BLACK] = black_pocket

    def board_fen(self, promoted: Optional[bool] = None) -> str:
        if promoted is None:
            promoted = True
        return super().board_fen(promoted=promoted)

    def epd(self, shredder: bool = False, en_passant: str = "legal", promoted: Optional[bool] = None,
            **operations: Union[None, str, int, float, chess.Move, Iterable[chess.Move]]) -> str:
        epd = super().epd(shredder=shredder, en_passant=en_passant, promoted=promoted)
        board_part, info_part = epd.split(" ", 1)
        return "{}[{}{}] {}".format(board_part, str(self.pockets[chess.WHITE]).upper(), str(self.pockets[chess.BLACK]),
                                    info_part)

    def copy(self: CrazyhouseBoardT, stack: Union[bool, int] = True) -> CrazyhouseBoardT:
        board = super().copy(stack=stack)
        #board.pockets[chess.WHITE] = self.pockets[chess.WHITE].copy()
        #board.pockets[chess.BLACK] = self.pockets[chess.BLACK].copy()
        return board

    def mirror(self: CrazyhouseBoardT) -> CrazyhouseBoardT:
        board = super().mirror()
        #board.pockets[chess.WHITE] = self.pockets[chess.BLACK].copy()
        #board.pockets[chess.BLACK] = self.pockets[chess.WHITE].copy()
        return board

    def status(self) -> chess.Status:
        status = super().status()

        if chess.popcount(self.pawns) + self.pockets[chess.WHITE].count(chess.PAWN) + self.pockets[chess.BLACK].count(
                chess.PAWN) <= 16:
            status &= ~chess.STATUS_TOO_MANY_BLACK_PAWNS
            status &= ~chess.STATUS_TOO_MANY_WHITE_PAWNS

        if chess.popcount(self.occupied) + len(self.pockets[chess.WHITE]) + len(self.pockets[chess.BLACK]) <= 32:
            status &= ~chess.STATUS_TOO_MANY_BLACK_PIECES
            status &= ~chess.STATUS_TOO_MANY_WHITE_PIECES

        return status


BughouseSuperBoardT = TypeVar("BughouseSuperBoardT", bound="BughouseSuperBoard")
BughouseBaseBoardT = TypeVar("BughouseBaseBoardT", bound="BughouseBaseBoardT")
BughousePocketT = TypeVar("BughousePocketT", bound="BughousePocket")


class BughousePocket:
    UNICODE_PIECE_SYMBOLS = {
        "R": u"♖", "r": u"♜",
        "N": u"♘", "n": u"♞",
        "B": u"♗", "b": u"♝",
        "Q": u"♕", "q": u"♛",
        "K": u"♔", "k": u"♚",
        "P": u"♙", "p": u"♟",
    }

    PIECE_NUM_LETTERS = {
        1: "p", 2: "n", 3: "b",
        4: "r", 5: "q", 6: "k"
    }

    PIECE_LETTERS_NUM = {
        "p": 1, "P": 1,
        "n": 2, "N": 2,
        "b": 3, "B": 3,
        "r": 4, "R": 4,
        "q": 5, "Q": 5,
        "k": 6, "K": 6
    }

    # the maximum possible amount of any piece that can be in a pocket
    # in any board instance, likely less; but this is the absolute most
    MAX_POS = {
        chess.KING: 0,
        chess.QUEEN: 4,
        chess.BISHOP: 8,
        chess.ROOK: 8,
        chess.PAWN: 32,
        chess.KNIGHT: 8
    }

    def __init__(self, symbols: Iterable[str] = "") -> None:
        self.pieces = {}  # type: Dict[chess.PieceType, int]
        for p in chess.PIECE_TYPES:
            # initialize all pieces (except king) to 0; important for the check in remove
            self.pieces[p] = 0
        del self.pieces[chess.KING]
        for symbol in symbols:
            self.add(chess.PIECE_SYMBOLS.index(symbol))

    def unicode(self, is_white):
        pocket_str = ""
        for piece, num in self.pieces.items():
            if is_white:
                piece_str = self.PIECE_NUM_LETTERS[piece].upper()
            else:
                piece_str = self.PIECE_NUM_LETTERS[piece]
            pocket_str += (self.UNICODE_PIECE_SYMBOLS[piece_str] + " ") * num
        return pocket_str

    def add(self, pt: chess.PieceType) -> None:
        self.pieces[pt] = self.pieces.get(pt, 0) + 1
        if self.pieces[pt] > self.MAX_POS[pt]:
            raise ValueError("can't have {0} pieces of {1}".format(self.pieces[pt] + 1, self.PIECE_NUM_LETTERS[pt]))

    def size(self):
        return len(self.pieces)

    def remove(self, pt: chess.PieceType) -> None:
        if self.pieces.get(pt, 0) == 0:
            raise ValueError("can't have less than 0 pieces in a pocket")
        self.pieces[pt] -= 1

    def count(self, piece_type: chess.PieceType) -> int:
        return self.pieces.get(piece_type, 0)

    def reset(self) -> None:
        self.pieces.clear()

    def __str__(self) -> str:
        return "".join(chess.piece_symbol(pt) * self.count(pt) for pt in reversed(chess.PIECE_TYPES))

    def __len__(self) -> int:
        return sum(self.pieces.values())

    def __repr__(self) -> str:
        return "BughousePocket('{}')".format(str(self))

    def copy(self: BughousePocketT) -> BughousePocketT:
        pocket = type(self)()
        # pocket.pieces = dict()
        pocket.pieces = copy.copy(self.pieces)
        return pocket

    def diff(self, other: BughousePocketT) -> BughousePocketT:
        """
        Returns a new pocket where the number ocrresponding to the pieces are the difference between other and self.
        Other must have at least all of the pieces in self.
        :param other:
        :return:
        """
        new_pocket = BughousePocket()
        for p in chess.PIECE_TYPES:
            if not (p in self.pieces) and not (p in other.pieces):
                new_pocket.pieces[p] = 0
            elif not (p in self.pieces):
                new_pocket.pieces[p] = other.pieces[p]
            else:
                new_pocket.pieces[p] = other.pieces[p] - self.pieces[p]
        return new_pocket

    def same_as(self, string: str):
        """
        Returns true if the string is the same as
        this. That is, every letter in the string corresponds
        to one instance of a piece in self. 

        Example:
        string = "nn"
        self has 2 knights
        return True

        Example:
        string = "qnpp"
        self has 3 pawns and a knight
        return False

        Example:
        string = "hello world"
        raises ValueError because 'h' is not a valid piece type representation

        :param string: the string representation of a pocket to check against
        :raise ValueError: if a letter in string is not a valid letter or is a king
        """
        pieces_c = copy.copy(self.pieces)
        for l in string:
            if l not in self.PIECE_LETTERS_NUM:
                raise ValueError("{0} is not a valid piece type letter representation".format(l))
            elif l not in pieces_c or pieces_c[l] == 0:
                # incorrect amount of piece type l
                return False
            else: 
                pieces_c[l] -= 1
        if len(pieces_c) == 0:
            return True 
        return False


class _BughouseBaseBoardState(Generic[BughouseBaseBoardT], chess._BoardState[BughouseBaseBoardT]):
    """ I believe everything in here is correct, but, I 
    might be missing something that we should be doing.

    TODO: We should really add a __hash__() function in order to check 
    whether two states are the same. However, there are some issues with trying to
    do this that would result in some massive refactoring. Firstly, the Python standard
    requires that (and for good reason) only immutable objects implement __hash__(),
    because otherwise, if it can be mutated, then something that was put in a hash
    bucket could end up being in the wrong hashbucket if something mutates it in the future.
    And as of right now, _BughouseBaseBoard is mutable because of 1) the pockets and 2)
    the Bughouse BaseBoard it holds is also mutable. In fact, the only classes that implement the
    __hash__() function in the original python-chess code are Move and Piece.
    """

    def __init__(self, board: BughouseBaseBoardT) -> None:
        super().__init__(board)
        self.pockets_w = board.pockets[chess.WHITE].copy()
        self.pockets_b = board.pockets[chess.BLACK].copy()
        self.pushed_pieces = board.pushed_pieces.copy()

    def restore(self, board: BughouseBaseBoardT) -> None:
        # if len(board.pockets[chess.BLACK]) > 1:
        #     breakpoint()
        super().restore(board)
        board.pockets[chess.WHITE] = self.pockets_w.copy()
        board.pockets[chess.BLACK] = self.pockets_b.copy()
        board.pushed_pieces = self.pushed_pieces.copy()


class BughouseBaseBoard(chess.Board):
    name = "orig"
    aliases = ["Bughouse", "Bug House", "Siamese chess", "Siamese",
               "tandem chess", "tandem", "bug"]
    uci_variant = "bughouse"  # I'm assuming this is true; need to check
    xboard_variant = "bughouse"  # I'm assuming this is true; need to check
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1"
    # this is based on bfen in the BPGN standard; however, I am using the [] convention for
    # piece pocket from crazyboard instead of the bfen convention of just using another
    # slash and putting the pocket pieces after that, because the [] is clearer

    tbw_suffix = None
    tbz_suffix = None
    tbw_magic = None
    tbz_magic = None
    one_king = True

    # TODO:
    # Need to fix reset() to include changes to turns
    #   and do something with castling rights
    # Need to check on what this 'stack' attribute is
    # need to fix clear() to include changes to turns 
    #   and do something with castling rights
    # 

    # pockets[WHITE] and pockets[BLACK] represent this board's pockets,
    # the other board's pockets are not directly accessible, but can be pushed to
    def __init__(self, board_id: str, fen: Optional[str] = starting_fen, chess960: bool = False) -> None:
        self.pockets = [BughousePocket(), BughousePocket()]
        super().__init__(fen, chess960=chess960)
        self.board_id = board_id
        self.opposite_board_id = chess.opposite_bughouse_board_id(board_id)
        self.pushed_pieces = list()
        # Required, immediately call set_super_board

    def set_super_board(self, super_board):
        self.super_board = super_board

    def reset_board(self) -> None:
        super().reset_board()
        self._reset_pockets()

    def clear_board(self) -> None:
        super().clear_board()
        self._reset_pockets()
        # TODO: something with clear_stack

    def _reset_pockets(self) -> None:
        self.pockets[chess.WHITE].reset()
        self.pockets[chess.BLACK].reset()

    def _board_state(self: BughouseBaseBoardT) -> _BughouseBaseBoardState[BughouseBaseBoardT]:
        return _BughouseBaseBoardState(self)

    def push(self, move: chess.Move, pocket_pushing: bool=False) -> None:
        super().push(move, pocket_pushing)
        if move.drop:
            self.pockets[not self.turn].remove(move.drop)  # so, this needs to stay as 'not self.turn' because
            # super().push(move) switches the turn before returning

    def pop(self, pocket_popping: bool=False) -> None:
        if pocket_popping:
            pc = self.pushed_pieces.pop()
            if pc:
                self.super_board.rm_from_pocket(pc, self.opposite_board_id,
                                                self.turn)  # we use self.turn
        mv = super().pop()

    def _push_no_capture(self, pocket_pushing: bool=False):
        """
        This should be called whenever returning without using _push_capture
        Used to signal that this was a move without capture, for capture stack
        :return: None
        """
        if pocket_pushing:
            self.pushed_pieces.append(None)

    def _push_capture(self, move: chess.Move, capture_square: chess.Square, piece_type: chess.PieceType, was_promoted: bool, pocket_pushing: bool=False) -> None:
        """
        This should only be called on the turn of the color that captures; 
        Thus, the piece being captured is the opposite color of self.turn;
        This is also the color of the partner that is getting the piece on the other board;
        """
        if was_promoted:
            piece_type = chess.PAWN
        if pocket_pushing:
            self.pushed_pieces.append(piece_type)
            self.super_board.push_to_pocket(piece_type, self.opposite_board_id, color=not self.turn)

    def add_to_pocket(self, piece_type: chess.PieceType, color: chess.Color) -> None:
        """
        Adds piece_type to color's pocket
        """
        self.pockets[color].add(piece_type)

    def rm_from_pocket(self, piece_type: chess.PieceType, color: chess.Color) -> None:
        """
        Removes piece_type from color's pocket. If there are
        no pieces of piece_typeconnected_kings = {bool} False in color's pocket, throws a
        value error
        """
        self.pockets[color].remove(piece_type)

    def get_pocket(self, color: chess.Color):
        """
        Returns the pocket of the specified color
        """
        return self.pockets[color]

    def set_pocket(self, color: chess.Color, pocket: dict):
        """
        This is a dangerous method. Only use on a copy of the board of interest,
        and reset after (just incase you use want to use the previous value).

        This sets the dict representing the pocket for color to pocket.
        """
        self.pockets[color] = pocket

    def can_claim_fifty_moves(self) -> bool:
        return False

    def is_seventyfive_moves(self) -> bool:
        return False

    def is_irreversible(self, move: chess.Move) -> bool:
        return self._reduces_castling_rights(move)

    def _transposition_key(self) -> Hashable:
        return (super()._transposition_key(),
                self.promoted,
                str(self.pockets[chess.WHITE]), str(self.pockets[chess.BLACK]))

    def legal_drop_squares_mask(self) -> chess.Bitboard:
        king = self.king(self.turn)
        if king is None:
            return ~self.occupied

        king_attackers = self.attackers_mask(not self.turn, king)

        if not king_attackers:
            return ~self.occupied
        elif chess.popcount(king_attackers) == 1:
            return chess.BB_BETWEEN[king][chess.msb(king_attackers)] & ~self.occupied
        else:
            return chess.BB_EMPTY

    def legal_drop_squares(self) -> chess.SquareSet:
        return chess.SquareSet(self.legal_drop_squares_mask())

    def is_pseudo_legal(self, move: chess.Move) -> bool:
        if move.drop and move.from_square == move.to_square:
            return (
                    move.drop != chess.KING and
                    not chess.BB_SQUARES[move.to_square] & self.occupied and
                    not (move.drop == chess.PAWN and chess.BB_SQUARES[move.to_square] & chess.BB_BACKRANKS) and
                    self.pockets[self.turn].count(move.drop) > 0)
        else:
            return super().is_pseudo_legal(move)

    def is_legal(self, move: chess.Move) -> bool:
        if move.drop:
            return self.is_pseudo_legal(move) and bool(
                self.legal_drop_squares_mask() & chess.BB_SQUARES[move.to_square])
        else:
            return super().is_legal(move)

    def generate_pseudo_legal_drops(self, to_mask: chess.Bitboard = chess.BB_ALL) -> Iterator[chess.Move]:
        for to_square in chess.scan_forward(to_mask & ~self.occupied):
            for pt, count in self.pockets[self.turn].pieces.items():
                if count and (pt != chess.PAWN or not chess.BB_BACKRANKS & chess.BB_SQUARES[to_square]):
                    yield chess.Move(to_square, to_square, drop=pt)

    def generate_legal_drops(self, to_mask: chess.Bitboard = chess.BB_ALL) -> Iterator[chess.Move]:
        return self.generate_pseudo_legal_drops(to_mask=self.legal_drop_squares_mask() & to_mask)

    def generate_legal_moves(self, from_mask: chess.Bitboard = chess.BB_ALL, to_mask: chess.Bitboard = chess.BB_ALL) -> \
    Iterator[chess.Move]:
        return itertools.chain(
            super().generate_legal_moves(from_mask, to_mask),
            self.generate_legal_drops(from_mask & to_mask))

    def parse_san(self, san: str) -> chess.Move:
        if "@" in san:
            uci = san.rstrip("+# ")
            if uci[0] == "@":
                uci = "P" + uci
            move = chess.Move.from_uci(uci)
            if not self.is_legal(move):
                raise ValueError("illegal drop san: {} in {}".format(repr(san), self.fen()))
            return move
        else:
            return super().parse_san(san)

    def has_insufficient_material(self, color: chess.Color) -> bool:
        return (
                chess.popcount(self.occupied) + sum(len(pocket) for pocket in self.pockets) <= 3 and
                not self.pawns and
                not self.rooks and
                not self.queens and
                not any(pocket.count(chess.PAWN) for pocket in self.pockets) and
                not any(pocket.count(chess.ROOK) for pocket in self.pockets) and
                not any(pocket.count(chess.QUEEN) for pocket in self.pockets))

    def set_fen(self, fen: str) -> None:
        position_part, info_part = fen.split(None, 1)

        # Transform to lichess-style ZH FEN.
        if position_part.endswith("]"):
            if position_part.count("/") != 7:
                raise ValueError("expected 8 rows in position part of zh fen: {}", format(repr(fen)))
            position_part = position_part[:-1].replace("[", "/", 1)

        # Split off pocket part.
        if position_part.count("/") == 8:
            position_part, pocket_part = position_part.rsplit("/", 1)
        else:
            pocket_part = ""

        # Parse pocket.
        white_pocket = BughousePocket(c.lower() for c in pocket_part if c.isupper())
        black_pocket = BughousePocket(c for c in pocket_part if not c.isupper())

        # Set FEN and pockets.
        super().set_fen(position_part + " " + info_part)
        self.pockets[chess.WHITE] = white_pocket
        self.pockets[chess.BLACK] = black_pocket

    def board_fen(self, *, promoted: Optional[bool] = None) -> str:
        if promoted is None:
            promoted = True
        return super().board_fen(promoted=promoted)

    def epd(self, shredder: bool = False, en_passant: str = "legal", promoted: Optional[bool] = None,
            **operations: Union[None, str, int, float, chess.Move, Iterable[chess.Move]]) -> str:
        epd = super().epd(shredder=shredder, en_passant=en_passant, promoted=promoted)
        board_part, info_part = epd.split(" ", 1)
        print(info_part)
        return "{}[{}{}] {}".format(board_part, str(self.pockets[chess.WHITE]).upper(), str(self.pockets[chess.BLACK]),
                                    info_part)

    def copy(self: BughouseBaseBoardT, *, stack: Union[bool, int] = True) \
            -> BughouseBaseBoardT:
        board = super().copy(stack=stack)
        board.pockets[chess.WHITE] = self.pockets[chess.WHITE].copy()
        board.pockets[chess.BLACK] = self.pockets[chess.BLACK].copy()
        board.pushed_pieces = self.pushed_pieces.copy()
        board.board_id = self.board_id
        board.opposite_board_id = self.opposite_board_id
        # Immediately use set_super_board()
        return board

    def _copy_base_code(self: BughouseBaseBoardT, stack: Union[bool, int] = True):
        # Baseboard
        """Creates a copy of the board."""
        board = type(self)(None)

        board.pawns = self.pawns
        board.knights = self.knights
        board.bishops = self.bishops
        board.rooks = self.rooks
        board.queens = self.queens
        board.kings = self.kings

        board.occupied_co[chess.WHITE] = self.occupied_co[chess.WHITE]
        board.occupied_co[chess.BLACK] = self.occupied_co[chess.BLACK]
        board.occupied = self.occupied
        board.promoted = self.promoted

        # return board

        # Board
        """
        Creates a copy of the board.

        Defaults to copying the entire move stack. Alternatively, *stack* can
        be ``False``, or an integer to copy a limited number of moves.
        """
        # board = super().copy()

        board.chess960 = self.chess960

        board.ep_square = self.ep_square
        board.castling_rights = self.castling_rights
        board.turn = self.turn
        board.fullmove_number = self.fullmove_number
        board.halfmove_clock = self.halfmove_clock

        if stack:
            stack = len(self.move_stack) if stack is True else stack
            board.move_stack = [copy.copy(move) for move in self.move_stack[-stack:]]
            board._stack = self._stack[-stack:]

        return board

    def unicode(self, *, invert_color: bool = False, borders: bool = False) -> str:
        board_str = super().unicode()
        white_pockets = self.pockets[0].unicode(True)
        black_pockets = self.pockets[1].unicode(False)

        return board_str + '\n' + white_pockets + '|' + black_pockets

    # def mirror(self: CrazyhouseBoardT) -> CrazyhouseBoardT:
    #     board = super().mirror()
    #     board.pockets[chess.WHITE] = self.pockets[chess.BLACK].copy()
    #     board.pockets[chess.BLACK] = self.pockets[chess.WHITE].copy()
    #     return board

    def status(self) -> chess.Status:
        status = super().status()
        if chess.popcount(self.pawns) + self.pockets[chess.WHITE].count(chess.PAWN) + self.pockets[chess.BLACK].count(
                chess.PAWN) <= 16:
            status &= ~chess.STATUS_TOO_MANY_BLACK_PAWNS
            status &= ~chess.STATUS_TOO_MANY_WHITE_PAWNS

        if chess.popcount(self.occupied) + len(self.pockets[chess.WHITE]) + len(self.pockets[chess.BLACK]) <= 32:
            status &= ~chess.STATUS_TOO_MANY_BLACK_PIECES
            status &= ~chess.STATUS_TOO_MANY_WHITE_PIECES

        return status

    def pocket_size(self):
        return self.pockets[0].size() + self.pockets[1].size()

    def is_game_over(self, *, claim_draw=False):
        """
        Check for all of these
        """
        # Seventyfive-move rule.
        if self.is_seventyfive_moves():
            return "Reached seventy-five moves"

        # Insufficient material.
        if self.is_insufficient_material():
            return "Insufficient material"

        # Stalemate or checkmate.
        if not any(self.generate_legal_moves()):
            return "stalemate/checkmate"

        if claim_draw:
            # Claim draw, including by three-fold repetition.
            res = self.can_claim_draw()
            if res:
                return "claim draw"
            else:
                return res
        else:
            # Five-fold repetition.
            res = self.is_fivefold_repetition()
            if res:
                return "fivefold repetition"
            else:
                return res

    def is_repetition(self, count=3) -> bool:
        """
        Tries to fix the issue with the existing is_repetition function.

        Specifically, the existing is_repetition function uses 'switchyard' to 
        keep track of the moves that they 
        """
        # Fast check, based on occupancy only.
        maybe_repetitions = 1
        for state in reversed(self._stack):
            if state.occupied == self.occupied:
                maybe_repetitions += 1
                if maybe_repetitions >= count:
                    break
        if maybe_repetitions < count:
            return False

        # Check full replay.
        transposition_key = self._transposition_key()

        # try:
        peek_idx = -1 # the index of the move we are peeking
        while True:
            if count <= 1:
                return True

            if len(self.move_stack) < count - 1:
                break

            move = self.move_stack[peek_idx]
            peek_idx -= 1

            if self.is_irreversible(move):
                break

            if self._transposition_key() == transposition_key:
                count -= 1
        # except:


        return False


class _BughouseSuperBoardState(Generic[BughouseSuperBoardT], chess._BoardState[BughouseSuperBoardT]):
    """TODO: I'm not sure at all what to do here yet.
    As I understand, we can't use super() because _BoardState
    is for a single board. I believe that it makes more sense
    to hold two separate _BughouseBaseBoardState 's, but I am
    unsure of that as well right now.
    """

    def __init__(self, board: BughouseSuperBoardT) -> None:
        # super().__init__(board) # I think this is wrong
        # I think the following are right, but I don't know
        # what to do with them
        self.boardA = board.boardA
        self.boardB = board.boardB
        pass

    def restore(self, board: BughouseSuperBoardT) -> None:
        # super().restore(board)# I think this is wrong
        # I think the following are right, but I don't know
        # what to do with them
        # board.boardA = self.boardA
        # board.boardB = self.boardB
        pass


class BughouseSuperBoard(chess.Board):
    """ The BughouseSuperBoard contains two separate BughouseBaseBoard (s)
    """
    BOARD_A = "A"
    BOARD_B = "B"

    aliases = ["Bughouse", "Bug House", "Siamese chess", "Siamese",
               "tandem chess", "tandem", "bug", "bughouse"]
    uci_variant = "bughouse"  # I'm assuming this is true; need to check
    xboard_variant = "bughouse"  # I'm assuming this is true; need to check
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1 | rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1"
    # this is based on bfen in the BPGN standard; however, I am using the [] convention for
    # piece pocket from crazyboard instead of the bfen convention of just using another
    # slash and putting the pocket pieces after that, because the [] is clearer
    starting_board_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[]|rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[]"

    # will probably have a move stack in this class
    # that will need to be cleared with clear_stack
    # TODO: implement a super move_stack and super _stack

    def __init__(self, fen: Optional[str] = starting_board_fen, chess960: bool = False) -> None:
        # TODO: get fens working
        # if (fen != starting_fen or chess960):
        #     boardA_fen, boardB_fen = self._split_starting_fens(fen)
        # else:
        #     boardA_fen = BughouseBaseBoard.starting_fen
        #     boardB_fen = BughouseBaseBoard.starting_fen
        self.occupied_co = [0, 0]  # This is set in the normal base board __init__ call
        self.ep_square = None

        self.boardA = BughouseBaseBoard(board_id=chess.A)  # , fen = boardA_fen)
        self.boardB = BughouseBaseBoard(board_id=chess.B)  # , fen = boardB_fen)

        self.boardA.set_super_board(self)
        self.boardB.set_super_board(self)

        self.board_push_pop_stack = list()

        if fen is None:
            self._clear_board()
        elif fen == self.starting_board_fen:
            self._reset_board()
        else:
            self._set_board_fen(fen)

    def get_base_board(self, board_id: str):
        if board_id == self.BOARD_A:
            return self.boardA
        elif board_id == self.BOARD_B:
            return self.boardB
        else:
            raise ValueError("Invalid board string")

    # def _split_starting_fens(self, fen: str = starting_fen) -> Tuple[str,str]:
    #     pass # TODO:

    def to_unicode(self):
        return self.boardA.unicode(invert_color=True) + '\n\n' + self.boardB.unicode(invert_color=True)

    def unicode_ext(self, invert_color: bool=False, borders: bool=False, labels: bool=False,
                    play_info: Tuple = None, pockets: bool=False):
        """
        Returns a string representation of the super board with Unicode pieces.
        Useful for pretty-printing to a terminal.

        Ext: extended to support displaying both boards with pockets in a nice way.
        - also extended to support displaying additional information provided
        by args.

        TODO: consider flipping board B vertically and horizontal

        :param invert_color: Invert color of the Unicode pieces.
        :param borders: Show borders and a coordinate margin.
        :param labels: Show board labels
        :param play_info: a tuple of the color and board_id of the player and their move;
             in the form (color, board_id, move)
        """
        builder = []
        a_rank = 7  # decrement
        b_rank = 0  # increment; only to be used if we flip horizontally and vertically

        if play_info:
            c, b, m = play_info
            color = "white" if c else "black"
            builder.append("{0} {1} played {2}\n".format(color, b, m.uci()))

        if labels and not borders:
            builder.append("Board A          Board B \n")
        elif labels and borders:
            builder.append("  Board A            Board B \n")

        while a_rank >= 0:
            if borders:
                builder.append("  ")
                builder.append("-" * 17)  # was 17, this might be the wrong amount
                builder.append("  ")
                builder.append("-" * 17)
                builder.append("\n")

                builder.append(chess.RANK_NAMES[a_rank])  # originally rank_index
                builder.append(" ")

            for file_index in range(8):
                square_index = chess.square(file_index, a_rank)  # originally rank_index

                if borders:
                    builder.append("|")
                elif file_index > 0:
                    builder.append(" ")

                piece = self.boardA.piece_at(square_index)

                if piece:
                    builder.append(piece.unicode_symbol(invert_color=invert_color))
                else:
                    builder.append(u"·")

            if borders:
                builder.append("|")

            builder.append("  ")

            for file_index in range(8):
                square_index = chess.square(file_index, a_rank)  # prob needs to be changed to
                # b_rank if we flip

                if borders:
                    builder.append("|")
                elif file_index > 0:
                    builder.append(" ")

                piece = self.boardB.piece_at(square_index)

                if piece:
                    builder.append(piece.unicode_symbol(invert_color=invert_color))
                else:
                    builder.append(u"·")

            if borders:
                builder.append("|")

            if borders or a_rank > 0:  # was rank_index; might need to change
                builder.append("\n")

            a_rank -= 1
            b_rank += 1

        if borders:
            builder.append("  ")
            builder.append("-" * 17)  # was 17, this might be the wrong amount
            builder.append("  ")
            builder.append("-" * 17)
            builder.append("\n")
            builder.append("   a b c d e f g h    a b c d e f g h")

        builder.append("\n")

        if pockets:
            builder.append("white A pocket: [")
            builder.append(self.boardA.get_pocket(chess.WHITE).unicode(chess.WHITE))
            builder.append("]\n")
            builder.append("white B pocket: [")
            builder.append(self.boardB.get_pocket(chess.WHITE).unicode(chess.WHITE))
            builder.append("]\n")
            builder.append("black A pocket: [")
            builder.append(self.boardA.get_pocket(chess.BLACK).unicode(chess.BLACK))
            builder.append("]\n")
            builder.append("black B pocket: [")
            builder.append(self.boardB.get_pocket(chess.BLACK).unicode(chess.BLACK))
            builder.append("]\n")
            builder.append("\n")

        return "".join(builder)

    def __str__(self) -> str:
        return self.boardA.__str__() + "\n\n" + self.boardB.__str__()

    def get_pocket(self, board_id: str):
        if board_id == self.BOARD_A:
            print(self.boardA.pockets)
        elif board_id == self.BOARD_B:
            print(self.boardB.pockets)
        else:
            raise ValueError("Invalid board string")

    def reset(self) -> None:
        """Restores the starting position for each board."""
        self.boardA.reset()
        self.boardB.reset()

    def clear(self) -> None:
        """
        Clears the board.

        Resets move stack and move counters. The side to move is white. There
        are no rooks or kings, so castling rights are removed.

        In order to be in a valid :func:`~chess.Board.status()` at least kings
        need to be put on the board.
        """
        self.boardA.clear()
        self.boardB.clear()
        pass

    def reset_board(self) -> None:
        self.boardA.reset_board()
        self.boardB.reset_board()

    def clear_board(self) -> None:
        self.boardA.clear_board()
        self.boardB.clear_board()
        self.clear_stack()

    def clear_stack(self) -> None:
        """Clears the move stack."""
        super().clear_stack()

    def _board_state(self: BughouseSuperBoardT) -> _BughouseSuperBoardState[BughouseSuperBoardT]:
        return _BughouseSuperBoardState(self)

    def push_san(self, san: str, target: str = None):
        if target == 'A':
            self.boardA.push_san(san)
        elif target == 'B':
            self.boardB.push_san(san)
        else:
            raise ValueError("Invalid board string")

    def push(self, move: chess.Move, board_id: str) -> None:
        """
        Executes a push. Pushes the move to the board represented by board_id

        :param move: the move to push
        :param board_id: the board_id of the baseboard to push move to 

        :raises: :exc:`ValueError` if the id of the most recently pushed baseboard
        is not a valid board_id
        """
        if board_id == self.BOARD_A:
            self.boardA.push(move, pocket_pushing=True)
        elif board_id == self.BOARD_B:
            self.boardB.push(move, pocket_pushing=True)
        else:
            raise ValueError("Invalid board id. {} is not a valid board id".format(board_id))
        self.board_push_pop_stack.append(board_id)

    def pop(self) -> chess.Move:
        """
        Executes a pop. Pops the move of whichever baseboard most recently 
        pushed.

        :returns: the move that was popped from a baseboard

        :raises: :exc:`ValueError` if the id of the most recently pushed baseboard
        is not a valid board_id
        """
        board_id = self.board_push_pop_stack.pop()
        if board_id == self.BOARD_A:
            return self.boardA.pop(pocket_popping=True)
        elif board_id == self.BOARD_B:
            return self.boardB.pop(pocket_popping=True)
        else:
            raise ValueError("Invalid board string")

    def peek(self) -> str:
        """
        Gets the board_id of the board with the most recent move.
        :raises: :exc:`IndexError` if the move stack is empty
        """
        return self.board_push_pop_stack[-1]

    def can_claim_fifty_moves(self) -> bool:
        # This is what it was in Crazyhouse, and it seems sufficient to me
        return False

    def is_seventyfive_moves(self) -> bool:
        # This is what it was in Crazyhouse, and it seems sufficient to me
        return False

    def push_to_pocket(self, piece_type: chess.PieceType, board_id, color: chess.Color) -> None:
        """
        pushes the piece_type to board_id for color's pocket
        """
        if board_id == self.BOARD_A:
            self.boardA.add_to_pocket(piece_type, color)
        elif board_id == self.BOARD_B:
            self.boardB.add_to_pocket(piece_type, color)

    def rm_from_pocket(self, piece_type: chess.PieceType, board_id, color: chess.Color) -> None:
        """
        Removes the piece_type from color's pocket in board_id
        """
        if board_id == self.BOARD_A:
            self.boardA.rm_from_pocket(piece_type, color)
        elif board_id == self.BOARD_B:
            self.boardB.rm_from_pocket(piece_type, color)

    def is_irreversible(self, move: chess.Move) -> bool:
        return self.boardA.is_irreversible(move) and self.boardA.is_irreversible(move)

    def is_fivefold_repetition(self):
        return self.boardA.is_fivefold_repetition() or self.boardB.is_fivefold_repetition()

    def _transposition_key(self) -> Hashable:
        return (self.boardA._transposition_key(),
                self.boardB._transposition_key())

    def legal_drop_squares_mask(self, target: str) -> chess.Bitboard:
        if target == self.BOARD_A:
            return self.boardA.legal_drop_squares_mask()
        elif target == self.BOARD_B:
            return self.boardB.legal_drop_squares_mask()
        else:
            raise ValueError("Invalid board string")

    def parse_san(self, san: str, target: str = None) -> chess.Move:
        if target == self.BOARD_A:
            return self.boardA.parse_san(san)
        elif target == self.BOARD_B:
            return self.boardB.parse_san(san)
        else:
            raise ValueError("Invalid board string")

    # Don't think this function is needed
    # def has_insufficient_material(self, color: chess.Color, target: str=None) -> bool:
    #     # In practise no material can leave the game, but this is easy to
    #     # implement anyway. Note that bishops can be captured and put onto
    #     # a different color complex.
    #     return (
    #         chess.popcount(self.occupied) + sum(len(pocket) for pocket in self.pockets) <= 3 and
    #         not self.pawns and
    #         not self.rooks and
    #         not self.queens and
    #         not any(pocket.count(chess.PAWN) for pocket in self.pockets) and
    #         not any(pocket.count(chess.ROOK) for pocket in self.pockets) and
    #         not any(pocket.count(chess.QUEEN) for pocket in self.pockets))

    def set_fen(self, fen: str) -> None:
        fen_lst = fen.split("|")

        self.boardA.set_fen(fen_lst[0])
        self.boardB.set_fen(fen_lst[1])

    def board_fen(self, *, promoted: Optional[bool] = None) -> str:
        return self.boardA.board_fen() + "|" + self.boardB.board_fen()

    def fen(self, *, shredder: bool = False, en_passant: str = "legal", promoted: Optional[bool] = None) -> str:
        return self.boardA.fen() + " | " + self.boardB.fen()

    def is_valid(self) -> bool:
        return self.boardA.is_valid() and self.boardB.is_valid()

    def status(self, target: str) -> chess.Status:
        if target == chess.A:
            return self.boardA.status()
        elif target == chess.B:
            return self.boardB.status()
        else:
            raise ValueError("Invalid board string")

    def is_game_over(self):
        is_A_over = self.boardA.is_game_over()
        is_B_over = self.boardB.is_game_over()
        if is_A_over or is_B_over:
            return (is_A_over, is_B_over)
        else:
            return False 

    def copy(self):
        board = BughouseSuperBoard()
        # board.name = "copy"
        board.boardA = self.boardA.copy()
        board.boardA.set_super_board(board)
        board.boardB = self.boardB.copy()
        board.boardB.set_super_board(board)
        return board

    def pocket_size(self):
        return self.boardA.pocket_size() + self.boardB.pocket_size()

    # def epd(self, shredder: bool = False, en_passant: str = "legal", promoted: Optional[bool] = None, **operations: Union[None, str, int, float, chess.Move, Iterable[chess.Move]]) -> str:
    #     epd = super().epd(shredder=shredder, en_passant=en_passant, promoted=promoted)
    #     board_part, info_part = epd.split(" ", 1)
    #     return "{}[{}{}] {}".format(board_part, str(self.pockets[chess.WHITE]).upper(), str(self.pockets[chess.BLACK]), info_part)

    # def status(self) -> chess.Status:
    #     status = super().status()
    #
    #     if chess.popcount(self.pawns) + self.pockets[chess.WHITE].count(chess.PAWN) + self.pockets[chess.BLACK].count(chess.PAWN) <= 16:
    #         status &= ~chess.STATUS_TOO_MANY_BLACK_PAWNS
    #         status &= ~chess.STATUS_TOO_MANY_WHITE_PAWNS
    #
    #     if chess.popcount(self.occupied) + len(self.pockets[chess.WHITE]) + len(self.pockets[chess.BLACK]) <= 32:
    #         status &= ~chess.STATUS_TOO_MANY_BLACK_PIECES
    #         status &= ~chess.STATUS_TOO_MANY_WHITE_PIECES
    #
    #     return status


VARIANTS = [
    chess.Board,
    SuicideBoard, GiveawayBoard, AntichessBoard,
    AtomicBoard,
    KingOfTheHillBoard,
    RacingKingsBoard,
    HordeBoard,
    ThreeCheckBoard,
    CrazyhouseBoard,
    BughouseSuperBoard
]  # type: List[Type[chess.Board]]


def find_variant(name: str) -> Type[chess.Board]:
    """Looks for a variant board class by variant name."""
    for variant in VARIANTS:
        if any(alias.lower() == name.lower() for alias in variant.aliases):
            return variant
    raise ValueError("unsupported variant: {}".format(name))
