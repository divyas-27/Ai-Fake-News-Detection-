import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import DB_CONFIG, get_total_predictions, get_total_users, get_prediction_counts


def test_dashboard_stats_read_from_active_database():
    assert DB_CONFIG['database'] == 'fake_news_detection'

    total_predictions = get_total_predictions()
    total_users = get_total_users()
    counts = get_prediction_counts()

    assert total_predictions > 0
    assert total_users > 0
    assert counts['total'] > 0
