from typing import Set, List


class OFDMSymbol(object):
    def __init__(self, indices: Set[int]):
        self._indices = indices

    @property
    def weight(self):
        return len(self._indices)

    def frequencies(self, all_frequencies: List[float]) -> List[float]:
        return [all_frequencies[index] for index in self._indices]

    def __eq__(self, other):
        if not isinstance(other, OFDMSymbol):
            return False

        return self._indices == other._indices
