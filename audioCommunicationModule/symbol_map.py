from itertools import combinations
from symbol import OFDMSymbol


class SymbolMap:
    UNRECOGNISED_SYMBOL = '_'

    """
        construct the mapping between characters and symbols.
        param symbol_size is the size of the symbol binary vector
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
            symbol_weight,
            character_space_size)
        self._sync_symbol = self._symbol_map[character_space_size]
        self._termination_symbol = self._symbol_map[character_space_size + 1]

    @property
    def sync_symbol(self):
        return self._sync_symbol

    @property
    def termination_symbol(self):
        return self._termination_symbol

    @staticmethod
    def _create_mapping(
            symbol_size: int,
            symbol_weight: int,
            character_space_size: int) -> list[OFDMSymbol]:
        # Generate all combinations of indices with weight symbol_weight
        index_combinations = list(combinations(range(symbol_size), symbol_weight))

        symbols = [OFDMSymbol(set(index_combination)) for index_combination in index_combinations]

        return symbols

    def char_to_symbol(self, char: str) -> OFDMSymbol:
        return self._symbol_map[ord(char)]

    def symbol_to_char(self, symbol: OFDMSymbol | None) -> str:
        if symbol not in self._symbol_map:
            return self.UNRECOGNISED_SYMBOL
        return chr(self._symbol_map.index(symbol))

    def string_to_symbols(self, string: str) -> list[OFDMSymbol]:
        return [self.char_to_symbol(char) for char in string]

    def symbols_to_string(self, symbols: list[OFDMSymbol]) -> str:
        return ''.join([self.symbol_to_char(symbol) for symbol in symbols])
