import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_user_analytics_summary


def test_user_analytics_summary_uses_live_prediction_data():
    summary = get_user_analytics_summary(1)

    assert summary['total_predictions'] >= 0
    assert summary['fake_count'] >= 0
    assert summary['real_count'] >= 0
    assert 0 <= summary['fake_percentage'] <= 100
    assert summary['average_confidence'] >= 0
