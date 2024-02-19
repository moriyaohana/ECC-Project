from itertools import combinations


class CharSymbolMap:
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

        self.symbol_size = symbol_size
        self.symbol_weight = symbol_weight
        self.symbol_map = CharSymbolMap._create_mapping(
            symbol_size,
            symbol_weight,
            character_space_size)

    @staticmethod
    def _create_mapping(
            symbol_size: int,
            symbol_weight: int,
            character_space_size: int) -> list[list[int]]:
        # Generate all combinations of indices with weight symbol_weight
        index_combinations = list(combinations(range(symbol_size), symbol_weight))

        # Initialize the list to store binary vectors
        binary_vectors = []

        # Iterate over index combinations
        for indices in index_combinations:
            # Initialize a binary vector with all zeros
            binary_vector = [0] * symbol_size
            # Set the selected indices to 1
            for index in indices:
                binary_vector[index] = 1
            # Add the binary vector to the list
            binary_vectors.append(binary_vector)

        return binary_vectors[:character_space_size]

    def char_to_symbol(self, char: str) -> list[int]:
        return self.symbol_map[ord(char)]

    def symbol_to_char(self, symbol: list[int]) -> str:
        return chr(self.symbol_map.index(symbol))

    def string_to_symbols(self, string: str) -> list[list[int]]:
        return [self.char_to_symbol(char) for char in string]

    def symbols_to_string(self, symbols: list[list[int]]) -> str:
        return ''.join([self.symbol_to_char(sym) for sym in symbols])
