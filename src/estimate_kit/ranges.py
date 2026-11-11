"""Three-point estimates and how they combine.

A task is a best / likely / worst triple in hours. The PERT expected value is
(best + 4 * likely + worst) / 6 and the spread is (worst - best) / 6, which is
the usual standard-deviation approximation for a PERT distribution.

Totals add the expected values. The spreads are combined as the square root
of the sum of squares, which treats tasks as independent. Real tasks are not
independent (one wrong assumption can slow several at once), so the plausible
range this gives is narrower than reality. Treat it as a lower bound on how
wide the uncertainty is, and compare it with the plain sum of worst cases.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

# Number of standard deviations either side of the expected value used for the
# "plausible range" of a total.
PLAUSIBLE_SIGMAS = 2.0


@dataclass(frozen=True)
class ThreePoint:
    best: float
    likely: float
    worst: float

    def __post_init__(self) -> None:
        if self.best < 0:
            raise ValueError(f"best must not be negative, got {self.best}")
        if not self.best <= self.likely <= self.worst:
            raise ValueError(
                "expected best <= likely <= worst, "
                f"got best={self.best}, likely={self.likely}, worst={self.worst}"
            )

    @property
    def expected(self) -> float:
        return (self.best + 4 * self.likely + self.worst) / 6

    @property
    def spread(self) -> float:
        return (self.worst - self.best) / 6

    def scaled(self, factor: float) -> ThreePoint:
        if factor <= 0:
            raise ValueError(f"factor must be positive, got {factor}")
        return ThreePoint(self.best * factor, self.likely * factor, self.worst * factor)

    def rounded(self, step: float = 0.5) -> ThreePoint:
        # Rounding is monotonic, so best <= likely <= worst still holds.
        return ThreePoint(*(round(v / step) * step for v in (self.best, self.likely, self.worst)))


@dataclass(frozen=True)
class Total:
    best: float
    likely: float
    worst: float
    expected: float
    spread: float
    low: float
    high: float


def combine(items: Iterable[ThreePoint]) -> Total:
    points = list(items)
    best = sum(p.best for p in points)
    likely = sum(p.likely for p in points)
    worst = sum(p.worst for p in points)
    expected = sum(p.expected for p in points)
    spread = math.sqrt(sum(p.spread**2 for p in points))
    # The plausible range never leaves the sum of bests / sum of worsts.
    low = max(best, expected - PLAUSIBLE_SIGMAS * spread)
    high = min(worst, expected + PLAUSIBLE_SIGMAS * spread)
    return Total(best, likely, worst, expected, spread, low, high)
