# Protocol structure proposal

**Proposal for [README.md](README.md), reviewed 2026-11-07.** Organize the protocol by health topic, with daily foundations first and clear routes to care, schedules and reference material. This document proposes the layout; the active protocol stays in README.

## Proposed contents

Use **Contents** as the navigation title and unnumbered topic headings. The order below puts foundations before optional optimization and equipment. It is a reading order, not a universal ranking of medical benefit; indicated treatment and unresolved symptoms can take priority.

Above the contents, add a compact shortcut row: **Follow-up · Training plan · Meals · Intake schedule · Results**. Each shortcut links to its authoritative section or file.

| Order | Main section | Subsections |
|---|---|---|
| 1 | **Sleep** | Schedule, daylight & wind-down; Bedroom; Sleep problems & review |
| 2 | **Exercise & movement** | Principles & injury limits; Weekly training plan; Daily movement, mobility & recovery |
| 3 | **Diet & hydration** | Daily menu; Food choices & weekly rotation; Hydration & workout fuel; GI tolerance; Preparation & food safety |
| 4 | **Psychological wellbeing & social connection** | Relationships & social plans; Stress & mental recovery; Work boundaries & leisure |
| 5 | **Prevention & medical follow-up** | Current follow-up; Tracking & results; Tests & screening; Vaccinations; Oral health; Substance use & risk reduction |
| 6 | **Sexual & reproductive health** | Function, libido & comfort; Safer sex & STI care; Fertility & family planning |
| 7 | **Medicines & supplements** | Morning; Lunch; Before workout; During workout; After workout; Evening; Injectables & peptides |
| 8 | **Skin, hair & appearance** | Face; Lips; Eye area; Hair; Eyebrows; Beard; ABS; Body |
| 9 | **Environment & equipment** | Air & ventilation; Water; Cookware; Bedding & textiles; Hygiene; Laundry; Dishwasher care |

Keep these reference sections after the nine main topics:

- **Medical history** — completed surgeries/procedures, recovery history and links to reports.
- **Legend** — existing emojis, evidence medals and signatures.
- **Notes** — Totals; Food & calculation notes; Timing & training; Supplement details; Follow-up; Skin & teeth; Shopping.
- **TODOs / Things to consider** — retain the recent topic groups and add the bounded **Protocol gaps** list below.
- **Removed / unhealthy / redundant items** — retain the recent groups and decision history.

The outline is a target, not a set of empty live sections. Add new subsections when they have useful content; keep unfinished scope in TODOs. Health and Longevity remain goals in the subtitle, rather than catch-all sections.

### Useful deeper links

Keep a compact overview, with deeper links where they help lookup:

- **Training:** Core philosophy and Monday–Sunday; retain each day's exercises, order, weights and repetitions.
- **Daily menu:** Morning, Lunch, Afternoon drink, Before workout, During workout, Right after workout and Dinner. Link to **Notes → Totals** for calculations.
- **Tests & screening:** Laboratory Analysis → Blood / Urine / Stool; Cardiovascular Health; Diagnostic Imaging; Specialist Screenings; Gastrointestinal Health.
- **Face:** Skincare / Home procedures / Professional procedures. **Hair:** Haircare / Home procedures / Professional procedures.
- **Cookware:** Cutting Boards; Knives; Frying Pans; Cooking pot set; Ovenproof dish; Kitchen Utensils.
- **Reference material:** keep the existing Notes, TODO and Removed subsection links added by [#33](https://github.com/PawelTroka/health-protocol/pull/33).

## Where current and incoming content goes

Replace the two good/bad-behavior lists with topic homes. Describe what to do or limit within the relevant topic.

| Current content | Proposed home |
|---|---|
| Smoking, vaping, recreational drugs and alcohol | Prevention → Substance use & risk reduction; Sleep links to the relevant alcohol advice |
| Sugar/sweets, food quality, restaurants/catering/takeaway and drink rules | Diet → Food choices & weekly rotation; preserve the decisions during relocation |
| Sunbathing and UV protection | Skin → Face / Skincare, linked from Prevention |
| Unprotected sex | Sexual health → Safer sex & STI care |
| Sleep disruption, bedtime, DND, daylight, wind-down and caffeine cutoff | Sleep; product doses remain in the intake schedule |
| Overthinking, social media, gaming/TV, productivity and outsourcing boundaries | Psychological wellbeing → Stress & mental recovery / Work boundaries & leisure |
| Meditation and breathwork | Psychological wellbeing → Stress & mental recovery |
| Walks and stretching | Exercise → Daily movement, mobility & recovery |
| Sauna and cold exposure | Exercise → Daily movement, mobility & recovery; link from Sleep when relevant |
| Red Light Therapy | The relevant Face or Hair procedure, with its own device and application |
| Sleep tracking and the other tracking devices | Prevention → Tracking & results; link from Sleep, Exercise and Diet |
| Remaining Testing content | Prevention → Tests & screening, retaining its current subdivisions |
| Existing follow-up Notes and care actions | Prevention → Current follow-up provides a short linked index; supporting reasoning stays in Notes and optional trials stay in TODOs |
| Vaccines | Prevention → Vaccinations, preserving recorded status and dates |
| Oral health / teethmaxxing | Prevention → Oral health; retain the searchable teethmaxxing label and the dental-staining Note link |
| Supplements and drugs | Medicines & supplements, preserving all six timing windows and slot codes |
| Peptides | Medicines & supplements → Injectables & peptides |
| Looksmaxxing | Skin, hair & appearance; keep Looksmaxxing as a searchable alias and retain the existing procedure detail |
| Cookware and Environment | Environment & equipment; keep cookware types nested under Cookware |
| Bedroom conditions vs bedding/air equipment | Sleep owns the operating settings; Environment owns product choices and upkeep, connected by links |
| Surgeries | Medical history; future surgery candidates belong in TODOs until selected |

### Incoming PRs

- **[Sleep #13](https://github.com/PawelTroka/health-protocol/pull/13):** supplies the standalone Sleep routine, including the air/circadian work already merged into it from [#25](https://github.com/PawelTroka/health-protocol/pull/25). Preserve the chosen DND window and other personal settings. Redistribute its **Other recovery habits** using the table above.
- **[Wellbeing #14](https://github.com/PawelTroka/health-protocol/pull/14):** supplies daily connection, weekly social plans, mental reset, work/leisure boundaries and the weekly check-in. Keep these in their own main section. Resolve the old productivity wording within that PR's scope.
- **[Hair #6](https://github.com/PawelTroka/health-protocol/pull/6):** styling instructions belong under Haircare and supporting research in the relevant Note. Refresh it against current Hair content independently of the layout change.

These are incoming content decisions, not missing topics to rewrite from scratch. Snapshot: main at [`ae486e6`](https://github.com/PawelTroka/health-protocol/commit/ae486e69f96031bb83d9092c4ef872f5df383c0d), with #6, #13 and #14 open.

## One home for each instruction

- **Systemic doses and timing:** keep one intake schedule. Sexual health links to Tadalafil, Hair to Dutasteride/oral Minoxidil, and Sleep to relevant Evening entries. Preserve `M`, `L`, `B`, `IW`, `A`, `E`, exact formulations, doses, product links, deliberate order and pillbox mapping.
- **Topical care and devices:** keep application instructions in their body-area routine. Link shared procedures instead of prescribing them twice.
- **Injections:** retain exact formulations and current status per item. “Peptide” is a molecule category, not an evidence or approval category; do not label the whole block experimental or established.
- **Meal and training schedules:** keep the actual plan in one place. Hydration, social-sport and recovery subsections link to scheduled entries where they overlap.
- **Notes, TODOs and history:** Notes explain decisions; TODOs contain pending changes; Removed records past decisions. Keep their recently simplified groups. A structural move does not promote a candidate into current use or resolve conflicting dose statements.

## Protocol gaps to scope

These are proposed research tasks for a small **TODOs → Protocol gaps** group, not new treatment instructions.

- [ ] **Sexual & reproductive health:** develop concise coverage of function/comfort, sexual communication, safer sex/STI care and reproductive goals if relevant; link existing tests, vaccinations and treatments.
- [ ] **Prevention:** distinguish routine screening, follow-up of existing findings and exploratory testing; review indications and due dates in a separate clinical audit.
- [ ] **Care coordination:** surface existing follow-up actions, medicine-review decisions and procedure-related instructions without duplicating the underlying Notes or checklists.
- [ ] **Injury management:** extract the existing exercise restrictions and rehabilitation guidance into a brief Principles & injury limits subsection, linked to medical history.
- [ ] **Hearing & noise:** assess whether a short prevention topic is useful; no new test or device is assumed.
- [ ] **Psychological support:** assess whether #14 needs a concise route to support for persistent symptoms beyond its everyday habits.

Oral care, vision exams, vaccination records, nutrition totals and GI follow-up already exist. Improve their placement and links rather than calling them absent.

## Navigation and migration

1. Land [#33](https://github.com/PawelTroka/health-protocol/pull/33) for immediate subsection navigation. This proposal can be reviewed independently.
2. Review this layout and finish #13/#14 in their own PRs. Refresh the contents after each heading change; #6 remains a separate Hair update.
3. Apply the agreed layout as a move-and-link change. Preserve active entries, quantities, exercise prescriptions, product URLs, signatures and status; handle substantive corrections separately.
4. Add scoped gap content through focused follow-up PRs, keeping evidence and alternatives in Notes or PR descriptions.

Use short, stable IDs such as `sleep`, `sexual-health` and `medicines-supplements`, independent of display order. Preserve old heading IDs as aliases and update internal links when moving or renaming a section. Give repeated leaf headings explicit IDs such as `face-home-procedures` and `hair-home-procedures`. [GitHub's section-link rules](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#section-links) explain why renamed or reordered duplicate headings otherwise change their targets.

During migration, verify that each existing instruction is retained once, all contents links resolve, pending/removed items remain separate, and slot codes and doses are preserved. A layout-only change does not require regenerating the pillbox guide or medical reports.

## Evidence behind the grouping

The sources support including these domains; the exact headings and order are editorial choices.

| Design decision | Basis |
|---|---|
| Give Sleep the same prominence as diet and activity | [AHA Life's Essential 8](https://professional.heart.org/en/science-news/lifes-essential-8) includes sleep alongside diet, physical activity, nicotine exposure and cardiometabolic factors. |
| Give psychological wellbeing and relationships their own main section | [WHO's social-connection report](https://www.who.int/publications/i/item/978240112360) treats social health alongside physical and mental health; its [mental-health overview](https://www.who.int/news-room/fact-sheets/detail/mental-health-strengthening-our-response) includes coping, relationships and functioning. |
| Make prevention and follow-up easy to find | [WHO's NCD framework](https://www.who.int/news-room/fact-sheets/detail/noncommunicable-diseases) includes risk reduction, detection and treatment. Poland's [Moje Zdrowie](https://pacjent.gov.pl/program-moje-zdrowie) integrates health history, lifestyle, mental health and an individual prevention plan. This does not validate every current test or interval. |
| Broaden Sexual health beyond products and hormone values | [WHO's working definition](https://www.who.int/teams/sexual-and-reproductive-health-and-research/key-areas-of-work/sexual-health/defining-sexual-health) covers physical, emotional, mental and social wellbeing, including safe and satisfying experiences. |
| Place oral care within health prevention | [WHO's oral-health guidance](https://www.who.int/news-room/fact-sheets/detail/oral-health) treats dental disease and prevention as health concerns, distinct from appearance alone. |
