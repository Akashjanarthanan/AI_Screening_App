import re
from pathlib import Path

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = [
    "Candidate_ID", "Candidate_Name", "Qualification",
    "Experience_Years", "Technical_Skills", "Current_Role",
    "Preferred_Location",
]
STATUS_OPTIONS = ["All", "Qualified", "Not Qualified", "Manual Review"]

def normalize_text(value):
    """Normalize case and whitespace without inventing missing information."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().casefold()

def qualification_result(value):
    """Return pass/fail/unknown based on the qualifications allowed by the brief."""
    q = normalize_text(value)
    if not q:
        return "unknown"
    # Match the requested degree family and subject, allowing common BE/B.Tech wording.
    degree_ok = bool(re.search(r"\b(be|b\.e\.|btech|b\.tech|bachelor of engineering|bachelor of technology)\b", q))
    subject_ok = any(term in q for term in [
        "computer science", "information technology", "software engineering"
    ])
    if degree_ok and subject_ok:
        return "pass"
    # A clearly supplied but different qualification is a definite mismatch.
    return "fail"

def experience_result(value):
    if pd.isna(value) or str(value).strip() == "":
        return "unknown"
    try:
        years = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if years < 0:
        return "unknown"
    return "pass" if years >= 3 else "fail"

def skill_result(value, skill):
    """Recognize exact skill tokens and explicit equivalents, not substring accidents."""
    raw = normalize_text(value)
    if not raw:
        return "unknown"

    # Split common CSV skill lists on commas, semicolons, pipes, and new lines.
    tokens = [re.sub(r"\s+", " ", t).strip() for t in re.split(r"[,;|\n]+", raw)]
    tokens = [t for t in tokens if t]
    if not tokens:
        return "unknown"

    if skill == "python":
        if any(re.fullmatch(r"(python|python 2|python 3|python3|python 2\.x|python 3\.x)", t) for t in tokens):
            return "pass"
        # "Py" is not accepted automatically; it requires a human equivalence check.
        if any(re.fullmatch(r"py", t) for t in tokens):
            return "unknown"
        return "fail"

    if skill == "sql":
        if any(
            re.fullmatch(r"(sql|structured query language|sql server|mysql|postgresql|postgres|sqlite|tsql|t-sql)", t)
            for t in tokens
        ):
            return "pass"
        return "fail"

    return "unknown"

def screen_candidate(row):
    q = qualification_result(row.get("Qualification"))
    e = experience_result(row.get("Experience_Years"))
    p = skill_result(row.get("Technical_Skills"), "python")
    s = skill_result(row.get("Technical_Skills"), "sql")

    # A definitive failure takes precedence over any other unknown field.
    failures = []
    if q == "fail":
        failures.append("Qualification does not meet the specified BE/B.Tech subject requirement")
    if e == "fail":
        failures.append("Experience is below the required 3 years")
    if p == "fail":
        failures.append("Python is not listed as a mandatory skill")
    if s == "fail":
        failures.append("SQL is not listed as a mandatory skill")
    if failures:
        return pd.Series({"Expected_Status": "Not Qualified", "Reason": "; ".join(failures)})

    unknowns = []
    if q == "unknown":
        unknowns.append("Qualification is missing or unclear")
    if e == "unknown":
        unknowns.append("Experience is missing or invalid")
    if p == "unknown":
        unknowns.append("Python skill wording requires verification")
    if s == "unknown":
        unknowns.append("SQL skill wording requires verification")
    if unknowns:
        return pd.Series({"Expected_Status": "Manual Review", "Reason": "; ".join(unknowns)})

    return pd.Series({
        "Expected_Status": "Qualified",
        "Reason": "All mandatory requirements are clearly met"
    })

def evaluate_dataframe(data):
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing_columns:
        raise ValueError("Missing mandatory columns: " + ", ".join(missing_columns))
    if data.empty:
        raise ValueError("The uploaded CSV has no candidate rows.")
    results = data.copy()
    decisions = results.apply(screen_candidate, axis=1)
    
    results["Expected_Status"] = decisions["Expected_Status"]
    results["Reason"] = decisions["Reason"]

    # Apply Kochi as an additional eligibility condition
    #kochi_mask = (
    #    results["Preferred_Location"]
     #   .astype("string")
    #    .str.strip()
     #   .str.casefold()
     #   == "kochi"
   # )

    # Candidates must satisfy all screening conditions AND prefer Kochi
   # not_kochi = ~kochi_mask

  #  results.loc[not_kochi, "Expected_Status"] = "Not Qualified"
  #  results.loc[not_kochi, "Reason"] = "Preferred location is not Kochi"
 

    
    return results

st.set_page_config(page_title="HLL AI Candidate Screening", page_icon="📋", layout="wide")
st.title("HLL AI Candidate Screening")
st.caption("Decision-support prototype only — every result requires human review; no final hiring decision is automated.")

uploaded_file = st.file_uploader("Upload candidate CSV", type=["csv"])
if uploaded_file is None:
    st.info("Upload HLL_AI_Screening_200_Candidates.csv to begin.")
    st.write("Required columns:", ", ".join(REQUIRED_COLUMNS))
    st.stop()

try:
    data = pd.read_csv(uploaded_file)
except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
    st.error(f"Could not read this CSV. Please check its format. Details: {exc}")
    st.stop()

st.write(f"**Rows read:** {len(data)}")
missing = [col for col in REQUIRED_COLUMNS if col not in data.columns]
if missing:
    st.error("Missing mandatory columns: " + ", ".join(missing))
    st.stop()

try:
    results = evaluate_dataframe(data)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

counts = results["Expected_Status"].value_counts()
total = len(results)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total candidates", total)
c2.metric("Qualified", int(counts.get("Qualified", 0)))
c3.metric("Not Qualified", int(counts.get("Not Qualified", 0)))
c4.metric("Manual Review", int(counts.get("Manual Review", 0)))

if int(counts.sum()) != total:
    st.warning("Status totals do not reconcile. Please investigate.")
else:
    st.success(f"Totals reconcile: {int(counts.sum())} of {total} candidates have exactly one status.")


# Filter by status
selected_status = st.selectbox("Filter by status", STATUS_OPTIONS)

# Filter by location
location_options = ["All"] + sorted(
    results["Preferred_Location"].dropna().astype(str).str.strip().unique().tolist()
)

selected_location = st.selectbox("Filter by location", location_options)



# Apply both filters
view = results.copy()

if selected_status != "All":
    view = view[view["Expected_Status"] == selected_status]

if selected_location != "All":
    view = view[
        view["Preferred_Location"].astype("string").str.strip().str.casefold()
        == selected_location.strip().casefold()
    ]

# Display filtered results
display_columns = [
    "Candidate_ID",
    "Candidate_Name",
    "Preferred_Location",
    "Expected_Status",
    "Reason"
]

st.subheader(f"Candidate results ({len(view)} shown)")
st.dataframe(view[display_columns], use_container_width=True, hide_index=True)


st.subheader("Download report")
csv_bytes = results.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Download screening results CSV",
    data=csv_bytes,
    file_name="HLL_AI_Screening_Results.csv",
    mime="text/csv",
)
with st.expander("View input data preview"):
    st.dataframe(data.head(10), use_container_width=True, hide_index=True)
