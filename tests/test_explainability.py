from financial_ai.explainability.service import assess_risk


def test_risk_assessment_is_deterministic():
    analytics = {
        "metrics": {
            "annualized_volatility": 0.50,
            "max_drawdown": -0.35,
            "value_at_risk_95": -0.04,
        }
    }
    forecast = {"predicted_next_day_log_return": -0.025}
    result = assess_risk(analytics, forecast)
    assert result["risk_level"] == "critical"
    assert len(result["drivers"]) == 4
