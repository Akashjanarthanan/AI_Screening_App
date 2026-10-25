# HLL AI Candidate Screening

## What it does
- Reads the provided CSV through a local Streamlit interface.
- Validates the required columns and displays the input row count.
- Applies the stated mandatory criteria: approved BE/B.Tech subject, at least 3 years of experience, Python, and SQL.
- Returns exactly one label per candidate: `Qualified`, `Not Qualified`, or `Manual Review`.
- Gives a specific reason, supports status filtering, displays reconciling totals, and exports original fields plus `Expected_Status` and `Reason`.
- Keeps final hiring decisions with a human.

## Requirements
- Python 3.10+
- Packages in `requirements.txt`

## Run on Windows
Open Command Prompt in this folder and run:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser. Upload `HLL_AI_Screening_200_Candidates.csv`.

## Classification approach
1. A definite failure in any mandatory requirement leads to `Not Qualified`, even if another field is unclear.
2. If no definite failure exists but a required field is missing, invalid, or needs equivalence verification, the candidate is `Manual Review`.
3. Only candidates whose mandatory requirements are all clearly met are `Qualified`.
4. Desirable skills do not compensate for missing Python or SQL.
5. Missing experience is not treated as zero; it goes to `Manual Review` unless another criterion definitively fails.

## Notes
- This is a local prototype. Do not upload real personal data or send candidate records to external services.
- Skill matching is deliberately conservative. For example, `Py` alone is sent to manual review rather than automatically treated as Python.
- The qualification matching covers the common BE/B.Tech wording in the supplied task. Human verification remains appropriate for unusual qualification descriptions.
