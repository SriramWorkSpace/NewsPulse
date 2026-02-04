from __future__ import annotations

from app.services.analytics.trends import rank_trends


def test_ranking_new_group_above_existing():
    current = {"new kw": 3, "existing kw": 10}
    previous = {"existing kw": 1}

    ranked = rank_trends(current=current, previous=previous, limit=10)

    assert ranked[0].keyword == "new kw"  # Group A always above Group B
    assert ranked[0].previous_count == 0


def test_ranking_new_sorted_by_current_count_desc():
    current = {"a": 1, "b": 5, "c": 2}
    previous = {}

    ranked = rank_trends(current=current, previous=previous, limit=10)
    assert [r.keyword for r in ranked[:3]] == ["b", "c", "a"]


def test_ranking_existing_sorted_by_growth_desc():
    current = {"x": 10, "y": 10}
    previous = {"x": 5, "y": 2}

    ranked = rank_trends(current=current, previous=previous, limit=10)
    # growth(x)=1.0, growth(y)=4.0
    assert ranked[0].keyword == "y"
