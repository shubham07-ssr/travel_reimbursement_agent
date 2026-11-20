from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

Decision = Literal["APPROVE", "PARTIAL_APPROVE", "REJECT", "MANUAL_REVIEW"]

class ClaimItem(BaseModel):
    category: str
    description: str
    amount: Decimal = Field(ge=0)
    receipt_attached: bool = True
    quantity_days: int = Field(default=1, ge=1)
    airfare_class: str | None = None

class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    employee: str
    business_purpose: str
    expense_date: date
    submitted_date: date
    items: list[ClaimItem]

class ClaimResult(BaseModel):
    claim_id: str
    decision: Decision
    approved_amount: Decimal
    deducted_amount: Decimal
    missing_docs: list[str]
    policy_refs: list[str]
    confidence: float
    explanation: str
    tools_used: list[str]
