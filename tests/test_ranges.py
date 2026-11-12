import math

import pytest

from estimate_kit.ranges import ThreePoint, combine


def test_pert_expected_and_spread() -> None:
    p = ThreePoint(2, 4, 12)
    # (2 + 4*4 + 12) / 6 = 30 / 6
    assert p.expected == pytest.approx(5.0)
    # (12 - 2) / 6
    assert p.spread == pytest.approx(10 / 6)


@pytest.mark.parametrize(
    ("best", "likely", "worst"),
    [(3, 2, 5), (1, 4, 3), (-1, 2, 3)],
)
def test_invalid_order_or_negative_rejected(best: float, likely: float, worst: float) -> None:
    with pytest.raises(ValueError, match="best"):
        ThreePoint(best, likely, worst)


def test_equal_values_are_allowed() -> None:
    p = ThreePoint(4, 4, 4)
    assert p.expected == 4
    assert p.spread == 0


def test_scaled_and_rounded() -> None:
    p = ThreePoint(2, 5, 12).scaled(1.2)
    assert (p.best, p.likely, p.worst) == pytest.approx((2.4, 6.0, 14.4))
    r = p.rounded()
    assert (r.best, r.likely, r.worst) == (2.5, 6.0, 14.5)


def test_scaled_rejects_non_positive_factor() -> None:
    with pytest.raises(ValueError, match="factor"):
        ThreePoint(1, 2, 3).scaled(0)


def test_combine_two_tasks_by_hand() -> None:
    a = ThreePoint(2, 4, 12)  # expected 5, spread 10/6
    b = ThreePoint(1, 2, 3)  # expected 2, spread 2/6
    total = combine([a, b])
    assert (total.best, total.likely, total.worst) == (3, 6, 15)
    assert total.expected == pytest.approx(7.0)
    # sqrt((10/6)^2 + (2/6)^2) = sqrt(104) / 6
    assert total.spread == pytest.approx(math.sqrt(104) / 6)
    assert total.low == pytest.approx(7.0 - 2 * math.sqrt(104) / 6)
    assert total.high == pytest.approx(7.0 + 2 * math.sqrt(104) / 6)
    # The combined range is narrower than the naive 3 to 15 sum.
    assert total.high < total.worst


def test_combine_clamps_to_sum_of_best_and_worst() -> None:
    # One very skewed task: expected - 2 * spread would fall below best.
    total = combine([ThreePoint(0, 0, 12)])
    assert total.expected == pytest.approx(2.0)
    assert total.spread == pytest.approx(2.0)
    assert total.low == 0  # 2 - 4 = -2, clamped to the sum of bests
    assert total.high == pytest.approx(6.0)


def test_combine_empty() -> None:
    total = combine([])
    assert total.expected == 0
    assert total.low == total.high == 0


@pytest.mark.parametrize("value", [float("inf"), float("nan"), -float("inf")])
def test_non_finite_hours_are_rejected(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        ThreePoint(value, value, value)


def test_rounding_huge_values_does_not_overflow() -> None:
    p = ThreePoint(1e308, 1e308, 1e308).rounded()
    assert p.worst == 1e308
