import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))
from app.schemas import Claim
from app.policy import evaluate_claim
from app.sample_data import SAMPLE_CLAIMS
from app.policy import duplicate_detector, output_validator

def test_five_sample_claims_return_decisions():
    results = [evaluate_claim(Claim.model_validate(x)) for x in SAMPLE_CLAIMS]
    assert len(results) == 5
    assert all(r.decision in {"APPROVE","PARTIAL_APPROVE","REJECT","MANUAL_REVIEW"} for r in results)

def test_spa_and_minibar_rejected():
    result = evaluate_claim(Claim.model_validate(SAMPLE_CLAIMS[1]))
    assert result.decision == "REJECT"
    assert str(result.deducted_amount) == "380.00"

def test_missing_receipt_routes_manual_review():
    result = evaluate_claim(Claim.model_validate(SAMPLE_CLAIMS[4]))
    assert result.decision == "MANUAL_REVIEW"

def test_exact_cap_boundaries_are_approved():
    claim = Claim.model_validate({
        "claim_id": "BOUNDARY-001",
        "employee": "Test User",
        "business_purpose": "Test",
        "expense_date": "2026-06-01",
        "submitted_date": "2026-06-02",
        "items": [
            {"category": "lodging", "description": "Lodging", "amount": "200.00",
             "receipt_attached": True, "quantity_days": 1},
            {"category": "meals", "description": "Meals", "amount": "75.00",
             "receipt_attached": True, "quantity_days": 1},
            {"category": "ground_transport", "description": "Taxi", "amount": "50.00",
             "receipt_attached": True, "quantity_days": 1},
        ],
    })
    result = evaluate_claim(claim)
    assert result.decision == "APPROVE"
    assert str(result.approved_amount) == "325.00"
    assert str(result.deducted_amount) == "0.00"

def test_late_submission_routes_manual_review():
    claim = Claim.model_validate({
        "claim_id": "LATE-001",
        "employee": "Test User",
        "business_purpose": "Test",
        "expense_date": "2026-05-01",
        "submitted_date": "2026-06-01",
        "items": [
            {"category": "meals", "description": "Meal", "amount": "20.00",
             "receipt_attached": True, "quantity_days": 1},
        ],
    })
    result = evaluate_claim(claim)
    assert result.decision == "MANUAL_REVIEW"
    assert "POL-TIME-01" in result.policy_refs

def test_duplicate_item_routes_manual_review():
    claim = Claim.model_validate({
        "claim_id": "DUP-001",
        "employee": "Test User",
        "business_purpose": "Test",
        "expense_date": "2026-06-01",
        "submitted_date": "2026-06-02",
        "items": [
            {"category": "meals", "description": "Dinner", "amount": "40.00",
             "receipt_attached": True, "quantity_days": 1},
            {"category": "meals", "description": "Dinner", "amount": "40.00",
             "receipt_attached": True, "quantity_days": 1},
        ],
    })
    result = evaluate_claim(claim)
    assert result.decision == "MANUAL_REVIEW"
    assert duplicate_detector(claim)

def test_unknown_category_routes_manual_review():
    claim = Claim.model_validate({
        "claim_id": "UNKNOWN-001",
        "employee": "Test User",
        "business_purpose": "Test",
        "expense_date": "2026-06-01",
        "submitted_date": "2026-06-02",
        "items": [
            {"category": "custom_expense", "description": "Unexpected item",
             "amount": "10.00", "receipt_attached": True, "quantity_days": 1},
        ],
    })
    result = evaluate_claim(claim)
    assert result.decision == "MANUAL_REVIEW"

def test_output_validator_accepts_valid_result():
    result = evaluate_claim(Claim.model_validate(SAMPLE_CLAIMS[0]))
    assert output_validator(result) == []
