# Repository agent instructions

These instructions apply to the entire repository. This is a living health-protocol repository: preserve the user's intent, distinguish research from authorization to edit, and never let a generated artifact drift from the canonical protocol.

## Sources of truth and file roles

- `README.md` is the canonical protocol. It owns the active stack, food plan, doses, timing windows, slot codes, display order, Notes, TODO replacements, Removed items, product links and Blueprint/BJ comparison signatures.
- Conversation history explains intent but is not authoritative. Inspect the live files before answering or editing, and perform a fresh audit when asked to re-review.
- `generate_pillbox_guide.py` is the editable source for the physical pillbox guide. It manually mirrors pill entries from `README.md`; it does not parse the README.
- `Supplement-Pillbox-Guide.docx` is generated, checked-in output. Never edit it manually.
- `generate_colored_report.py` contains the structured lab-result data and generates `results.md` and `results.html`. It writes files when deliberately run; do not import or execute it casually.
- Treat raw medical material under `results/`—including images, DICOM data, PDFs and archives—as sensitive, immutable source material unless the user explicitly requests a scoped operation.
- `COST_ANALYSIS.md` is derived and may lag behind the protocol. Do not update one line and leave dependent totals stale; reconcile it comprehensively only when cost analysis is in scope.
- Preserve unrelated modified and untracked user files. Do not add render folders, remote attachments, `__pycache__`, raw results or unrelated artifacts to a commit.

## Authorization and collaboration

- A question, audit, explanation, comparison, or “research but do not change yet” request is read-only. Do not edit the protocol, regenerate documents, change doses, or substitute products.
- When the user asks to change, fix, upgrade, remove or move something, implement the complete in-scope change and update all dependent references and artifacts.
- Never silently add, remove, double, taper or change a prescription medicine or dose. Answer hypothetical medication questions as hypotheticals unless an edit is explicitly requested.
- Preserve the user's existing work and intent. Do not revert dirty-worktree changes or normalize unrelated content.
- Lead with the result. Explain close calls and uncertainty without repeatedly asking the user to choose when a safe, well-supported assumption will work.

## Health-protocol audit method

For every intervention, keep these questions separate:

1. What exact ingredient, active dose and formulation is scheduled?
2. Is its timing window appropriate for food, fat, fiber, exercise, sleep and adherence?
3. Is its approximate evidence-weighted position within that window defensible?
4. What cumulative safety, interaction, duplication and monitoring issues arise across the whole stack?

Additional rules:

- Do not turn a formulation or dose problem into an arbitrary timing move. Conversely, better absorption or pharmacokinetics does not by itself establish a better clinical outcome.
- The displayed order is an approximate ranking by expected marginal benefit, evidence, formulation confidence, protocol fit and risk. It is not necessarily a minute-by-minute swallowing sequence.
- Avoid rank churn over negligible or uncertain differences. Recommend a move only when the expected distinction is material and reasonably supported.
- Empty compartments belong at meaningful evidence-benefit gaps, not automatically at the end.
- Recalculate aggregate exposure across foods, medicines, powders, blends, pills and conditional products. Use scenario-specific totals when relevant: rest, workout, sauna, fatty-fish and non-fatty-fish days.
- Preserve distinctions among active-base mass, salt or complex mass, extract mass, raw-material equivalent, DER, standardization percentage and actual daily active dose.
- Favorable biomarkers observed while the stack is active do not prove an intervention is redundant; the untreated counterfactual is unknown. They also do not prove that the intervention caused the favorable result.
- Do not let supplement optimization displace follow-up of a materially abnormal result. In particular, probiotics, fiber and butyrate are not substitutes for appropriate evaluation of inflammatory gastrointestinal findings.
- Timing separation must not be presented as eliminating a systemic pharmacodynamic or metabolic interaction.

## Research and evidence standards

- Browse again for information that can change, including exact labels, serving instructions, recalls, regulatory status, current formulations, prices, stock and Polish availability.
- Prefer sources in this order: official label/manufacturer documentation; EU, EFSA or another regulator; trial registry; peer-reviewed human trials; high-quality systematic reviews. A retailer can establish that an exact SKU is purchasable, but should not support an efficacy claim.
- For Poland availability, distinguish ordinary Polish/EU retail access from marketplace import, freight forwarding and regulatory-grey direct import.
- Verify the exact finished product whenever possible: serving size, plant part, DER, active standardization, delivery system, branded raw material, capsule matrix, finished-batch potency and contaminant testing.
- Explicitly distinguish:
  - an exact finished product from a branded ingredient or generic molecule;
  - a finished-capsule assay from a raw-material purity certificate;
  - pharmacokinetics or biomarkers from functional and clinical outcomes;
  - an acute tracer response from durable adaptation;
  - short-term tolerability from chronic safety;
  - mechanistic plausibility from demonstrated human benefit;
  - absence of evidence from evidence of no effect;
  - a regulatory maximum or ADI from an acute-toxicity threshold.
- “Best” must identify the criterion: evidence-first, potency-first, analytical transparency, practical Polish availability, value, or protocol fit. Do not manufacture one universal winner when these differ.
- Never assume synergy merely because ingredients are sold together. A combination requires direct evidence and should preserve dose traceability.
- Use calibrated language. Prefer “low expected marginal benefit” over “useless” or “redundant” unless duplication is actually established. Avoid false certainty such as “120% sure.”
- Do not freeze prices, availability, product winners, dose limits or literature conclusions in this file; reverify them and document current conclusions in `README.md` or its Notes.

## Current user-established decision constraints

These are workflow constraints, not immutable medical facts. Preserve them unless the user explicitly reopens the decision. If materially stronger evidence conflicts with one, report it clearly instead of silently overwriting the protocol.

- Retain the post-workout EAA as a low-Calorie muscle-protection and under-eating insurance layer. Keep it as a post-workout bolus with WPI; do not move it intra-workout, duplicate it or remove it as merely redundant.
- Retain the standalone pre-workout Collagen serving even though MicroVitamin+ also contains Collagen.
- Keep Cocoa Flavanols at Lunch.
- Keep UC-II pills before the WPI/EAA drink, and preserve the explanation that the pills are swallowed first.
- Keep HBCD intra-workout rather than automatically adding or moving another full dose pre-workout.
- Keep Aged Black Garlic above Phosphatidylserine. Do not demote Garlic solely because current Blood Pressure, ApoB or Triglycerides are favorable.
- Pending the planned repeat thyroid testing, do not treat Ashwagandha as the established cause of the thyroid result or demote/remove it solely for that reason. Continue to state uncertainty and appropriate monitoring honestly.
- Preserve the deliberate visual orders of Morning WPI above MicroVitamin+ and pre-workout Collagen above Creatine monohydrate. These are display preferences, not claims of biological superiority.
- Fisetin remains removed unless the user explicitly asks to reconsider it in light of materially stronger human evidence.
- Keep standalone PQQ separate/TODO rather than assuming a CoQ10-PQQ combination is synergistic or automatically superior.
- Do not reposition Maca, Tribulus, Fenugreek or CaAKG merely for organizer aesthetics or a negligible evidence difference.

## Protocol writing and formatting

- Use compact number-unit forms everywhere in the protocol and guide: `1g`, `250mg`, `1,000IU`, `1scoop`, `1tbsp`, `1pill`, `200mln CFU`. Leave natural prose durations such as “12 weeks” readable.
- Use `~` only for a genuine estimate, not for a labeled scoop or capsule count.
- Keep timing sections compact. Do not insert gratuitous blank lines directly after timing headings, before `🥤 drink:`, before `🥤 intra-workout drink:`, or between the final drink entry and `💊 pills:`.
- Active protocol names should normally lead with the ingredient, form, strain, plant part or meaningful standardization rather than marketing copy.
- Preserve a make or proprietary identifier when it materially defines identity, formulation, trial provenance or the user's selected product. Existing meaningful examples include Pamako, MicroVitamin+, `35624®`, `Gastrus®`, Pycnogenol, ErgoActive®, Longvida® SLCP™, Ceratiq®, KSM-66, UC-II®, Transparent Labs BULK with `"White Cherry"`, and ALLHydrate Electrolytes Neutral.
- Preserve exact product links and Blueprint/BJ signatures. Do not delete them as “marketing names.” Product and branded-formulation names are freely usable in Notes and TODO comparisons.
- Preserve established wording such as `Creatine monohydrate`, `Whey Protein Isolate (WPI) Unflavored` and `Essential Amino Acids (EAA) Unflavored`.
- Do not add prose already conveyed by the slot code: no `shared slot`, `one capsule per slot`, `one softgel per slot`, or obvious multiplied totals such as `(1,000mg total)` when the multiplier and dose already make it clear.
- Do not add the word `total` after a combined CFU headline unless genuine ambiguity requires it.
- Emojis should represent genuinely distinct intended benefit areas. More than one is allowed; do not cap the guide at two merely for aesthetics.

## Slot-code system

- Use only `M`, `L`, `B`, `IW`, `A` and `E` for Morning, Lunch, Before Workout, Intra-Workout, After Workout and Evening. Do not restore `BW` or `AW`.
- Zero-series codes such as `M.0.2` identify drinks or powders outside the organizer and consume no physical compartment.
- Use `.1` and `.2` for distinct small pills that share one physical compartment.
- Use a range such as `M.5-6` when large pills occupy separate compartments.
- Use one code plus a leading multiplier, such as `M.15 3x`, when several small identical pills share one compartment.
- Slot-code references replace old numeric Note superscripts. Nested ingredient paths may extend zero-series codes, for example `M.0.3.2.1`.
- Preserve strategically positioned empty slots and the physical organizer capacity. Do not collapse or move gaps without checking the evidence-tier meaning and pill dimensions.

## Notes, TODOs and Removed items

- A Note should cover one coherent topic. Do not dump analyses of unrelated supplements into one Note.
- Add a Note when it materially explains totals, timing, formulation identity, dose uncertainty, safety, an interaction or a consequential decision—not merely to justify every active row.
- Notes may name exact brands, finished products, proprietary delivery systems, trial products and alternatives.
- Keep cross-source totals traceable with slot-code references to every meaningful contributor.
- When removing an intervention, delete it from the active stack, free or strategically reassign its slot, remove/update its focused Note, and add it to `Removed / unhealthy / redundant items` with the former exact formulation, the reason and appropriate evidence. Update all totals and cross-references.
- TODO replacements must state why the candidate could be better, whether it is available in Poland, and whether the advantage is formulation, verification, dose convenience or clinical provenance rather than proven superior outcomes.

## Pillbox-guide synchronization and document QA

Every change to an active physical pill's code, order, name, dose, multiplier, conditional use, icon set, empty slot or meaningful formulation identity must be mirrored in `generate_pillbox_guide.py`.

- The guide's prominent ingredient name must match the README entry. Dose and count may occupy their dedicated guide fields, but do not invent shorter or generic aliases that lose meaningful identity.
- Show `2x` or `3x` before the supplement name when multiple identical pills share one compartment.
- Do not place zero-series drinks or powders into pillbox cells.
- Preserve exactly eight 3x3 pages: Morning 1/2, Lunch 1/2, Evening 1/2, Before Workout and After Workout. Each page has nine physical cells.
- Keep the visible guide-header date current whenever the document is regenerated.
- Never hand-edit `Supplement-Pillbox-Guide.docx`.

After an authorized pillbox-affecting change:

1. Update `README.md` and `generate_pillbox_guide.py` together.
2. Use the bundled workspace Python runtime to compile and run `generate_pillbox_guide.py`.
3. Use the `documents` skill and its current `render_docx.py` workflow to render the DOCX to page PNGs, optionally with a PDF.
4. Confirm there are exactly eight pages and visually inspect every page—not only the changed page—for clipping, overflow, row-major placement, codes, names, doses, multipliers, emojis, conditional warnings and empty cells.
5. Search the generated document or extracted text for stale names, doses and old `BW`/`AW` codes.
6. Run the repository validation checks below.

## Validation and hygiene

For ordinary protocol edits, run at minimum:

```powershell
git status --short
git diff --check
git diff -- README.md generate_pillbox_guide.py
```

For pillbox changes, also verify the Python data structure without generating output:

```powershell
python -B -c "import generate_pillbox_guide as g; assert len(g.PAGES) == 8; assert all(len(p['cells']) == 9 for p in g.PAGES); cells = [c for p in g.PAGES for c in p['cells']]; assert len(cells) == 72; assert len({c['code'] for c in cells}) == 72; print('8 pages, 72 unique physical cells')"
```

Use the bundled Python path returned by the workspace-dependency loader if the system `python` lacks `python-docx` or the rendering dependencies.

When intentionally changing lab-result source data, run `generate_colored_report.py` only from the repository root, then inspect both outputs:

```powershell
python -B .\generate_colored_report.py
git diff -- results.md results.html
```

Do not commit, publish or push unless the user explicitly requests it.
