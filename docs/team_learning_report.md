# Quarterly Learning Performance Summary (Synthetic)

> Synthetic demonstration document. All figures, names, and metrics are fabricated for demonstration purposes only.

---

## Headline Metrics — Q2 2026

| Metric | Value |
|---|---|
| Learners actively enrolled | 20 |
| Certifications targeted | AZ-204, AZ-305, AZ-400, DP-203, SC-200 |
| Average study hours completed | 19.4h |
| Overall first-attempt pass rate | 60% |
| Learners deemed exam-ready (readiness gate met) | 9 / 20 (45%) |
| Capacity-constrained learners (>20 meeting hrs/wk) | 6 / 20 (30%) |

---

## Pass Rate by Certification

| Certification | Enrolled | Passed | Pass Rate | Avg Hours |
|---|---|---|---|---|
| AZ-204 | 6 | 3 | 50% | 18.5h |
| AZ-305 | 3 | 1 | 33% | 17.0h |
| AZ-400 | 5 | 3 | 60% | 21.8h |
| DP-203 | 4 | 2 | 50% | 17.8h |
| SC-200 | 2 | 2 | 100% | 24.0h |

**Key observation:** SC-200 learners achieved 100% pass rate with the highest average study hours (24h), confirming that sustained study above the recommended threshold (20h) drives outcomes. AZ-305 shows the lowest pass rate, largely explained by under-study — average 17h against a 30h recommendation.

---

## Study Hours vs. Practice Score Correlation

Analysis across 20 learners shows a strong positive correlation between study hours and practice scores, but with a critical threshold effect:

- Learners with **fewer than 12 study hours** have a 0% first-attempt pass rate regardless of practice score.
- Between 12–18 hours, practice score becomes the dominant predictor — learners scoring 75%+ pass at a 72% rate.
- Above 18 study hours, learners scoring 75%+ pass at an 89% rate.
- **Practice score is a stronger predictor of outcome than raw hours** once the minimum study threshold (90% of recommended hours) is met.

| Study Hours Bracket | Avg Practice Score | Pass Rate |
|---|---|---|
| < 12h | 61% | 0% |
| 12–18h | 69% | 38% |
| 18–24h | 76% | 71% |
| > 24h | 83% | 92% |

---

## Risk Indicators

Learners flagged as **at-risk** share one or more of the following patterns:

1. **Under-studied:** Study hours below 70% of the certification's recommended hours. Currently affects 8 of 20 learners.
2. **Low practice score:** Practice assessment average below the 75% readiness gate. Currently affects 9 of 20 learners.
3. **Capacity-constrained:** More than 20 meeting hours per week, correlating with fragmented study sessions and lower completion rates. Currently affects 6 of 20 learners.

### At-Risk Learner Profile

Learners with all three risk indicators simultaneously have a historically 0% first-attempt pass rate in this dataset. Early intervention — plan extension, manager check-in, or workload adjustment — is recommended for these cases.

---

## Microsoft Learn Engagement Data

When cross-referenced with Microsoft Learn module completion (via the Microsoft Learn MCP integration), learners who complete **at least 3 hands-on lab modules** before the exam show a 2.3x higher pass rate than learners who study from documentation alone:

| Microsoft Learn Engagement | Pass Rate |
|---|---|
| 0 hands-on modules completed | 28% |
| 1–2 modules completed | 51% |
| 3+ modules completed | 83% |

**Recommendation:** The Curator agent should retrieve and surface Microsoft Learn hands-on lab modules (via the Microsoft Learn MCP) as a priority over passive reading materials.

---

## Team-Level Readiness Summary

| Team | Learners | Exam-Ready | At Risk | Capacity Constrained | Readiness Rate |
|---|---|---|---|---|---|
| TEAM-A | 7 | 3 | 4 | 3 | 43% |
| TEAM-B | 6 | 2 | 3 | 2 | 33% |
| TEAM-C | 7 | 4 | 3 | 1 | 57% |

TEAM-C shows the strongest readiness rate (57%) despite having 7 learners. Key differentiators: lower average meeting load (14.4h/wk vs. 19.2h/wk for TEAM-A) and higher focus hours (17.6h/wk). TEAM-B has the lowest readiness rate — 2 of its 6 learners are pursuing AZ-305, which has the highest recommended study hours (30h) but the lowest average actual hours.

---

## Certification Completion Velocity

Average time from enrolment to exam booking across cohorts:

- **AZ-204:** 6.2 weeks (target: 4–6 weeks)
- **AZ-305:** 9.8 weeks (target: 6–8 weeks) — longest path, as expected
- **AZ-400:** 7.1 weeks (target: 5–7 weeks)
- **DP-203:** 6.8 weeks (target: 5–7 weeks)
- **SC-200:** 5.4 weeks (target: 4–6 weeks) — fastest completion

---

## Recommendations for L&D Programme

1. **Enforce the readiness gate:** No learner should book the exam with fewer than 90% of recommended hours and less than 75% on the most recent practice assessment. Currently 4 learners have booked prematurely.
2. **Prioritise Microsoft Learn hands-on labs:** Module completion data shows a 2.3x pass rate improvement. Surface these explicitly in every learning plan (via Microsoft Learn MCP).
3. **Reduce meeting load for TEAM-A and TEAM-B:** Work with managers to protect at least two 45-minute focus blocks per day during active study periods.
4. **Early risk detection:** Flag learners with fewer than 12 study hours after two weeks of enrolment for proactive coaching.
5. **Advance AZ-305 learners earlier:** AZ-305's 30h recommendation requires 8+ weeks. Enrol Cloud Engineers in AZ-305 preparation within 2 weeks of passing AZ-204.
