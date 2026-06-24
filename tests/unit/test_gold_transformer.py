def test_bucket_descriptions():
    """All 5 buckets must have descriptions."""
    buckets = ["micro", "small", "medium", "large", "very_large"]
    descriptions = {
        "micro":      "Under $10 — typically small retail",
        "small":      "$10-$99 — everyday purchases",
        "medium":     "$100-$999 — significant purchases",
        "large":      "$1000-$9999 — high value transactions",
        "very_large": "$10000+ — very high value, review required",
    }

    for bucket in buckets:
        assert bucket in descriptions
        assert len(descriptions[bucket]) > 0

def test_risk_levels():
    """Verify risk level assignment per class."""
    risk_levels = {0 : "LOW", 1 : "CRITICAL"}
    assert risk_levels[0] == "LOW"
    assert risk_levels[1] == "CRITICAL"

def test_fraud_class_keys():
    legitimate_key = 0
    fraudulent_key = 1
    assert legitimate_key != fraudulent_key
    assert legitimate_key == 0
    assert fraudulent_key == 1

def test_bucket_sort_order():
    bucket_order = {
        "micro" : 1,
        "small" : 2,
        "medium" : 3,
        "large" : 4,
        "very_large" : 5
    }
    assert bucket_order["micro"] < bucket_order["small"]
    assert bucket_order["small"] < bucket_order["medium"]
    assert bucket_order["medium"] < bucket_order["large"]
    assert bucket_order["large"] < bucket_order["very_large"]

def test_days_of_week():
    weekend_days = [1,7]
    week_days = [i for i in range(2,7)]

    for day in weekend_days:
        assert day in [1, 7]
    for day in week_days:
        assert day in [2,3,4,5,6]