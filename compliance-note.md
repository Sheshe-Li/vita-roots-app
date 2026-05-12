# Compliance Note — Vita Roots Signal Harvester

**Capstone Part 1 · Intelligent Automation Immersive · May 2026**

---

## Data Sources

Vita Roots Signal Harvester interacts with the following data sources during normal operation.

**PubMed E-utilities API** is a public API operated by the National Center for Biotechnology Information (NCBI). No authentication is required. No personally identifiable information (PII) is submitted in queries. Keyword-based searches are used to retrieve article metadata including title, journal name, publication date, author names, and publication type. Raw abstracts are not stored persistently; article records are retained for a maximum of seven days before expiration.

**Open Food Facts** is a public, open-license database of food and supplement products. Queries are keyword-based and contain no user data. Results are used to identify product categories for price monitoring purposes only.

**Supabase (PostgreSQL)** serves as the primary persistent data store. This database contains personally identifiable and health-adjacent information including family names, email addresses, family member ages and health conditions, dietary preferences, wellness philosophies, active meal plans, grocery lists, and supplement guides. Access is restricted to the backend service role key. Row-level security is configured at the database level.

**Resend** is used exclusively to deliver transactional email notifications to family account holders. Email addresses are transmitted to Resend solely for the purpose of delivering approval request and confirmation messages. No marketing or unsolicited communications are sent through this channel.

**Anthropic Claude API** processes family profile data and signal content to perform enrichment matching and support agent responses. Data submitted to the API is governed by Anthropic's data processing terms. No raw health records are submitted; enrichment prompts are structured to include only the minimum context required for the matching task.

---

## Access Controls

All database operations are performed using Supabase's service role key, which is stored as an environment variable and never committed to version control. The `.env` file containing API credentials is listed in `.gitignore`. API keys for Anthropic, Phoenix Arize, and Resend are managed exclusively through environment variables.

The MCP server runs on a separate port (8001) from the main API (8000) and is not exposed to the public internet during development. In a production deployment, MCP tool endpoints would sit behind authentication middleware and would not be accessible without a valid service token.

---

## What Gets Logged

Every meaningful action in the system produces a record in one of two places: the Supabase `audit_log` table or a Phoenix Arize trace span.

The `audit_log` table captures the following events with a timestamp, `family_id`, `entity_type`, `entity_id`, and a JSON details payload: family creation and updates, family member additions and updates, meal plan generation, grocery list generation, supplement guide generation, plan approval requests, plan approval decisions (approved or rejected), grocery approval requests, grocery approval decisions, support ticket creation, support ticket status changes, and signal alert decisions.

Phoenix Arize receives an OpenTelemetry trace span for every call to the Anthropic API. Each span is tagged with `service.name`, `project.name`, `wellness.request_type`, `family.id` where applicable, `signal.type` where applicable, and `approval.decision` where applicable. This provides a complete, queryable record of every LLM interaction with enough context to reconstruct what happened and why.

---

## Approval Gate Design

The approval flow is the primary compliance mechanism for health-adjacent decisions. Its design reflects the stakes and reversibility of each signal type.

Research signals carry high stakes because they concern health decisions, and the consequences of an incorrect plan change are difficult to reverse. Accordingly, no meal plan or supplement guide modification occurs without explicit family approval. The approval request creates a unique, single-use token stored in the `plan_approvals` table. That token is embedded in an email link sent to the family. Clicking the link resolves the token and records the decision. If the family takes no action, the system defaults to "stay the course" and logs the timeout — the plan is never modified automatically.

Market signals carry medium stakes because they concern purchasing decisions, which are financially consequential but operationally reversible. The approval gate follows the same token-based mechanism but applies a 48-hour timeout after which the default action — stay the course — is logged automatically. No grocery list modification or supplement substitution occurs without the family's explicit choice.

All approval decisions, including timeouts, are recorded in the `audit_log` with the decision method (email link or in-app), the timestamp, and the relevant entity ID.

---

## Hard Nos

The following actions are prohibited by design and are not implemented anywhere in the codebase.

No meal plan, supplement guide, or grocery list is modified as a result of a research signal without explicit human approval. The approval gate is not bypassed under any condition, including timeouts.

Animal studies, in-vitro studies, and preprints are filtered out by the signal scorer before an alert is created. These source types receive a score deduction of -3 and will not meet the fire threshold of 5 under normal conditions.

Raw PubMed article records are not stored permanently. The `signals` table includes an `expires_at` column set to seven days from the catch timestamp. Expired records are eligible for cleanup.

Payment card data, government identification numbers, passport numbers, and similar sensitive financial or identity credentials are not handled, stored, or transmitted by any component of this system.

The system does not attempt to bypass CAPTCHA, rate limiting, or bot-detection mechanisms on any external API. PubMed queries include the required `email` parameter per NCBI's usage guidelines.

No email addresses collected from family profiles are used for any purpose other than delivering plan and grocery approval notifications. No marketing communications are sent.

---

## Stakes × Reversibility Map

| Action | Stakes | Reversibility | Gate Required | Timeout Default |
|---|---|---|---|---|
| Meal plan modification via research signal | High (health) | Low | Always | Stay the course (no change) |
| Supplement guide modification via research signal | High (health) | Low | Always | Stay the course (no change) |
| Grocery list modification via market signal | Medium (cost) | High | Always | Stay the course (no change) |
| Support ticket response | Low | High | None (AI-generated, human-reviewed) | N/A |

---

*Compliance is design, not paperwork. These constraints were established at the outset of the build and directly shaped the architecture, database schema, and approval flow implementation.*
