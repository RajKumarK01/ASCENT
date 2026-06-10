# Workload and Learning Correlation (Synthetic)

> Synthetic demonstration document. All figures and patterns are fabricated for demonstration purposes only.

---

## Summary

Analysis of work signals across 20 learners reveals a strong inverse correlation between meeting load and certification study completion. The primary driver of under-study is not lack of motivation — it is calendar fragmentation caused by excessive meeting density.

---

## Meeting Load vs. Study Completion

| Meeting Hours / Week | Avg Study Hours Completed | Completion Rate vs. Target |
|---|---|---|
| < 10h | 22.3h | 108% |
| 10–14h | 20.8h | 101% |
| 14–18h | 18.9h | 92% |
| 18–22h | 14.2h | 69% |
| > 22h | 9.7h | 47% |

**Key finding:** Learners with more than 22 meeting hours per week complete fewer than half of their target study hours. This is the single strongest predictor of under-study in this dataset — stronger than role, certification difficulty, or tenure.

---

## Capacity-Constrained Learner Profile

A learner is classified as **capacity-constrained** when meeting hours exceed 20 per week. Six of 20 learners in the current cohort meet this threshold.

Characteristics of capacity-constrained learners:
- Average actual study hours: 9.7h (vs. 22.1h for non-constrained)
- Preferred learning slot: primarily Evening (63%) — studying after-hours due to daytime meeting load
- Session completion rate: 41% vs. 78% for non-constrained learners
- Most effective intervention: condensing sessions to 30 minutes and scheduling them around identified focus windows

**Recommended cadence for capacity-constrained learners:** 3 short 30-minute sessions per week, timed to coincide with low-meeting windows identified from calendar analysis. Avoid sending reminders during peak meeting blocks (typically 09:00–12:00 for this cohort).

---

## Focus Hours vs. Learning Velocity

| Focus Hours / Week | Avg Modules Completed | Learning Velocity |
|---|---|---|
| < 8h | 1.2 modules/week | Low |
| 8–12h | 2.1 modules/week | Below average |
| 12–16h | 3.4 modules/week | Average |
| 16–20h | 4.8 modules/week | Above average |
| > 20h | 6.1 modules/week | High |

Learners with 15+ focus hours per week show 2.8x higher learning velocity than those with fewer than 8 focus hours. The optimal profile for certification completion is: **12–18 meeting hours + 15+ focus hours per week**.

---

## Preferred Learning Slot Adherence

Respecting a learner's stated preferred learning slot (morning, afternoon, or evening) has a measurable impact on study plan adherence:

| Preferred Slot Respected | Adherence Rate |
|---|---|
| Yes (reminders and blocks match stated preference) | 81% |
| No (generic reminders, slot ignored) | 47% |

**Recommendation:** Always surface reminders at the start of the learner's preferred slot. Use the Work IQ signal (preferred_learning_slot field) to personalise scheduling. Generic "daily study reminder" notifications show 34% lower engagement than slot-targeted ones.

### Slot Distribution in Current Cohort

| Preferred Slot | Learners | Suggested Reminder Time |
|---|---|---|
| Morning | 9 (45%) | 09:00 |
| Afternoon | 7 (35%) | 14:00 |
| Evening | 4 (20%) | 19:00 |

---

## Role-Specific Workload Patterns

### Cloud Engineers
- Average meeting hours: 17.8h/wk
- Focus hours: 14.2h/wk
- Best study window: Morning (67% preference)
- Note: Senior Cloud Engineers frequently pulled into architecture reviews, increasing meeting load above the capacity threshold.

### DevOps Engineers
- Average meeting hours: 14.3h/wk
- Focus hours: 18.1h/wk
- Best study window: Afternoon (57% preference)
- Note: DevOps Engineers benefit from strong focus blocks during CI/CD pipeline maintenance windows — align study sessions with these periods.

### Data Engineers
- Average meeting hours: 20.1h/wk
- Focus hours: 12.8h/wk
- Best study window: Morning (50%) / Evening (30%)
- Note: Data Engineers involved in sprint planning have elevated meeting loads mid-quarter. Schedule intensive study for the first 2 weeks of each quarter.

### Security Engineers
- Average meeting hours: 13.5h/wk
- Focus hours: 19.2h/wk
- Best study window: Morning (75% preference)
- Note: Security Engineers have the lowest meeting load and highest focus time in the cohort — consistently the most exam-ready group.

---

## Microsoft Learn Integration with Work Signals

The ASCENT Work IQ layer is designed to be extended with real Microsoft 365 calendar signals via the **Work IQ MCP** and **Microsoft Graph API**. In the current synthetic deployment:

- Work signals are sourced from `data/work_signals.json` (fabricated)
- In production, the same fields (meeting_hours_per_week, focus_hours_per_week, preferred_learning_slot) would be derived from Microsoft Outlook calendar data via Microsoft Graph
- The Microsoft Learn MCP can additionally surface which Microsoft Learn modules the learner has already completed, allowing the study plan to skip already-mastered content

When both integrations are active, the Engagement Agent can produce hyper-personalised reminders such as: *"You have a 45-minute focus block at 14:00 today — here's the Azure Functions module to continue."*

---

## Scheduling Recommendations by Learner Type

### High meeting load (>20h/wk) — "Condensed" mode
- Session length: 25–30 minutes
- Frequency: 3 sessions/week minimum
- Timing: Evening or early morning before peak meeting windows begin
- Reminder: Single nudge per day, timed to a low-meeting slot
- Avoid: Lunchtime reminders (often consumed by meetings) and end-of-day reminders when cognitive load is highest

### Moderate meeting load (12–20h/wk) — "Steady" mode
- Session length: 45 minutes
- Frequency: 3–4 sessions/week
- Timing: Preferred slot (morning/afternoon/evening per learner signal)
- Reminder: Slot-targeted reminder at start of preferred window
- Ideal: Align with existing focus blocks in calendar

### Low meeting load (<12h/wk) — "Accelerated" mode
- Session length: 60–90 minutes
- Frequency: 4–5 sessions/week
- Timing: Peak focus periods (typically mid-morning for morning-preferred learners)
- Reminder: Daily reminder + optional weekend session nudge
- Opportunity: This cohort can complete certifications 30–40% faster than the stated recommended hours if motivated

---

## Privacy and Data Use Policy

Work signals are used **only to support the individual learner's study scheduling**. Team-level reporting surfaces only aggregate counts and rates — no individual's meeting load, focus hours, or calendar data is ever exposed in manager or team views. The Manager Insights agent is explicitly constrained to aggregate-only output. This aligns with Microsoft's responsible AI principles and the organisation's data minimisation policy.
