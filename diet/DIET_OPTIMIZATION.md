# Diet delivery optimization

**Current state23September:** Bioshi357/361/370 are active. Nut A370/order246975 is paid133.61zł with free GLS; IdoPay confirms its active card while the parent verification notice updates. Use the [renewal plan](DIET_RENEWAL_PLAN.md), [activation calendar](DIET_ACTIVATION_ROLLOUT.md) and [payment handoff](DIET_PAYMENT_HANDOFF.md) for current dates and required actions. Older schedules and quotes below are historical; they are not activation instructions.

Adopted **2026-09-14**. Find a genuinely automatic purchasing-and-consumption schedule that supplies every required meal category and minimizes freshness loss when food is eaten, within the agreed Diet, budget and free home-courier requirement. **The current six-fresh/six-pantry proposal is a candidate, not a demonstrated feasible solution or a solved optimum.**

The canonical [Diet](../README.md#4-diet) defines permitted foods, quality, preparation, portions and rotation. The [coverage model](DIET_ROTATION_COVERAGE.md) supplies provisional meal allocations; the [delivery schedule](DIET_DELIVERY_SCHEDULE.md), [shopping inventory](DIET_SHOPPING_PLAN.md), [subscription audit](DIET_SUBSCRIPTION_AUDIT.md) and [cost model](DIET_SUBSCRIPTION_COSTS.md) own current quantities, evidence and status. This specification does not activate orders, change portions or authorize substitutions. Where the older plan relies on routine skips, sharing or manual refills, those remain disclosed exceptions rather than proof of compliance with the adopted constraints.

The [executable quantity comparison](DIET_RENEWAL_MODEL.json) and [offline audit](../tools/plan_diet_renewals.py) add a verified500g Oat candidate:500g/30days plus500g/60days, or1kg/60days plus500g/60days, each exactly25g/day. This expands the restricted300g/1kg search below. The tested79.27zł Oat/Macadamia shipment fails free home courier; arithmetic balance alone does not release it.

## Hard constraints

| Requirement | Acceptance condition |
| --- | --- |
| Complete category-meal coverage | Every required category at every planned eating occasion receives its full written portion from an approved food. A pack is converted using its actual edible yield and the food's prescribed portion. One CHOOSE ONE selection cannot silently become a mixture of species or foods. Having every alternative in stock simultaneously is unnecessary. |
| Unchanged Diet | Preserve portions, preparation, quality and required variety, including **6×Tempeh200g +12×Eggs200g shell-free +10 Fish dinners per28days**, alongside the separate Lunch Protein and weekly Fish rules. Extra meals, larger portions or deleting perishable choices cannot repair a purchasing problem. |
| Usable inventory | Allocate each quantity once, after its actual arrival and before its effective expiry. Track batch identity, remaining edible quantity, arrival, opening, storage and expiry. Gross produce weight, dry/cooked conversions and Egg counts are not guaranteed edible yields. |
| Free home courier | Every recurring shipment must have a verified0zł home-courier charge at its applicable recurring prices/discounts and composition. Lockers and pickup points do not qualify. Include any packing/handling fee in the delivered budget; whether such a fee also violates the intended meaning of free delivery must be an explicit input. No surplus purchases just to qualify. |
| Delivered-price cap | Each subscription product costs no more than125% of a comparable manual purchase, normalized to the same meaningful form and usable quantity, including compulsory fees. Unrelated savings cannot hide an over-cap item. No whole-Diet numeric budget was supplied; record full recurring and transition costs separately. |
| Zero planned waste | All purchased edible food has a permitted consumption assignment before expiry. Normal inedible trim uses a measured yield; it cannot conceal edible waste. Sharing is not the user's meal coverage or an automatic balancing device. It requires separately agreed, fixed demand if included at all. |
| No stock drift | After the transition, each food's delivered edible quantity equals its consumption over the complete repeat period, with no planned discard. Usable quantity **and age/opening/expiry distribution** repeat across the boundary. A permanent reserve is stock, not recurring consumption. |
| Native repeatability | Retailer subscriptions only, explicitly selected18September. Pack quantities, dates, intervals, payment and any alternating pattern must be supported and verified by the retailer. Saved lists, reminders, routine Codex orders and manual skips/quantity/date edits do not meet this requirement. Monitoring handles exceptional disruption; it is not the normal ordering mechanism. |

Coverage must also survive an agreed delivery-delay buffer `Δ` and the stated yield/lifetime assumptions. Until these are specified, a nominal calendar proves neither continuous availability nor robustness. Existing usable stock and already-created orders belong in a separate transition; credit only verified quantities and arrival status, and remove overlapping renewals before replacements start.

## Freshness objective

Let `e` identify a fixed meal-category event, `t_e` its eating time, and `b` a delivered batch. Let `x_be` be the fraction of that event's prescribed food portion drawn from batch `b`, and `w_e` its fixed category/meal weight. For required events, `Σ_b x_be=1`; a split across batches is allowed only for the same permitted food where the portion rules allow it. The food-specific edible quantity consumed is `q_be×x_be`, where `q_be` is its written portion in the appropriate weighing basis.

```text
                        Σ_b,e w_e × x_be × (t_e − a_b) / L_be
Minimize F =            ────────────────────────────────────
                                   Σ_b,e w_e × x_be
```

Here `a_b` is arrival and `L_be>0` is usable lifetime remaining at arrival under the actual storage/opening plan. For an ordinary pack:

```text
effective_expiry_b = min(unopened_expiry_b, opening_time_b + opened_life_b)
L_be              = effective_expiry_b − a_b
a_b ≤ t_e < effective_expiry_b, interpreted at the label's actual precision
opening_time_b ≤ t_e for every portion requiring the pack to be opened
```

Opening times and labels therefore constrain both feasibility and the score. No generic shelf life replaces the delivered batch's label or a verified supplier guarantee. Where preservation is permitted by the written food form, record the original arrival and a validated storage/expiry path; freezing, repacking or opening another container cannot reset the arrival clock. Preserved food does not automatically count as a required raw/fresh choice.

The weights, event set and choice/variety constraints are fixed **before** comparing schedules. Pack splitting leaves the same `x` and total weight; it cannot improve the score. Numerous spice packets cannot create extra weighted events and overwhelm meals. Optional CHOOSE ANY foods need an agreed selection frequency and weight, not invented daily demand. Do not improve `F` by deleting a category or changing the agreed rotation. Until weights and remaining lifetimes are supplied, report feasibility gaps and sensitivity ranges rather than a fabricated numeric optimum.

`F` measures the fraction of remaining usable life spent in storage; it is a scheduling proxy, not a direct assay of harvest freshness, nutrient retention or health benefit. Incoming quality remains a constraint. Compare feasible schedules on the same horizon and assumptions. Among schedules within an agreed tolerance `ε` of the lowest `F`, prefer lower delivered cost, then fewer unnecessary deliveries. Delivery count and duplicate pack count are decisions, not objectives or arbitrary limits: pack counts are nonnegative integers subject to actual minimums.

For each food and a full repeat period `H`:

```text
ending_stock = starting_stock + delivered_edible_quantity − eaten_quantity
ending_age_state = starting_age_state
```

With zero planned waste and repeatable stock, delivered and eaten quantities must match. `H` may exceed28days: existing28/90-day patterns with180-day alternation have a1260-day common period, but parity still needs native support. Matching average quantities is necessary and insufficient: verify every meal and expiry, including the cycle boundary. A shorter analytical proof is acceptable when it establishes the same state recurrence.

## Current six-fresh / six-pantry audit

| Issue in the live candidate | Consequence and next check |
| --- | --- |
| Five10-Egg cartons/28days versus approximately48 Eggs for12×200g meals | Nominal surplus is2 Eggs/cycle; a400g startup reserve does not absorb it indefinitely. Skipping a carton roughly every five cycles is routine intervention. Actual shell-free yield must replace the count estimate. |
| Oats2.3kg/90days versus25g/day =2.25kg | Adds50g/cycle. The proposed omission of300g roughly every six cycles is not a fixed automatic schedule. |
| Black Beans and Chickpeas in alternate90-day cycles | Effective180-day ordering depends on manual omission; native alternation/custom180days is not verified. Their total meal allocation and cooked yields also need a repeating schedule. |
| Spices use stock-triggered omissions; Cinnamon/Cloves are initial additions | No fixed consumption frequency proves recurring quantities, especially CHOOSE ANY selections. Initial one-off purchases are valid transition entries but do not demonstrate native replenishment. |
| Other pantry balances remain approximate | Morning Seeds650g/90days versus630g if all three packs repeat gives20g surplus; Dinner Seeds600g versus630g leaves30g uncovered. Quinoa500g versus approximately482g dry demand depends on an illustrative yield. Fixed Oil supply and optional uses likewise need exact allocation. |
| Fresh remainders and Sauerkraut |50g Shiitake,20g Radish, Berry/Mushroom buffers and other pack remainders need later same-food assignments. Two800g Sauerkraut jars versus14×100g fresh choices leave200g; sharing is not a self-consumption solution. Label conflict of3 versus7days remains unresolved; two later permitted preserved choices could balance quantity only if the agreed fresh rotation and later Ferment purchases are preserved. |
| Arrival does not prove usable life | Tempeh remaining life, Tomato ten-choice storage, Kiwi ripeness, Mushroom carryover, edible yields and the second Sauerkraut jar's unopened life are unverified. Three Tempeh packs per F2/F5 satisfy six dinners arithmetically; they still require suitable expiry and meal timing. |
| Coverage is partly manual or unavailable | Fish/Lunch Proteins, multiple Vegetable categories, Microgreens, Fruit, Ferments, Milk, specialty Mushrooms and pantry top-ups still rely on manual sourcing. Blueberries and Radish block complete fresh baskets; several fallback foods are unavailable. Counts-only choices receive no usable-stock or automation credit. |
| Free GLS evidence is limited | Available-food fresh baskets and revised P2 have delivery-method-step quotes, not complete final/renewal guarantees. Other pantry final reviews and existing next-renewal quotes prove only their recorded compositions. Public courier terms do not establish a universal GLS threshold. |
| Budget and transition are incomplete | The current43-food model is a partial purchasing estimate, with hypothetical10%/15% scenarios; no numeric whole-scope cap is recorded here. Existing pending/held orders and incorrect paused359 must be reconciled before replacements. The candidate has no fully verified recurring payment/phase configuration. |

These findings prevent a claim of full feasibility even if all twelve phase names and lists exist. The [coverage model](DIET_ROTATION_COVERAGE.md) remains useful for constructing the complete meal calendar; its routine corrections must become verified native rules or be explicitly acknowledged as outside the fully automatic solution.

## Balanced quantity candidates to verify

1. **Balance Eggs using the verified interval set.** Four one-carton streams at **14/30/30/30days** supply `10/14+3×10/30=12/7 Eggs/day`, exactly48 nominal Eggs/28days. **14/21/28/60days** is another exact match. Each supplies72 cartons/720 Eggs over420days, matching180 four-Egg dinners. An exact-rational enumeration of one to four one-carton streams over7/14/21/28/30/60/90days found these two matches at four streams; it does not establish a global freshness optimum. Allocate them to qualifying mixed-food groups where possible, not assumed free Egg-only parcels. The21/28-day streams preserve weekdays, while30/60days drift; actual phase rules, category coverage, expiry, delay buffer, recurring cost and200g shell-free yield still control feasibility. These are candidate rates, not configured orders.
   A custom-cycle alternative is six10-Egg streams every35days: `6×10×28/35=48 Eggs/28days`, with24 cartons/140days. The native editor was checked14September and exposes only7/14/21/28/30/60/90days, **not35days**. An automatically supported24-carton/140-day pattern would also balance nominal counts, but neither custom option may be assumed or replaced with routine manual skips. The rate candidates are alternatives, not cumulative purchases.
2. **Remove Oat drift using existing packs and interval choices.** Two streams of the same plain gluten-free300g Oats, every**21days and28days**, supply `300/21+300/28=25g/day`; over84days, seven packs supply2.1kg. This avoids the current50g/90-day surplus and manual300g omission. Verify the exact SKU's offered cycles, minimum, phased coverage, opened life, mixed-basket home delivery and delivered cost; smaller packs may carry a premium. It is the sole exact match found among one/two streams of300g or1kg packs using the seven verified interval choices, not proof of the best overall schedule. One1kg/40days or300g/12days also balances mathematically, but those custom intervals are unverified alternatives only.
3. **Separate slower pantry demand from90-day bundles.** Test actual180-day Beans/Chickpeas or native alternating compositions; derive spice replenishment from agreed choices. Both custom-cycle support and free courier for the resulting baskets remain inputs. Move only genuinely due pantry purchases into fresh shipments when this improves feasible grouping without earlier stock accumulation. IdoSell configuration flexibility does not establish Bioshi customer availability.
4. **Build the complete meal/batch ledger first.** Use the coverage model's approved alternatives to fill every category and identify exact quantities still lacking. Seek smaller compatible packs and automatic routes for those gaps, retaining the written forms. Keep manual sourcing labelled as an unresolved automation exception. Changing to another approved alternative still requires the stated rotation/variety and full stock, price and native-capability checks.
5. **Then compare delivery phases.** Use six fresh phases as one baseline; test additional or fewer phases only when the same needed food can arrive closer to consumption while all constraints hold. Do not add a pantry-only parcel or buy extra food merely to increase delivery count. Resolve Sauerkraut's label and fresh-use requirement before optimizing its cadence.

### Numerical repair checks — 15September

These calculations establish quantity rates under the stated assumptions; **none is an activated subscription or a proof of free courier, usable life, whole-Diet coverage or optimality**.

| Category | Verified calculation and practical implication |
| --- | --- |
| Oats | Same300g pack every21days from day0 and every28days from day4 supplies exactly25g/day: seven packs/84days. With steady25g/day consumption and arrivals before use, inventory returns to0g at day84 and peaks at525g. A permanent50g reserve covers a modeled2day delivery delay and raises the nominal peak to575g; it is startup stock, not extra recurring demand. Actual SKU cycles, dates, expiry and courier grouping remain to verify. |
| Nuts | Existing P1–P6 quantities300+500+300+350+150+200g already sum to1,800g/90days, exactly20g/day. Preserve that combined rate while phasing the four varieties and deducting opening stock; no recurring quantity increase is needed. Quantity balance alone does not verify freshness or a repeatable meal allocation. |
| Eggs | Four10-Egg carton streams every14/21/28/60days supply `10/14+10/21+10/28+10/60=12/7 Eggs/day`:48 nominal Eggs/28days and720/420days. This matches12 Egg dinners/28days **only under the provisional four Eggs =200g shell-free assumption**. Actual edible yield, phases, expiry and qualifying mixed shipments remain necessary. |
| Seeds | With fixed native periods7/14/21/28/30/60/90days, the common period is1,260days. Each daily7g Seed category consumes8,820g in that period. If every available pack is a multiple of50g, fixed integer-pack subscriptions can deliver only multiples of50g;8,820g leaves a20g remainder, so exact zero-drift replenishment is impossible within that restricted pack/period set. Morning650g/90days is7.222g/day, exceeding demand by20g/cycle. Seek a compatible smaller pack, additional verified interval or native variable-quantity pattern; changing the7g serving or relying on routine manual skips is not a repair within the agreed constraints. |

## Inputs and acceptance

Required inputs are: the numeric budget and scope; category/meal weights and `ε`; full required/optional meal frequencies; measured edible yields and any agreed uncertainty bounds; batch remaining/opened life and storage permissions; opening stock with age; actual incoming orders; delay buffer `Δ`; exact vendor-supported pack/minimum/interval/phase/alternation capabilities; and recurring delivered prices, discounts and fees. Delivery-date selection, dispatch estimates and arrival guarantees must remain distinct.

For each candidate, record **feasible / infeasible / unverified** for every hard constraint. Accept only after a dated meal-and-batch allocation establishes full coverage, no expiry violations, equal quantity and age state across repetition, budget compliance, and verified native renewals with free home courier. Present `F` only with its inputs, assumptions and comparison horizon. If no candidate passes, report the smallest concrete conflict and the merchant capability or user input needed; do not label a manually maintained workaround fully optimized.

Official checks informing the current uncertainty: [Bioshi delivery](https://bioshi.pl/pl/delivery), [Bioshi terms](https://bioshi.pl/pl/terms), [IdoSell subscription capabilities](https://pomoc.idosell.com/sprzedaz/sprzedaz-subskrypcyjna). The public pages do not establish a universal free-GLS renewal rule or prove35/40/12/180-day Bioshi presets. Historical account10%/15% confirmations remain evidence for those subscriptions, not automatically transferable to new ones.
