# Signal Decision — Vita Roots Signal Harvester

## Signal Types Chosen

### Signal Type 1: Research Signal
**Source:** PubMed, arXiv (nutrition/medicine corpus)
**Trigger:** New peer-reviewed publication that intersects with a family member's active health conditions, goals, dietary style, wellness philosophy, or current supplements

**Why this signal:**
Families trust Vita Roots to give them personalized guidance. That guidance is built on the state of nutritional science at the time of plan generation. Medical knowledge evolves — a supplement that was recommended six months ago may now have new contraindication data, or a dietary approach may have new supporting evidence. Families have no way to track this themselves. This is the signal that makes Vita Roots a living system rather than a static plan generator.

**What noise looks like:**
- Preprints not yet peer-reviewed
- Animal or in-vitro studies (not human trials)
- Studies with sample sizes under 50
- Research unrelated to any active family member's profile
- Duplicate coverage of a signal already surfaced in the last 30 days
- General population findings that don't intersect with any specific member condition or goal

---

### Signal Type 2: Market Signal
**Source:** Commodity price APIs, supplement retailer pricing feeds
**Trigger:** Projected price increase ≥15% or confirmed supply disruption for an item currently in a family's active grocery list or supplement guide

**Why this signal:**
Every family on Vita Roots has a weekly budget. Grocery and supplement recommendations are generated with that budget in mind. When key items shift significantly in price, the plan becomes financially invalid without the family knowing. Early warning gives families real choices: stock up before the increase, find a nutritionally equivalent substitute, or consciously stay the course. Without this signal, families discover the problem at checkout.

**What noise looks like:**
- Price fluctuations under 15% (normal market variance)
- Items not in any active family plan
- Short-term single-day spikes with no projected sustained increase
- Price changes on items the family has already checked off / completed purchasing
- Signals for items the family has flagged as "substitutable" with no preference

---

## Approval Flow Design

Both signals route through a human-in-the-loop gate before any plan modification occurs.

**Research signal gate:**
Stakes: HIGH (health decisions) × Reversibility: LOW
→ Always requires explicit family approval before WellnessAgent regenerates any plan
→ Options presented: Adopt new direction | Flag and revisit in 30 days | Stay the course
→ No timeout default that modifies the plan — inaction = stay the course

**Market signal gate:**
Stakes: MEDIUM (cost) × Reversibility: HIGH
→ Presents options with a 48-hour response window
→ Options: Stock up now | Substitute item | Stay the course
→ Timeout default: Stay the course (logged)

This asymmetry is intentional. Health decisions are irreversible in a way that purchasing decisions are not. The approval gate is stricter where the stakes are higher.
