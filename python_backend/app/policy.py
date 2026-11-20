from decimal import Decimal
from datetime import date
from .schemas import Claim, ClaimResult

INELIGIBLE = {"spa", "minibar", "alcohol", "personal_entertainment", "in_room_movies",
              "personal_shopping", "gifts", "traffic_fines", "penalties", "late_fees"}
ELIGIBLE = {"airfare", "lodging", "meals", "ground_transport", "conference_fees", "registration"}

def policy_lookup(category: str) -> list[str]:
    if category.lower() in INELIGIBLE:
        return ["POL-CAT-02"]
    if category.lower() in ELIGIBLE:
        return ["POL-CAT-01"]
    return []

def receipt_completeness_check(claim: Claim) -> list[str]:
    missing = []
    for i, item in enumerate(claim.items, 1):
        required = item.amount > Decimal("25") or item.category.lower() in {"airfare", "lodging"}
        if required and not item.receipt_attached:
            missing.append(f"Item {i}: {item.description} ({item.category})")
    return missing

def reimbursement_calculator(claim: Claim):
    approved = Decimal("0.00")
    deducted = Decimal("0.00")
    refs = set()
    reasons = []
    manual = []
    all_ineligible = True

    for item in claim.items:
        category = item.category.lower()
        refs.update(policy_lookup(category))
        amount = item.amount

        if category in INELIGIBLE:
            deducted += amount
            reasons.append(f"{item.description}: ineligible; deducted ${amount:.2f}.")
            continue

        all_ineligible = False
        if category == "airfare":
            refs.add("POL-AIR-01")
            if (item.airfare_class or "economy").lower() not in {"economy", "coach"}:
                manual.append("Non-economy airfare requires review for possible pre-approval.")
                continue
            approved += amount
        elif category == "lodging":
            refs.add("POL-PD-02")
            cap = Decimal("200") * item.quantity_days
            allowed = min(amount, cap)
            approved += allowed
            deducted += amount - allowed
            if amount > cap:
                reasons.append(f"{item.description}: lodging cap applied; ${amount-cap:.2f} deducted.")
        elif category == "meals":
            refs.add("POL-PD-01")
            cap = Decimal("75") * item.quantity_days
            allowed = min(amount, cap)
            approved += allowed
            deducted += amount - allowed
            if amount > cap:
                reasons.append(f"{item.description}: meal per-diem cap applied; ${amount-cap:.2f} deducted.")
        elif category == "ground_transport":
            refs.add("POL-PD-03")
            cap = Decimal("50") * item.quantity_days
            allowed = min(amount, cap)
            approved += allowed
            deducted += amount - allowed
            if amount > cap:
                reasons.append(f"{item.description}: ground transport cap applied; ${amount-cap:.2f} deducted.")
        elif category in ELIGIBLE:
            approved += amount
        else:
            manual.append(f"Unrecognized expense category: {item.category}.")

    return approved.quantize(Decimal("0.01")), deducted.quantize(Decimal("0.01")), refs, reasons, manual, all_ineligible

def duplicate_detector(claim: Claim) -> list[str]:
    duplicates = []
    seen = set()
    for item in claim.items:
        key = (
            item.category.lower(),
            item.description.strip().lower(),
            item.amount,
        )
        if key in seen:
            duplicates.append(
                f"Possible duplicate item: {item.description} ({item.category}, ${item.amount:.2f})"
            )
        seen.add(key)
    return duplicates

def output_validator(result: ClaimResult) -> list[str]:
    errors = []
    required_fields = {
        "claim_id", "decision", "approved_amount", "deducted_amount",
        "missing_docs", "policy_refs", "confidence", "explanation", "tools_used",
    }
    if set(result.model_dump().keys()) != required_fields:
        errors.append("Structured result does not contain exactly the required fields.")
    if result.decision not in {"APPROVE", "PARTIAL_APPROVE", "REJECT", "MANUAL_REVIEW"}:
        errors.append("Invalid decision value.")
    if result.approved_amount < 0 or result.deducted_amount < 0:
        errors.append("Approved and deducted amounts must be non-negative.")
    if not 0 <= result.confidence <= 1:
        errors.append("Confidence must be between 0 and 1.")
    if not isinstance(result.missing_docs, list):
        errors.append("missing_docs must be a list.")
    if not isinstance(result.policy_refs, list):
        errors.append("policy_refs must be a list.")
    return errors

def approval_threshold_checker(amount: Decimal):
    if amount > Decimal("2000"):
        return "MANUAL_REVIEW", "POL-APR-03"
    if amount > Decimal("500"):
        return "APPROVE", "POL-APR-02"
    return "APPROVE", "POL-APR-01"

def evaluate_claim(claim: Claim) -> ClaimResult:
    approved, deducted, refs, reasons, manual, all_ineligible = reimbursement_calculator(claim)
    missing = receipt_completeness_check(claim)
    duplicates = duplicate_detector(claim)
    if missing:
        refs.update({"POL-RCT-01", "POL-RCT-02"})
    if any(x.category.lower() in {"airfare", "lodging"} for x in claim.items):
        refs.add("POL-RCT-01")
    if (claim.submitted_date - claim.expense_date).days > 30:
        refs.add("POL-TIME-01")
        manual.append("Claim submitted more than 30 days after expense date.")
    if missing:
        manual.append("Required receipt is missing.")
    if duplicates:
        manual.extend(duplicates)
    threshold_decision, threshold_ref = approval_threshold_checker(approved)
    refs.add(threshold_ref)

    if manual or threshold_decision == "MANUAL_REVIEW":
        decision = "MANUAL_REVIEW"
    elif all_ineligible:
        decision = "REJECT"
    elif deducted > 0:
        decision = "PARTIAL_APPROVE"
    else:
        decision = "APPROVE"

    explanation = " ".join(reasons + manual)
    if not explanation:
        explanation = "All submitted items comply with the applicable category, receipt, limit, and approval rules."
    elif decision == "MANUAL_REVIEW":
        explanation = "Manual review required. " + explanation

    tools = ["policy_lookup", "receipt_completeness_check", "reimbursement_calculator",
             "approval_threshold_checker", "duplicate_detector", "output_validator"]
    result = ClaimResult(
        claim_id=claim.claim_id, decision=decision,
        approved_amount=approved, deducted_amount=deducted,
        missing_docs=missing, policy_refs=sorted(refs),
        confidence=0.95 if decision != "MANUAL_REVIEW" else 0.78,
        explanation=explanation, tools_used=tools
    )
    validation_errors = output_validator(result)
    if validation_errors:
        raise ValueError("Invalid claim result: " + " ".join(validation_errors))
    return result
