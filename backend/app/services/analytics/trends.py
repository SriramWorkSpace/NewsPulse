from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrendItem:
    keyword: str
    current_count: int
    previous_count: int
    growth: float | None  # None => new/emerging (previous_count == 0)


def compute_growth(current_count: int, previous_count: int) -> float | None:
    if previous_count == 0:
        return None
    return (current_count - previous_count) / previous_count


def rank_trends(
    *,
    current: dict[str, int],
    previous: dict[str, int],
    limit: int = 50,
) -> list[TrendItem]:
    items: list[TrendItem] = []
    for kw, cur_count in current.items():
        prev_count = previous.get(kw, 0)
        items.append(
            TrendItem(
                keyword=kw,
                current_count=cur_count,
                previous_count=prev_count,
                growth=compute_growth(cur_count, prev_count),
            )
        )

    # Locked ranking rule:
    # Group A (new/emerging) -> previous_count == 0, rank by currentCount
    # Group B (existing)     -> previous_count > 0, rank by growth
    group_a = [i for i in items if i.previous_count == 0]
    group_b = [i for i in items if i.previous_count > 0]

    group_a.sort(key=lambda i: (i.current_count, i.keyword), reverse=True)
    group_b.sort(key=lambda i: ((i.growth or float("-inf")), i.current_count, i.keyword), reverse=True)

    ranked = group_a + group_b
    return ranked[:limit]
