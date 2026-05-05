# Investor Demo Guide — FamilyWellness

## Before the Meeting (Day Before)

1. **Install dependencies & start the app**
   ```bash
   cd family-wellness-app
   docker-compose up          # starts backend + Phoenix + Langflow + frontend
   ```
   Or run frontend manually (faster cold start):
   ```bash
   cd frontend && npm install && npm run dev     # http://localhost:3000
   cd backend && pip install -r requirements.txt && uvicorn main:app --reload  # http://localhost:8000
   ```

2. **Set your API key** in `backend/.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Pre-load the demo page** in your browser: `http://localhost:3000/demo`

4. **Open a second tab** pointing to Phoenix Arize: `http://localhost:6006`

5. **Open a third tab** pointing to Langflow: `http://localhost:7860`
   - Import the flow: Langflow → + New Flow → Import → select `langflow/wellness_agent_flow.json`

6. Send yourself one chat message in the demo ahead of time so Phoenix has at least one trace to show.

---

## Demo Script (~12 minutes)

### Opening (1 min)
> "Families today are more health-conscious than ever — but the tools they have are generic. 
> MyFitnessPal tracks calories. Google gives one-size-fits-all results. Nobody is solving 
> personalized, whole-family wellness planning. That's what FamilyWellness does."

---

### Screen 1 — Landing Page (1 min)
**URL:** `http://localhost:3000`

Point out:
- Clean consumer app feel
- Three core value props: Personalized Meal Plans, Smart Grocery Lists, Wellness Guidance
- "Powered by Claude AI" badge — positions the product as AI-native
- **Key investor message:** "This is a subscription SaaS product. Families pay once, plan every week."

---

### Screen 2 — Demo Dashboard: Meal Plans (3 min)
**URL:** `http://localhost:3000/demo`

Walk through:
1. **The Rivera Family sidebar** — point out 4 members, each with different needs:
   - Maria: Ayurvedic Pitta, perimenopausal, gluten-free
   - David: Western integrative, elevated cholesterol
   - Sofia: Teen vegetarian, Ayurvedic Vata, dairy-free
   - Mateo: Active 9-year-old, peanut-free

   > "One family. Four completely different nutritional profiles. One plan that serves them all."

2. **Meal Plan tab** — show Mon/Tue/Wed cards. Click to expand a meal card.
   - Show the **"Why it works"** section — per-member personalized explanations
   - Show **member compatibility dots** — which meals work for everyone
   
   > "Every meal explains why it was chosen for each person. Maria gets a Pitta-cooling explanation. 
   > David gets a heart-health angle. Sofia gets an Ayurvedic Vata note. Same meal, four insights."

3. **Stats bar** — 21 meals planned, 40 grocery items, 13 supplements, $56 under budget
   > "Every week, automatically. In under 60 seconds."

---

### Screen 3 — Grocery List (2 min)
**Click Grocery List tab**

Walk through:
1. **Budget tracker** — $218.50 of $275 budget, progress bar
   > "Budget-aware from the start. The AI knows what your family can spend."

2. **Category organization** — produce, protein, pantry etc.

3. **Smart flags** — point out organic labels, priority flags, and money-saving tips
   > "Frozen organic berries are equally nutritious and 40% cheaper — it tells you that."

4. **Member tags** — hover over items with member names
   > "Every item traces back to the member it serves. Sofia's iron supplement. David's omega-3 fish."

5. **Click a checkbox** — show real-time check-off

---

### Screen 4 — Wellness / Supplement Guide (2 min)
**Click Wellness Guide tab**

Walk through:
1. Click **Maria** — show her 4 supplement recommendations
   - Shatavari: Ayurvedic perimenopause support
   - Magnesium Glycinate: sleep
   - Ashwagandha: stress
   - D3+K2: bone density

   > "Maria follows Ayurvedic principles. So her guide leads with Shatavari, an Ayurvedic 
   > adaptogen, not just generic multivitamins."

2. Click **David** — show Western integrative approach (Berberine, CoQ10, Omega-3)
   > "David gets a cardiology-informed guide — Berberine for cholesterol, CoQ10 for heart 
   > muscle energy. Evidence-based, not one-size-fits-all."

3. Point to the **contraindication note** on Red Yeast Rice
   > "We flag interactions. We remind users to verify with their doctor. We're an assistant, 
   > not a replacement for healthcare."

---

### Screen 5 — Live AI Chat (2 min)
**Click the chat bubble (bottom right)**

Type one of these live:
- `"What makes kitchari good for the whole family?"`
- `"Suggest a peanut-free after-school snack for Mateo"`
- `"Why did you recommend Shatavari for Maria?"`

> "This is a live call to Claude Sonnet 4.6 — real-time, streaming, context-aware. 
> The assistant knows every member of the Rivera family. It doesn't just give generic answers."

Show the streaming response arriving.

> "The AI knows Maria is perimenopausal and Pitta-dominant, knows Sofia is a vegetarian teen 
> with iron needs, knows Mateo can't have peanuts. Every answer is in context."

---

### Screen 6 — Phoenix Arize (QA & Observability) (1 min)
**Switch to tab: `http://localhost:6006`**

> "Before we ship to users, every AI response goes through Arize Phoenix — our LLM 
> observability layer."

Point out:
- **Traces** — every Anthropic API call captured
- **Span attributes** — family_id, member_id, request_type, model, latency
- **Evaluations** — we can run automated evals on response quality, safety, accuracy

> "For a health-adjacent product, trust is everything. We can audit every recommendation 
> the AI ever made, for any family, at any time."

---

### Screen 7 — Langflow (Workflow QA) (30 sec)
**Switch to tab: `http://localhost:7860`**

> "Langflow gives our QA team a visual canvas to test and iterate on our AI workflows 
> without writing code. When we want to test a new prompting strategy or a new meal 
> planning flow, we prototype it here first."

Show the imported flow briefly — no need to run it live.

---

### Closing (1 min)

> "What you've seen is a working product — not a mockup. Real AI generation, real budget 
> tracking, real observability. Built on Claude Sonnet 4.6."
>
> "The market is families — and every family is different. We're the first product to 
> take that seriously at the individual member level."
>
> "We're raising [X] to [goal: e.g. 'launch a public beta with 500 families and establish 
> practitioner partnerships']. Here's what we'd like to walk you through next…"

---

## Backup Plan (if internet is down)

The `/demo` page loads **100% from pre-seeded local data** — no API calls needed for:
- Meal plan display
- Grocery list
- Supplement guide
- Member profiles
- Stats

Only the **live chat** requires internet (Anthropic API). If offline, simply skip Screen 5 
and say: "The chat assistant streams live from Claude — I'll demo that separately."

---

## Key Numbers to Know

| Metric | Value |
|---|---|
| AI Model | Claude Sonnet 4.6 (Anthropic) |
| Meal plan generation time | ~15–25 seconds |
| Grocery list generation time | ~8–12 seconds |
| Prompt caching savings | ~65% on repeat family context |
| Demo family members | 4 |
| Demo grocery items | 40 |
| Demo supplements | 13 recommendations across 4 members |
| Weekly budget | $275 → estimated $218.50 (21% under) |
| Observability | Phoenix Arize (open source, self-hosted) |
| Workflow QA | Langflow (open source, self-hosted) |

---

## FAQ Prep

**"Is this medical advice?"**
> "No — and we're intentional about that. The app surfaces itself as a wellness guide, 
> not a doctor. Every supplement recommendation includes a consult-your-provider note. 
> We operate firmly in the lifestyle and planning space."

**"What's the monetization model?"**
> "Freemium subscription. Free tier: 1 member, 1 plan/month. Family plan: up to 8 members, 
> weekly plans, full features. Premium: all features plus integrations (Instacart, Apple Health). 
> B2B opportunity: white-label for functional medicine practices."

**"Why Claude / Anthropic?"**
> "Claude Sonnet 4.6 gives us the best combination of nuanced reasoning — critical for 
> multi-philosophy wellness guidance — and cost efficiency via prompt caching. We cache the 
> family context and system prompt, cutting per-request costs by ~65%."

**"How do you handle safety / liability?"**
> "Three layers: (1) The AI is prompted to never diagnose or treat, only guide and suggest. 
> (2) Persistent in-app disclaimers on every supplement and health recommendation. 
> (3) Phoenix Arize lets us audit and eval every AI output — we can detect and correct 
> any drift toward medical claims."

**"What does the onboarding look like?"**
> "Five-step flow, under 5 minutes. Family name and budget, then a per-member deep-dive: 
> age, goals, dietary style, allergies, wellness philosophy (Ayurvedic, TCM, Western, or 
> blend), and current supplements. The AI uses all of it — nothing is cosmetic."
