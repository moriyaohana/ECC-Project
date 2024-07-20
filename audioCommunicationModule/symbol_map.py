from itertools import combinations

from typing import List, Union, Optional, Tuple, Set

from symbol import OFDMSymbol


class SymbolMap:
    UNRECOGNISED_SYMBOL = 0xFF
    """
    construct the mapping between bytes and symbols.
    :param symbol_size: is the size of the symbol binary vector
    :param symbol_size: the size of the symbol binary vector
    :param symbol_weight: the required weight of each symbol binary vector,
            the number of '1' bits in the vector.
    """

    def __init__(
            self,
            symbol_size: int,
            symbol_weight: int,
            character_space_size: int = 256):

        # CR: Add type hints to members of class
        self._symbol_size = symbol_size
        self._symbol_weight = symbol_weight
        self._symbol_map = SymbolMap._create_mapping(
            symbol_size,
            symbol_weight)
        self._character_space_size = character_space_size
        self._termination_symbol = self._symbol_map[character_space_size + 1]

    @property
    def termination_symbol(self):
        return self._termination_symbol

    @staticmethod
    def _create_mapping(
            symbol_size: int,
            symbol_weight: int) -> List[OFDMSymbol]:
        # Generate all combinations of indices with weight symbol_weight
        index_combinations = list(combinations(range(symbol_size), symbol_weight))

        symbols = [OFDMSymbol(set(index_combination)) for index_combination in index_combinations]

        return symbols

    def _byte_to_symbol(self, byte: int) -> Optional[OFDMSymbol]:
        if byte >= self._character_space_size:
            return None
        return self._symbol_map[byte]

    def _symbol_to_value(self, symbol: Optional[OFDMSymbol]) -> Optional[int]:
        if symbol not in self._symbol_map:
            return None
        return self._symbol_map.index(symbol)

    def bytes_to_symbols(self, data: bytes) -> List[OFDMSymbol]:
        return [self._byte_to_symbol(byte) for byte in data]

    def _symbols_to_raw_values(self, symbols: List[OFDMSymbol]) -> List[int]:
        return [self._symbol_to_value(symbol) for symbol in symbols]

    def symbols_to_bytes(self, symbols: List[OFDMSymbol]) -> Tuple[bytes, Set[int]]:
        raw_values = self._symbols_to_raw_values(symbols)
        byte_values = bytes([value if value is not None and value < self._character_space_size
                             else self.UNRECOGNISED_SYMBOL
                             for value
                             in raw_values])

        erasure_locations = set(index for index, value in enumerate(raw_values) if value is None
                                or value >= self._character_space_size)

        return byte_values, erasure_locations
