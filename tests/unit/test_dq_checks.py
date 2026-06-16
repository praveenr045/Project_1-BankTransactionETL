"""
Pure Python unit tests for is_quarantined().
No Spark, no Java, no Databricks needed — runs in GitHub Actions CI
in under a second.
"""

from src.quality.dq_checks import is_quarantined


def test_null_amount_is_quarantined():
    assert is_quarantined(amount=None, time=100.0, class_label=0) is True


def test_null_time_is_quarantined():
    assert is_quarantined(amount=150.0, time=None, class_label=0) is True


def test_null_class_is_quarantined():
    assert is_quarantined(amount=150.0, time=100.0, class_label=None) is True


def test_negative_amount_is_quarantined():
    assert is_quarantined(amount=-10.0, time=100.0, class_label=0) is True


def test_outlier_amount_is_quarantined():
    assert is_quarantined(amount=999_999_999.99, time=100.0, class_label=0) is True


def test_future_timestamp_is_quarantined():
    assert is_quarantined(amount=150.0, time=999_999_999.0, class_label=0) is True


def test_clean_record_is_not_quarantined():
    assert is_quarantined(amount=150.0, time=100.0, class_label=0) is False


def test_zero_amount_is_not_quarantined():
    # Zero-amount transactions are valid (e.g. balance checks), not quarantined
    assert is_quarantined(amount=0.0, time=100.0, class_label=0) is False


def test_max_valid_amount_is_not_quarantined():
    assert is_quarantined(amount=999_999.99, time=100.0, class_label=0) is False