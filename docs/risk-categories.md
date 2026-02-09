# Risk Categories

Every test maps to one of four risk categories. The category determines what kind of harm occurs if the assertion fails.

## Financial Accuracy

**File:** `tests/test_financial_accuracy.py`

Incorrect dollar amounts, accumulation logic, or penalty rules. The most direct form of harm — someone gets charged the wrong amount.

| Area | Example Risk |
|------|-------------|
| Deductible amounts | Member charged $3000 instead of $1500 |
| Embedded vs non-embedded | Family member forced to satisfy full family deductible |
| Cross-accumulation | In-network spend incorrectly reduces OON deductible |
| Accumulator adjustment | Copay cards count toward OOP max, plan pays 100% too soon |
| ER copay waiver | Member double-charged on admission from ER |
| Prior auth penalty | $500 penalty counts toward OOP, defeating its purpose |
| Pharmacy tiers | Wrong copay amount, no per-fill cap on specialty |
| Mail order ratio | 90-day mail not cheaper than 3x30-day retail |

## Benefit Determination (Coverage)

**File:** `tests/test_benefit_determination.py`

Claims approved when they should be denied, or denied when they should be approved. Both directions cause harm.

| Area | Example Risk |
|------|-------------|
| Preventive frequency | 3 cleanings allowed (overpay) or 1 (denial) instead of 2 |
| Age/gender gating | Mammogram offered to wrong population or denied to eligible |
| Reclassification | Entire colonoscopy billed as diagnostic when only polyp removal is |
| Observation status | Inpatient benefits applied to observation stay |
| Shared visit pools | PT and OT tracked separately, allowing 60 total instead of 60 combined |
| Missing tooth clause | Replacement covered for pre-existing missing teeth |
| Step therapy | Non-preferred drug dispensed without trying generic first |
| Dental waiting periods | Basic services covered before 6-month waiting period |

## Regulatory Compliance

**File:** `tests/test_regulatory.py`

Violations of federal statute. Consequences include fines, lawsuits, regulatory action, and plan disqualification.

| Statute | What's Tested |
|---------|--------------|
| MHPAEA | No separate MH visit/day limits, copay not exceeding medical |
| No Surprises Act | OON emergency at in-network rates, prudent layperson standard |
| NMHPA | 48hr vaginal / 96hr cesarean minimum stays |
| COBRA | 18/36 month eligibility, 102% premium |
| ERISA | Filing deadlines, appeal timelines, expedited review, member rights |

Also tests **regulatory traceability** — every base policy must have a statute citation, and all required statutes must be present.

## Correspondence

**File:** `tests/test_correspondence.py`

Non-compliant communications sent to members. State regulatory action, fines, member complaints, access barriers.

| Area | Example Risk |
|------|-------------|
| Gendered language | "him/her" in CA/NY/OR correspondence (requires gender-neutral) |
| Threshold languages | Missing Spanish, Chinese, Tagalog translations in CA |
| Surprise billing notices | Required notice absent in states with balance billing protections |
| State disclosures | CA independent medical review rights not mentioned |
| EOB fields | Missing remaining deductible/OOP, no appeal rights notice |
| Denial letters | No clinical criteria, no appeal deadline, no external review info |
