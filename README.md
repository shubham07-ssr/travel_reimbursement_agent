# Travel Reimbursement Approval Agent

A lightweight assessment prototype. The Python service owns policy evaluation; the optional ASP.NET Core MVC application is a thin client.

## Prerequisites
- Python 3.11+
- .NET 8 SDK (optional, for the MVC UI)
- A Hugging Face token with access to an Inference Provider (optional for deterministic policy evaluation)

## Python setup (Windows PowerShell)
```powershell
cd python_backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
Copy-Item ..\.env.example ..\.env
# Edit ..\.env only if you want hosted inference; HF_TOKEN may remain blank.
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

The deterministic policy engine runs without an HF token. The hosted model is used as an explanatory/triage assistant when configured; it does not decide reimbursement amounts or override policy rules.

## Notebook
Open `notebook/travel_reimbursement_agent.ipynb` and run all cells. It uses the same deterministic rules and attempts hosted inference only when `HF_TOKEN` is configured. The notebook is the primary assignment deliverable.

## ASP.NET Core MVC (optional demo)
```powershell
cd dotnet_mvc/TravelReimbursement.Web
dotnet run
```
Set `API_BASE_URL` to the Python API URL if it differs from the default.

## Design choices
- Policy arithmetic uses `Decimal`; LLM output is never trusted for monetary calculations.
- Missing required receipts, business/first-class airfare, claims over $2,000, late submissions, and ambiguity route to `MANUAL_REVIEW`.
- The five sample claims are copied from Appendix B of the supplied assignment.
- The final notebook cell emits exactly the nine required fields per claim.
- No vector database is added: the assignment has a small, fixed policy set, so direct policy lookup is simpler and more auditable.

## Known limitations
- Receipt attachment is represented by supplied metadata; no OCR or binary receipt parsing is implemented.
- No persistent database or identity/authentication layer is included.
- The sample claim dates are historical relative to current date. The assignment's policy says claims must be submitted within 30 days of expense date; the supplied sample claims are within that interval.
- Verify the configured Hugging Face model/provider is currently available to your account. Provider availability and supported features can change.

## Validation
```powershell
python -m pytest -q
python -m compileall -q python_backend tests
```
