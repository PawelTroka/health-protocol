# Complete Diet demand and shipment plan

## 22 November: protein purchasing quantities on hold

The live [README Diet](../README.md#4-diet), changed by `2c772ea` on21November, restores Tempeh and removes Dinner Turkey and the fixed rotation. Preserve it. The27October scenario of12Egg/6Turkey/6Salmon/2Mackerel/2Sardine dinners,3,900g Turkey and900g Salmon per28days is historical, not current canonical demand or activation quantities. Reconcile meal frequencies before sizing new Protein purchases; infer no new frequencies, substitutions or Tempeh order. Exact Turkey and skinless Salmon sourcing may continue. Keep361 paused and all Bioshi settings unchanged. [Reconciliation hold](DIET_PAYMENT_HANDOFF.md#22-november-incoming-review-and-protein-reconciliation).

## 18 November: remove cancelled257757 from incoming supply

Today's Bioshi order and shipment show **Anulowane**, confirming cancellation of all four foods: Eggs, Cauliflower, Carrots and Raspberries. Allocate none of257757 to upcoming meals or received stock. The original99.25zł payment remains recorded, with99.25zł removed and revised order total0zł; no replacement purchase is booked.

Refund payment remains unverified. The17November messages conflict between return to the original payment method and a later bank-account-details request; the earlier unspecified Cauliflower refund must not be added to99.25zł. Profile399's saved foods retain their5November source date, and the order cancellation does not prove its profile was cancelled. Keep Bioshi unchanged. [Current evidence and refund action](DIET_PAYMENT_HANDOFF.md#18-november-order257757-cancelled-refund-action). Earlier dated accepted-order snapshots below are historical.

6November: the merchant email received5November23:37:03 Warsaw confirms Tomato removal from old255381. Keep its27October22.27zł issued refund and28October carrier delivery separate; bank credit remains unknown. This does not change the future357 template. [Dated clarification](DIET_PAYMENT_HANDOFF.md#6november-review-old-tomato-removal-clarified-no-new-action).

## 5November — pantry carrier delivery verified; usable stock uninspected

The order-linked InPost parcel **520000012680462133044051** is **Doręczona**. Expanded carrier history records delivery **2November2026,10:02**, verified5November; the carrier prints **no timezone**. This is **500156 = legacy258958, one paid pantry lot**, not extra Nuts/Oats. Bioshi still shows W drodze /paid344.52zł/free InPost with14SKU/18 ordered packs. Carrier delivery supersedes the earlier estimate, while contents, condition, actual quantities, expiry and today's usable balance remain unknown.

Expanded257757 remains **Przyjęte /PAID99.25zł/free GLS with all four ordered foods**. The earlier4November schedule has passed; no order-linked tracking, revised ETA or arrival is verified, and the elapsed date alone does not establish a delivery failure. Six active profiles plus paused361 remain unchanged;361 still contains Tempeh. No Bioshi account or financial changes were made. [Current evidence](DIET_PAYMENT_HANDOFF.md).

**Yōkiro5November preparation:** the saved4×30g/60day cart remains109.21zł first goods. Previously approved contact fields persisted without re-entry. First **InPost Kurier HOME** was selected and remained selected after reload, with **109.21zł first total/free HOME**. The separate **Recurring shipments** section still lists **InPost Paczkomat8.99zł/60days** alongside151.20zł recurring goods; this does not establish renewal HOME delivery or its cost, and lockers are excluded. The old panel-close handoff is superseded; do not repeat it. Renewal HOME configuration, delivered-price qualification and final terms/payment remain unresolved. No card, terms acceptance, order, payment or activation occurred; the2November0g Matcha report remains the latest balance.

## Historical2November direct execution — automatic suppliers chosen; external Matcha checkout prepared

The user explicitly chose **“Prioritize fully automatic suppliers”** rather than configuring Bioshi plans that require manual renewals. Keep Bioshi profiles, orders and financial schedules unchanged. Current published [Bioshi terms](https://bioshi.pl/pl/terms) §§4.7 and5.3 require customer checkout submission/payment each cycle; §5.1.1 claims old automatic orders/card collections ended23October2026. The independently verified399 debit on29October remains valid historical evidence, with the cutoff discrepancy unresolved. Six active profiles do not establish future unattended meal coverage.

| Prepared external route | Current verified state / remaining action |
| --- | --- |
| [Yōkiro Traditional Japanese Matcha](DIET_YOKIRO_ACTIVATION_02NOV.md) |4×30g every60days =120g/60days =2g/day. Four sealed packs open sequentially for15days each. Loaded checkout goods109.21zł first after promotion; recurring goods151.20zł/60days. Checkout explicitly displays automatic renewal/collection until cancellation, but the mandate has **not** been accepted. |
| HOME costs and first timing |The user approved sharing existing Bioshi delivery address,email and phone with Yōkiro; the corresponding fields are filled, without reproducing those details here. Checkout now lists first InPost Kurier HOME10.99zł→FREE. The method is not verified selected: the Brave extension panel blocked input and the user has been asked to close it. Actual recurring HOME charges and first arrival remain unverified. At the10% rule first logistics must be≤10.92zł and renewal≤15.12zł. The user reports0g Matcha, superseding historical stock; the60day cycle does not defer the immediate first order. |
| Matched price comparison |The same four sealed30g packs are currently126.01zł via3-pack84.01zł +single42zł before shipping. Renewal151.20zł is approximately20% higher in goods arithmetic; actual shipping on both routes still controls the25% delivered cap. The100g89zł alternative has different opening duration and must not be silently ignored. |
| [Zielono standing-delivery request](DIET_ZIELONO_STANDING_REQUEST_02NOV.md) |SENT2November20:01:45 Warsaw after explicit approval, including routine clarifications within this same request. Outgoing recipient, subject and full body verified; actual UTC time/message ID recorded in the request file. Requests210g edible Watercress Microgreens/week (7×30g, replacing shared category choices rather than adding food), optional custom150g Maitake/28days, fixed composition, unattended billing, usable life and an itemized consumer HOME quote. No quote, accepted order or activation yet; no resend. |

Yōkiro remains **unpaid/unactivated**: authorized address/contact entry is complete, but HOME selection/recurring fee, card, terms acceptance and final order are not verified. Continue the actual HOME check after the extension panel is closed, confirm first arrival against the reported0g reserve, then obtain the required final terms/payment approval. After real activation, verify accepted quantities/cycle and reconcile the canonical same-food link; do not count the cart as automatic coverage. Bioshi stays unchanged. The earlier Bioshi fresh/ambient combinations below remain offline composition research, not current activation instructions under the user's latest decision.

## 2November — full live re-audit supersedes old availability gates

The [single coverage map](DIET_AUTOMATION_GAPS.md) now reflects the full Diet inventory:49 fresh alternatives,35 pantry/foundation entries and8 protein groups, with overlapping/optional entries kept distinct from mandatory demand. Supported signed-in Brave checked61 actual Bioshi product pages:50 available and11 unavailable for new orders. The [structured live record](DIET_LIVE_BIOSHI_AUDIT_02NOV.json) contains exact SKUs, displayed goods prices, native controls and catalogue contradictions; these are not accepted destination quotes or reservations.

**Corrected preparation candidates:** Klimeko400g lactose-free organic live Kefir; exact Moya30g and Japanese organic60g Matcha; Flax/Chia/Pumpkin and matching organic Sunflower; organic King Oyster200g; Spinach/Kohlrabi/Celeriac/roots/Oranges and Arugula. Ordinary brands are flexible when meaningful food attributes match. Do not repeat their old blanket unavailable/no-product exclusions. Current new Regularnie requires confirmation before each purchase; native interval controls alone are not unattended supply. Preserve legacy399's genuine automatic debit separately.

The live account again has six ACTIVE groups plus PAUSED361, unchanged. Expanded257757 is PAID/Przyjęte99.25zł/free delivery with all four ordered foods. Public Cauliflower/Raspberry unavailability does not prove loss of an accepted reservation. No basket/account setting/order/payment/contract/activation changed in this re-audit. The earlier browser-disabled handoff is resolved; no login/reconnect request is pending.

The new **750g four-kind candidate** is Oyster200g +Shiitake200g +Maitake150g +King Oyster200g:10 full choices plus separate50g Oyster/50g Shiitake remnants. It is an alternative to the older800g/250g-King scenario, not an instruction to duplicate357 or carry fresh remnants month to month. Four400g Kefirs/14days match the8/28day Ferment allocation; they do not declare Robico's named culture and their400g panel adds44kcal/3.6g Fat. No canonical identity/portion has been silently changed.

Real remaining gates are exact first stock/timing, usable life, unit/pack/formulation contradictions, each product's delivered comparison, independent home fees and genuinely unattended native ordering/payment. Source details: [fresh](DIET_REAUDIT_FRESH_02NOV.md), [pantry](DIET_REAUDIT_PANTRY_02NOV.md), [proteins](DIET_REAUDIT_PROTEINS_02NOV.md). The three approved2November follow-ups are SENT; no further message was sent by this audit.

## Historical2November17:40 Warsaw — supplier follow-ups sent; earlier account gate

The three specifically approved [supplier follow-ups](DIET_SUPPLIER_FOLLOWUPS_02NOV.md) were sent to Bioshi, Polskie Eko Zagrody and Catch Club; outgoing recipients, subjects and full bodies were verified. The user also approved routine clarifications within those exact requests. No purchase, contract, payment,370 cancellation or361 resumption follows from the messages. Scheduled monitoring still sends nothing.

At this earlier observation the user reported enabling browser use, but two fresh inventories including a runtime reset still returned **Local browser use is disabled in Work settings**, with no connected browser. The later2November live re-audit resolved that gate; no further login/reconnect request is needed. This never established a retailer logout. No account, cart, quantity, financial schedule or subscription was changed at the earlier observation; its30/31October source dates remain separate from the later2November checks.

Public qualification excluded Pora Na Pola (official homepage: sales suspended) and Perkoz's Atlantic subscription (local Olsztyn/Tomaszkowo/Dorotowo delivery, not Gdańsk). Additional exact organic Turkey tenderloins are ordinary-product leads pending native standing-delivery proof. See the [Turkey](DIET_TURKEY_ROUTE_RESEARCH_28OCT.md), [Salmon](DIET_SALMON_ROUTE_RESEARCH_28OCT.md) and [staple](DIET_STAPLE_ROUTE_RESEARCH_28OCT.md) records.

A separate **paper-only** Egg46125×10 + Blueberry55183 125g×6/14day candidate gives750g Blueberries =five150g servings, with advertised later goods122.08zł arithmetic. It is not a saved cart or qualifying quote: actual HOME fees, current stock/first timing, usable life, per-product delivered comparison and unattended new-flow renewal remain unresolved. No extra399, Nuts or Oats order is prepared from this scenario.

## 1November — offline Oil/Fish correction screen

Incoming mail released no new activation; see the [handoff](DIET_PAYMENT_HANDOFF.md). Independent arithmetic rules out simply halving the current Oil/Fish order as a complete correction. These scenarios use **26October500125 prices**, illustrative Oil density0.915g/ml and fixed **Phileos13.5g/day**, separate from Pamako; they are neither current renewal quotes nor saved changes.

| Phileos native quantity/cycle | Supply / fixed use per cycle | Accumulating excess |
| --- | --- | --- |
| Existing2×500ml/30days |915g /405g |510g/30days |
|1×500ml/30days |457.5g /405g |52.5g/30days |
|2×500ml/60days |915g /810g |105g/60days |
|3×500ml/90days |1372.5g /1215g |157.5g/90days |

Each reduced scenario still adds1.75g/day to stock. Exact illustrative balance would require500ml/33.89days or1L/67.78days; those custom cycles are **not verified capabilities**. A delayed first order cannot correct the long-run drift, and optional Dinner Nothing does not consume it. Other pack/cycle combinations or a genuine supported standing schedule still need qualification.

One500ml bottle at the dated55.25zł plus the same17.09zł Mackerel/26.45zł Sardine jars gives **98.79zł goods**. If the old9.49zł courier fee held, total would be108.28zł and logistics9.606%: approximately100zł goods and the10% arithmetic screen, **not an accepted checkout**. It leaves Oil drift and under-supplies Fish: one125g Mackerel jar/30days gives116.67g/28days against250g required; one126g Sardine jar gives117.6g against340g. The Sardine meal remains170g drained, and exact identities, opening/remainder life, per-product delivered comparisons and actual renewal fees remain unverified. Do not save this reduced basket as complete Diet coverage or increase consumption to fit it.

## 31October — pantry mapping resolved; incoming quantities retained

Fresh500156 details now show **W drodze /Opłacone**, unchanged14SKU/18packs,344.52zł/free InPost HOME and **520000012680462133044051**. Bioshi's notice received30October21:41:22 Warsaw assigns the same parcel/total to **legacy258958**: one pantry order, not additional supply. InPost's31October08:33:39 Warsaw departure notice verifies carrier handover, **not delivery or inspected usable stock**. This supersedes3November's proposed dispatch and the earlier unmatched label/accepted-only state. Do not duplicate Nuts/Oats or repay.

Last full profile verification remains **30October**, with six active, paused361 and unresolved370 overlap. Separate renewal prices/fees/automatic charging and protein supplier quotes remain unverified. No new reconfiguration answer, payment failure, account change or stock balance was established. Source trail: [31October handoff](DIET_PAYMENT_HANDOFF.md).

## 30October — exact saved groups retained; first-stock allocation unchanged

Fresh signed-in Brave review confirms **six ACTIVE profiles plus PAUSED361**, unchanged exact P60/P90 foods and60/90day cycles, next27December/26January. Their future quotes/fees and unattended collection remain unverified.370 remains active with unresolved overlap;361 still contains Tempeh and must stay paused. No new supplier quote or applied reconfiguration was found, and no account settings or commitments changed.

Paid500156 remains accepted at344.52zł with free InPost HOME and no order-linked tracking/receipt. A new Bioshi label is unmatched;258958's planned3November dispatch is likewise not mapped to500156,257757 or another known food allocation. Do not credit usable stock, advance first purchases or infer missing foods from either. Newly read255381 refund22.27zł/dispatch82.28zł evidence preserves unknown affected goods;258647/500125 are one explicitly matched parcel. See the [30October handoff](DIET_PAYMENT_HANDOFF.md). Canonical portions, desired rotation and measured-stock uncertainties remain unchanged.

## 29October — six active profiles, paid renewal and carrier deliveries

**Current verified state supersedes older snapshots below.** Connected Brave shows **six ACTIVE profiles plus PAUSED361**, seven rows:357,399, Oil/Fish and370 retain their previous foods/cadences; P60 and P90 are now verified ACTIVE. Their IDs were not exposed, and no future renewal price/fee quote was available.

| Newly verified profile | Exact saved recurring contents | Native cycle / next displayed date |
| --- | --- | --- |
| P60 |Oats1kg×1 +500g×1; Pistachios150g×2; Coriander30g, Rosemary30g, Oregano20g and Thyme20g each×1; Cumin30g×2. **8 SKUs /10 packs.** |60days;27December2026. |
| P90 |Walnuts300g×2; Almonds350g×1; Macadamias200g×2; Quinoa500g, Beluga400g and Black Beans500g each×1. **6 SKUs /8 packs.** |90days;26January2027. |

Expanded**500156** matches all14 SKUs/18 packs and confirms **Opłacone /Przyjęte,344.52zł, free InPost Kurier HOME**; no parcel tracking or arrival yet. Do not recreate or repay it. **370 is still ACTIVE**,800g Nuts/90days, next24December: the one-time transfer/overlap remains unresolved. No cancellation, pause, duplicate order or new commitment was submitted in this29October review.361 remains PAUSED with Tempeh200g×3 and no removal controls; do not resume it as stored.

**257757 is paid:** IdoPay confirms99.25zł charged, transaction257757-1, email received28October23:51:32Z =**29October00:51:32 Warsaw**. The earlier28October awaiting-payment reminder is superseded; do not repay.399's4November delivery remains scheduled. This confirms that legacy renewal's automatic collection despite the generic payment label; it does not establish P60/P90 unattended charging.

| Verified GLS delivery | Displayed carrier event, checked29October |
| --- | --- |
|255381 →33685101838, explicitly matched by the27October label reference |DELIVERED28October14:52. |
|500125 →33685101618, explicitly matched by the merchant link |DELIVERED28October12:29. |

GLS prints no timezone for these events; do not assign one. Contents, condition, expiry and usable balances remain uninspected, and elapsed time is not depletion.500125's older merchant“W drodze” status does not negate the carrier delivery or establish a new failure.

**Supplier responses:** Polskie Eko Zagrody replied28October11:24:03Z =12:24:03 Warsaw, inviting a visit to Gdańsk Słowackiego19A on Thursdays/Saturdays10–15. This answers neither home/native standing delivery nor the usable-life/custom-quote questions. Exact-sender search found no Catch Club reply and no substantive Bioshi reconfiguration response. Both approved protein inquiries remain sent; do not resend or ask for approval/login again.

Six completed incoming queries covered Bioshi, Polskie Eko Zagrody, Catch Club, GLS, IdoPay and InPost, without pagination. Unrelated iHerb/DrZdrowie messages were excluded from Diet evidence. This is routine progress with **no user payment, card or sign-in action required**. Preserve all earlier quote/source dates and the27October cart as historical evidence.

## Historical28October01:13:54 Warsaw — pantry order500156 paid

Read-only Outlook search found Bioshi's **“Mamy Twoje zamówienie500156”**, received2026-10-28T00:13:54Z (**01:13:54 Warsaw**). It confirms payment received and preparation of the exact **14 SKUs /18 packs** matching the P60/P90 design: **344.52zł goods and344.52zł total, InPost Kurier HOME free**. No discount is shown. The27October310.05zł cart quote remains historical; the differing amounts do not establish a price increase or the reason a discount was absent.

**Do not recreate or repay this pantry order.** Treat its contents as paid incoming food when offsetting other first purchases, without crediting inspected usable stock. The email does not verify new future profiles, native renewal cycles,370 transfer/cancellation, dispatch or receipt. Separate renewal fees and automatic collection remain unverified. No order was placed in this28October research turn. Today's sender search found this paid-order notice, but no reply completing the requested Bioshi reconfiguration.

## 28October — independent sourcing continues while Bioshi replies

The user confirmed **Turkey and skinless Salmon as the priority** and asked preparation to continue across the remaining Diet categories while awaiting Bioshi. Work on these independent routes proceeds alongside pantry renewal reconciliation, rather than waiting for a merchant answer to begin research. This sourcing work made no account or ordering changes; the separate read-only mail finding above confirms500156 paid. The cart evidence below remains dated27October.

- **Turkey:** [28October route research](DIET_TURKEY_ROUTE_RESEARCH_28OCT.md) identifies Polskie Eko Zagrody's exact organic Turkey tenderloin; the manufacturer's outdoor-rearing statement supports the intended identity. A native standing order to the Gdańsk home address, exact pack allocation, delivered usable life and qualifying recurring quote remain unconfirmed.
- **Skinless Salmon:** [28October route research](DIET_SALMON_ROUTE_RESEARCH_28OCT.md) identifies Catch Club's real weekly/fortnightly Stripe subscription plans at129/179/249zł including delivery according to its official FAQ. This is a subscription-capability lead; exact skinless custom goods, full portions, remaining life and the first/renewal quote for the requested composition still need confirmation. No default assortment is accepted as Diet coverage.
- **Staples:** the [exact-product refresh](DIET_STAPLE_ROUTE_RESEARCH_28OCT.md) retains Alpro/Sante and the selected Ferments. Exact native replenishment/automatic charging remain unverified. Alpro's five-day opened life fits200ml/day; the optional Mlekovita1L pack's48hour instruction needs a different pack allocation before coverage can be claimed. Dairy Milk is an alternative within the shared Milk demand, not another compulsory purchase.

Both focused [supplier quote inquiries](DIET_PROTEIN_STANDING_DELIVERY_REQUESTS_28OCT.md) were **explicitly approved and SENT28October**, to Polskie Eko Zagrody at11:49:01 Warsaw and Catch Club at11:49:02 Warsaw, from pawel.troka@outlook.com; both outgoing Outlook copies were verified. Await responses; do not resend or ask for send approval again. These request information/itemized quotes only and authorize no orders, payments, contracts, substitutions or activation. Qualify each route against approximately100zł genuinely needed post-discount goods, compulsory logistics≤10%, the25% per-product delivered cap, exact foods and actual expiry before activation. The separate approved Bioshi request is recorded in the [handoff](DIET_PAYMENT_HANDOFF.md); these separate protein inquiries do not change its sent status.

## Historical27October23:09 Warsaw — replacement cart saved, then unpaid

At this27October review the loaded signed-in Brave cart contained the exact replacement **P60/P90:14 distinct SKUs /18 packs**, with every quantity and native60/90day badge verified. Walnuts/Macadamias are2packs each; the old unpaid Pistachio90day and Cumin30day lines were replaced by2packs each/60days; Oregano/Thyme were added. Actual cart goods at that review were **344.52zł ordinary −34.47zł discount =310.05zł**. The old12-line draft below is historical.

Checkout displayed **InPost Kurier home delivery0zł** at310.05zł goods and a250zł threshold; GLS Kurier10.49zł and DHL11.99zł were also listed. Contact/address fields were blank, so this is **not a destination-verified quote or proof of free separate renewals**. Terms were not accepted; no payment, order or new profile was submitted. The cart was left saved and unpaid. Four active profiles plus paused361 were reverified;361 still contains Tempeh and no product-removal controls were available. **That historical submission hold is superseded by the paid500156 confirmation above; do not recreate or repay the order. Future370 migration and separate renewal fees still require verification.**

**27October2026 — revised planning specification, not activated orders.** This covers every required Diet category and replaces the earlier approach of configuring only the saved pantry cart. The user removed Tempeh and Tofu, requested more organic Turkey and skinless Salmon, and requested all four approved Mushroom varieties. Strawberries remain excluded from purchasing after the quality failures. On28October the user chose to keep Turkey and skinless Salmon as the priority; Rainbow Trout remains a deferred candidate, not an active food or purchase.

The [canonical Diet](../README.md#4-diet) owns foods, portions and preparation. This plan defines their consumption and proposed purchasing allocation; the [payment handoff](DIET_PAYMENT_HANDOFF.md) owns actual orders/account evidence. The [earlier12-line cart](DIET_27OCT_ACTIVATION_BATCH.md) is historical. The exact P60/P9014-SKU/18-pack design now matches paid order500156; the27October cart/checkout record remains a separate earlier observation. **No370 transfer or new future profile/cycle is verified by the paid-order email.** First shipping is confirmed free in that email; separate renewal shipping is not.

## Shipment acceptance rules

- Prefer free **home courier**. Paid home courier is authorized; lockers/pickup points remain excluded.
- Each actual shipment should contain approximately **100zł or more of goods after discounts**. Its compulsory delivery/packing charges must be **no more than10% of that goods amount**, including renewals at later discounts. Do not aggregate separate shipments to manufacture a pass.
- Keep the separate **25% maximum delivered-price premium per comparable product**, including compulsory fees on both routes. A cheap basket cannot conceal an over-cap food. No filler or extra portions solely to meet shipping thresholds.
- Minimize storage time before consumption, particularly for fresh protein, leaves, Microgreens and Berries. Buying every listed alternative is unnecessary; preserve complete category coverage and meaningful rotation.
- A later next-renewal date does not defer an immediate first order. Offset first purchases with actual usable stock and confirmed incoming quantities, without inferring depletion from elapsed time.

For net goods `G` and compulsory logistics `L`, require `G ≳100zł` and `L/G ≤0.10`. A9.49zł fee is9.49% at100zł goods;12.99zł requires at least129.90zł goods. Evaluate the actual discounted basket, including the consequences of unavailable or removed lines.

Current Bioshi **Regularnie** settings expose7/14/21/28/30/60/90-day intervals. Current product/terms wording requires confirmation/payment of later purchases; an active profile is not proof of unattended payment. A saved list is not a subscription. The selected cycle must be verified for each actual group. [Bioshi terms](https://bioshi.pl/pl/terms) · [Delivery terms](https://bioshi.pl/pl/delivery).

## Four-week protein calendar

Repeat **A in weeks1 and3**, **B in weeks2 and4**. This gives **12 Egg +6 Turkey +6 Salmon +2 Mackerel +2 Sardine dinners**, with28 Lunches and28 Dinners allocated. Turkey appears in both meals without becoming an extra serving in either.

Portions: Turkey150g raw; skinless Salmon150g raw; Eggs200g shell-free; Pollock200g raw excluding glaze; cooked Mussel Meat150g; Shrimps180g; Mackerel125g drained; Sardines170g drained.

| Day | A Lunch | A Dinner | B Lunch | B Dinner |
| --- | --- | --- | --- | --- |
| Monday |Turkey |Eggs |Turkey |Eggs |
| Tuesday |Turkey |Salmon |Turkey |Salmon |
| Wednesday |Pollock |Turkey |Turkey |Eggs |
| Thursday |Turkey |Eggs |Mussels |Mackerel |
| Friday |Mussels |Salmon |Turkey |Turkey |
| Saturday |Shrimps |Turkey |Turkey |Sardines |
| Sunday |Turkey |Eggs |Turkey |Eggs |

Using the existing illustrative cooked yields of120g Salmon from150g raw and160g Pollock from200g raw, A supplies400g ready-to-eat Fish and B415g. Both include at least200g Fatty Fish. Actual cooked weights control the comparison; Shellfish is separate. The README's checked-day calories are not the weekly average of these different meals.

| Protein |28-day consumption | Practical purchase constraint / current route |
| --- | ---: | --- |
| organic pasture-raised Turkey tenderloins |3,900g raw:20 Lunch +6 Dinner servings |The selected500g pack does not divide into150g portions. Prefer a verified weighed150/300/450g quantity or a whole-pack allocation within its usable window. Native replenishment for the exact approved form is unverified. |
| Norwegian Salmon without skin |900g raw:6 servings |300g in A weeks;150g in B weeks. The selected Auchan fish is sold thawed; do not refreeze. Nominal500g catchweight has a350g minimum; a300g order is unsupported and a selectable450g pack is unverified. Allocate exact portions/remainders within the actual use-by window. No native route verified. |
| MSC Alaska Pollock |400g raw excluding glaze:2 servings |Selected450g frozen pack requires actual deglazed mass and a same-food frozen remainder allocation. No native route verified. |
| cooked Chilean Mussel Meat |600g:4 servings |450g packs give three150g portions; two packs supply six meals across the rolling schedule, not six meals forced into this month. No native route verified. |
| Wild-caught Argentinian Red Shrimps |360g:2 servings |Two selected180g packs. No native route verified. |
| Atlantic Mackerel fillets |250g drained:2 servings |Two approved125g drained portions. The new Oil/Fish group's Emperatriz91402 jar is recorded separately from the canonical Vilgain product; do not equate an active profile with verified SKU/portion compliance. |
| Sardines |340g drained:2 servings |Four selected85g drained tins. New Emperatriz90555 jars provide126g drained each; one jar is not a170g dinner. Do not silently change the portion or assume the jar is the canonical product. |
| organic green-legged-hen Eggs |2,400g shell-free:12 servings |Approximately48 medium Eggs; weigh actual edible yield. Existing399 supplies10 nominal Eggs/30days. |

Multiply consumption by3 for an84-day demand comparison or by90/28 for a90-day rate equivalent. These are **not delivery calendars or instructions to round every row up and repeat that overpurchase**.

For Egg rate balance, existing10/30days plus additional10/14days and two further10/30day streams gives `10/30 +10/14 +10/30 +10/30 =48/28` nominal Eggs/day. Stagger the three30-day streams rather than starting all cartons together. Complete shipment composition, actual shell-free yield, expiry and phase checks remain necessary; only399 exists today.

The [offline comparison](DIET_SHIPMENT_REOPTIMIZATION.json) uses this exact A/B calendar over420days, nominal four Eggs per dinner, FIFO and no invented opening stock. Among140 evenly spaced small-carton phase candidates, its best pattern has10Egg/14days at phase6 and10Egg/30days at phases1/11/21: maximum delivery-to-consumption age10days, mean4.42days, peak20Eggs. Among25,200 phases of10Egg/14days +20Egg/30days +20Egg/60days, the best has maximum21days, mean9.28days and peak40Eggs. These are restricted arithmetic comparisons, not booked dates or a global freshness optimum. **Prefer the small cartons inside genuinely needed mixed grocery groups.** Require delivered remaining life beyond the modeled maximum plus a practical delay margin; the old carton's11days cannot be transferred to the selected green-legged Eggs. Do not buy20Eggs merely to raise a parcel's value.

## Complete plant-category demand

These28-day allocations give one choice per day in each required category. They are a usable consumption example, not a requirement to buy every alternative. Steamed vegetables are weighed after preparation where the README specifies; Fruit and raw produce use edible weight. Gross head/pack weights cannot be substituted for these quantities.

| Category |28-day portion allocation | Procurement / coverage status |
| --- | --- | --- |
| Lunch starch |6×Quinoa75g cooked;9×Orange Sweet Potato100g;9×peeled Potato80g;4×Beni-imo100g |450g cooked Quinoa,900g prepared Orange Sweet Potato,720g prepared Potato,400g prepared Beni-imo. P90 covers Quinoa only. Native Potato/Sweet Potato offers do not by themselves establish whole-category coverage; Beni-imo cultivar identity still needs matching. |
| Dinner starch |4×Beluga65g cooked;6×Black Beans60g;18×Beni-imo100g |260g cooked Lentils,360g cooked Beans,1,800g prepared Beni-imo. This is2.5 Pulse meals/week. P90's actual yields can support some additional Pulse choices replacing Beni-imo; Chickpeas remain a replacement option, not a compulsory third pack. |
| Cruciferous Vegetables |14×Broccoli100g;6×Cauliflower100g;4×Brussels Sprouts100g;4×Kohlrabi100g |2.8kg prepared.399's approximately800g gross Cauliflower/30days is partial coverage; it is currently unavailable for new purchasing. Fill any unavailable choice with another approved Cruciferous, using its written portion. |
| Colorful Vegetables |12×Carrots100g;7×Butternut100g;9×Red Pepper100g |2.8kg edible. Preserve the user's1kg gross Butternut/28day purchasing target. Seven choices assume700g prepared yield; if actual yield differs, adjust the split with an approved vegetable rather than enlarge Butternut purchasing.399's1kg gross Carrots/30days covers only part. |
| Leafy Greens |12×Kale100g;10×Bok Choy100g;6×Spinach100g |2.8kg prepared. Buy smaller fresh lots;100g raw Spinach is not automatically100g steamed. Swiss Chard can replace a choice when available. No complete native route is verified. |
| Mediterranean Vegetables |10×Tomatoes100g;12×Green Beans100g;6×Celeriac75g |2.65kg edible.357's1kg Tomatoes/28days covers the nominal Tomato allocation only if fulfilled and usable. Old255381's Tomatoes were removed without substitution, so no Tomato portions are credited from that order. New Tomato purchases are currently unavailable. Other approved options can fill actual gaps; do not add disliked vegetables. |
| Microgreens |24×Arugula50g;4×Watercress Leaves50g |1.4kg edible. At the known100g/50g pack sizes, three Arugula packs plus one Watercress pack weekly cover seven choices. Bioshi Arugula44667 is now available24.29zł/100g under2November live evidence; current delivered comparison, usable-life schedule and unattended renewal remain unqualified. Sprouts/other Microgreens replace choices when their pack remnants fit nearby meals. |
| Whole Fruit |12×Kiwi150g;4×Orange150g;8×Pomegranate130g arils;4×Tart Cherries100g |1.8kg edible Kiwi,600g Orange,1.04kg arils,400g Cherries. Preserve1kg gross Oranges/28days.357's1.2kg gross Kiwi does not cover1.8kg edible Kiwi; fill remaining Fruit demand with purchased edible quantities or other approved choices. Preserve the existing Kiwi purchase. The2November profile shows one pack with a current approximately600g title; actual saved gross mass/pack multiple remains unverified against the historical1200g created-order lines. No new Kiwi price investigation. |
| Fermented food |14×Sauerkraut100g;8×Kefir400g;4×Skyr200g;2×Kimchi75g |1.4kg Sauerkraut,3.2kg Kefir,800g Skyr,150g Kimchi. Sauerkraut averages3.5days/week. Existing jars offset startup. The800g jar's conflicting opened-life instructions must be resolved before claiming all eight100g choices fit. Klimeko400g is an available organic/lactose-free/live-culture alternative with a changed panel and no named L.rhamnosus; Maluta/Skyr and Kimchi formulation/pack life remain unresolved. The new recurring flow still requires confirmation. |
| Berries |One written choice daily; four-kind rate example below |Keep150g Blueberries and100g Raspberries/Bilberries/Blackcurrants. No Strawberries. Current399 covers only500g gross Raspberries/30days, if fulfilled and usable. |

The three100g Vegetable categories each require700g prepared weekly; the Mediterranean example averages662.5g weekly. Microgreens require350g weekly in this allocation. These are consumption weights, not asserted raw pack sizes. Across the example, the four main Vegetable groups total11.05kg/28days because Celeriac uses its written75g portion; do not enlarge it solely to force a round400g/day.

At illustrative3× Quinoa and2.4× Pulse cooking yields, the starch example needs150g dry Quinoa,108.3g dry Beluga and150g dry Black Beans/28days. Measure actual cooked yield and allocate the dry-pack remainder to subsequent written choices. Preparation yield and transient stock do not authorize daily portion increases.

## Berries and four-kind Mushroom rotation

The following **rate comparison** supplies exactly one Berry choice/day, using canonical150g Blueberries:

| Food | Integer pack-rate candidate | Daily choice rate |
| --- | --- | ---: |
| Blueberries |125g×4 every7days |500/150/7 =10/21 |
| Raspberries |125g×4 every30days, existing399 |500/100/30 =1/6 |
| Bilberries |200g×2 every21days |400/100/21 =4/21 |
| Blackcurrants |350g×1 every21days |350/100/21 =1/6 |
| **Combined** | |**1** |

Over a complete210-day quantity cycle these rates supply100 Blueberry,35 Raspberry,40 Bilberry and35 Blackcurrant choices. That is not yet an arrival/expiry proof: monthly Raspberries move through weekly Blueberry phases, and same-species fresh remainders need timely meals. Frozen21-day retailer subscriptions are **not verified**. Do not present this rate table as booked delivery dates.

An alternative fresh candidate is **Eggs10 +Blueberries125g×6 every14days**, with122.08zł later advertised goods. If logistics were9.49zł, the ratio would be7.77% and delivered total131.57zł; final destination/renewal quotes remain unverified. This supplies5 Blueberry choices/14days and one additional Egg carton; it does not cover all Berries or Eggs. It is an **alternative to the weekly Blueberry line**, not an extra overlapping line. Rebuild the remaining Berry allocation if this candidate is selected.

The user's four-kind Mushroom request supersedes the old200g combined purchasing limit. A practical first rotation is:

| Mushroom | Small-pack baseline | Complete written choices | Remainder |
| --- | ---: | ---: | ---: |
| Oyster |200g, already in357 |2×75g |50g |
| Shiitake |200g, already in357 |2×75g |50g |
| Maitake |150g |2×75g |0g |
| King Oyster |250g |5×50g |0g |
| **All four** |**800g** |**11 full choices** |**100g, separated by species** |

Acquire the packs near their own consumption blocks, rather than all four on day1. Retain both existing357 species; its earlier requested Shiitake removal was not saved. Maitake/King Oyster need a verified retailer route. A50g Oyster or Shiitake remainder cannot be called a75g choice, mixed with another species or assumed fresh until the next monthly pack. Use a smaller weighed pack or a verified same-species storage/next-meal arrangement before repeating the baseline. **This is a reduced four-kind rotation, not daily75g Mushroom coverage or a demonstrated zero-waste recurring schedule.**

## Fixed foods and selected seasonings

| Requirement |28days |90day consumption equivalent | Supply position |
| --- | ---: | ---: | --- |
| Rolled Oats |700g |2,250g |P60 below exactly matches25g/day. |
| Exact Sante High-Fiber Oat Bran |280g |900g |Three200g packs/60days would match10g/day; no exact native route verified. |
| Morning Seeds |196g |630g |Shared7g/day among Flax/Chia/Hemp. Owned stock offsets first purchases; all alternatives need not be purchased together. |
| Dinner Seeds |196g |630g |Shared7g/day among Pumpkin/Tahini/Sunflower; exact continuing pack/cycle balance unresolved. |
| Nuts |560g |1,800g |Replacement P60/P90 preserve the existing four-kind mass mix. |
| Matcha |56g |180g |User reports0g on2November, superseding September's200g. Yōkiro4×30g/60days remains prepared/unactivated:5November first HOME/free109.21zł total persisted, but recurring151.20zł goods still lists locker8.99zł. Renewal HOME/cap qualification and final terms/payment remain pending; mandate not accepted. |
| Milk |5.6L |18L |Six1L cartons/30days matches200ml/day, split between approved options if desired. Exact current native route not verified; opened cartons must fit their labels. |
| Pamako |378g |1,215g |Fixed13.5g/day. Separate meaningful product; Phileos cannot silently replace it. No qualifying native route verified. |
| Phileos, fixed Lunch |378g |1,215g |Fixed13.5g/day. Existing1L/30day Oil/Fish group is materially oversized; reconcile below. |
| Optional Dinner fats |0g under checked Nothing |0g |No extra purchasing demand without selecting EVOO/Avocado in place of Nothing. |

Morning Spices are one selected choice daily; Lunch/Dinner CHOOSE ANY lists do not make every alternative mandatory. P60/P90 support Coriander Seed0.5g/day, Rosemary0.5g/day and Cumin1g/day. Oregano20g/60days and Thyme20g/60days each supply40 selected0.5g uses per60days, not daily use. If daily use of either checked herb is required, that pack allocation is short10g/60days and must be revised explicitly.

Fresh-herb variety can use2×Parsley20g +2×Cilantro15g at Lunch and2×Basil15g +2×Dill15g at Dinner weekly:160g/120g/120g/120g edible respectively per28days. This is a chosen seasoning pattern, not an obligation to buy every CHOOSE ANY food. Buy bunches/pots only when their edible quantity can be used at these portions; leaf mass is not gross pot weight. Existing Cinnamon, Cloves and Cardamom offset first purchases; do not add them to every pantry renewal by default.

WPI, MicroVitamin+, standalone Psyllium, Collagen, EAA and workout powders remain in the supplement supply ledger at their existing doses. Diet references do not create duplicate grocery orders. Filtered Water has no bottled-water subscription demand.

## Replacement pantry design: P60 and P90

**These replace/transfer Nut A370, the old Nut B proposal and the historical12-line pantry draft. They are not additions.** The ordered quantities match paid500156/258958, carrier-delivered2November10:02 and verified5November, without a printed timezone or inspected actual contents. The27October draft badges were initially the cycle evidence;29October verified both exact ACTIVE60/90day profiles and their next dates, unchanged5November. Their IDs, separate renewal prices/fees and unattended charging remain unverified. Do not recreate the first order. Leaving old overlapping Nut commitments unchanged while new renewals also run would overbuy; actual370 migration and stock transition still require reconciliation.

Prices below use the27October advertised later regular-purchase line prices, not accepted checkout totals. The exact product links and pricing evidence are in the [preparation manifest](DIET_27OCT_ACTIVATION_BATCH.md). Separate groups must qualify individually; there is no assumed cross-cycle shipment merging.

| P60 — every60days | SKU | Packs | Later goods |
| --- | --- | ---: | ---: |
| organic Rolled Oats1kg |46956 |1 |12.40zł |
| organic Rolled Oats500g |52572 |1 |10.11zł |
| organic raw unsalted Pistachios150g |53019 |2 |74.28zł |
| organic Coriander Seed30g |46308 |1 |5.09zł |
| organic Rosemary30g |46323 |1 |6.11zł |
| organic Oregano20g |46317 |1 |5.69zł |
| organic Thyme20g |46325 |1 |5.09zł |
| organic whole Cumin Seed30g |46593 |2 |14.10zł |
| **P60 goods** | |**10 packs /8 SKUs** |**132.87zł** |

| P90 — every90days | SKU | Packs | Later goods |
| --- | --- | ---: | ---: |
| organic Walnuts300g |44492 |2 |39.08zł |
| organic Almonds350g |45420 |1 |24.13zł |
| organic Macadamias200g |44472 |2 |57.96zł |
| organic White Quinoa500g |44499 |1 |14.95zł |
| organic Beluga Black Lentils400g |44959 |1 |13.85zł |
| organic Black Beans500g |49356 |1 |10.02zł |
| **P90 goods** | |**8 packs /6 SKUs** |**159.99zł** |

| Individual shipment | Net goods | If logistics are9.49zł | Logistics/goods | Status |
| --- | ---: | ---: | ---: | --- |
| P60 |132.87zł |142.36zł delivered |7.14% |Profile ACTIVE/cycle verified29October; separate renewal price/logistics remain unquoted. This row retains the earlier hypothetical goods/fee calculation. |
| P90 |159.99zł |169.48zł delivered |5.93% |Profile ACTIVE/cycle verified29October; separate renewal price/logistics remain unquoted. This row retains the earlier hypothetical goods/fee calculation. |

P60 is156.30zł at ordinary goods prices,140.66zł at advertised first-discount line prices and132.87zł later; P90 is188.22/169.39/159.99zł respectively. First-discount eligibility is account-specific. Maximum logistics at later prices are13.287zł for P60 and15.999zł for P90; compare actual currency-rounded charges without rounding an over-limit fee down into a pass.

The9.49zł fee is a scenario, not a new checkout quote. Current public GLS weight-band applicability is ambiguous; any compulsory packing charge belongs in the numerator too. Before any further recurring commitment, refresh account discount eligibility, exact stock, home-courier method and each product's matched delivered premium. The first order500156 is already paid and must not be submitted again.

The restricted comparison assigns Pistachios and Cumin independently to30/60/90-day cycles while preserving six packs of each per180days, with all other lines fixed. Of those nine possibilities, only Pistachios60days+Cumin60days and Pistachios60days+Cumin90days keep every separate recurring group above100zł goods. **Cumin60days is preferred:** two30g packs arrive every60days instead of three every90days. Both passing designs buy the same quantity for718.59zł later goods over180days and produce five renewal parcels; the selected design reduces Cumin arrival stock and consumption age. This is a restricted grouping result, not a global food-plan optimum or a verified courier tariff.

Over180days, three P60 and two P90 deliveries supply:

- Walnuts1,200g +Pistachios900g +Almonds700g +Macadamias800g =**3,600g Nuts**, matching20g/day and preserving the former species totals.
- **4,500g Oats**, matching25g/day.
- **180g Cumin**, matching1g/day;90g each Coriander and Rosemary, matching0.5g/day.
- Quinoa1kg dry, Beluga800g dry and Black Beans1kg dry. At illustrative yields these support40 Quinoa and approximately69.54 Pulse choices/180days; remaining starch meals need the approved roots/tubers. Dry remainders feed subsequent permitted choices.

The packaging tradeoff is explicit: P90 brings **1.35kg Nuts at once**, versus the former800g/1kg staggered A/B shipments. P60 adds300g Pistachios every60days. Phase the groups against actual stock; do not automatically start both on one date. Open packs sequentially, keep same-species remainders identifiable, and follow cool/dry storage and actual labels. This improves shipment economics but is not proved fresher than the former Nut schedule. Nut portions remain20g; no disposal, mixed-species choice or extra daily serving is assumed.

## Fresh-food cohorts and current route status

Build weekly groceries around their actual near-term meals; use smaller protein/leaf purchases inside the week where remaining life requires it. A weekly cohort is a purchasing design, not a claim that every listed retailer offers autoship or one-week shelf life.

| Cohort | Genuine demand to group | Cadence / current qualification |
| --- | --- | --- |
| Fresh main groceries |A weeks:Turkey900g raw, Salmon300g raw, Pollock200g, Mussels150g, Shrimps180g; B weeks:Turkey1,050g raw, Salmon150g raw, Mussels150g, Mackerel125g and Sardines170g drained. Add the week's uncovered vegetables, Microgreens, Fruit, Milk/Ferments and selected herbs. |Weekly planning; refrigerated protein may need smaller more frequent purchases. Exact organic Turkey and skinless Salmon native routes are unverified. Do not turn the whole week's quantity into one unsafe raw-storage block. Recheck actual destination delivery charges rather than reuse old Frisco/Auchan quotes. |
| Native fresh Egg/Berry candidate |Eggs10 +Blueberries125g×6; later goods122.08zł. |Every14days candidate, not activated. Supplies one additional Egg stream and5 Berry choices/14days. First timing, remaining life, destination courier and renewal fees need verification. |
| Remaining selected Egg supply |Two further10-count/30day streams if399 and the14day candidate remain. |Place inside genuinely needed fresh shipments with their own approximately100zł goods/10% logistics qualification. Do not assume two cheap Egg-only parcels pass. Stagger phases using actual incoming cartons. |
| Other Berries / frozen approved foods |Remaining full Berry choices, selected frozen Bilberries/Blackcurrants, Pollock/Shellfish/Green Beans when needed. |21/28/30day quantity candidates need an actual retailer route and cold-chain shipment. An available manual frozen cart is not native automation. Do not buy frozen replacements for unrelated fresh preferences. |
| Durable produce |Oranges1kg gross/28days; Butternut1kg gross/28days; required Potatoes/Sweet Potatoes, actual missing Fruit/Vegetable choices. |Group with needed fresh deliveries; no old Tempeh line or Strawberry reintroduction. Native interval and public product listing do not establish current availability or meal coverage. |
| Four-kind Mushrooms |Existing Oyster/Shiitake plus Maitake/King Oyster near their own consumption blocks. |800g first rotation candidate; full repeated remainder/storage assignment still required. Specialty native routes unverified. |

**27October new-purchase availability evidence:** the following Bioshi products are currently unavailable for new buying. This does not prove that an already accepted order has lost a reservation.

| Food | Exact product | Effect |
| --- | --- | --- |
| Cauliflower |[45883](https://bioshi.pl/pl/products/kalafior-swiezy-bio-okolo-0-80-kg-45883) |Do not count a new Cauliflower purchase as ready. Existing399 reservation/fulfillment is a separate check. |
| Butternut |[64110](https://bioshi.pl/pl/products/dynia-pizmowa-butternut-swieza-bio-okolo-0-70-kg-64110) |The reduced purchasing target is preserved, but no new available native shipment is established. |
| Kiwi |[80086](https://bioshi.pl/pl/products/kiwi-swieze-bio-okolo-0-60-kg-80086) |Keep existing357 evidence separate; do not promise additional Kiwi supply. |
| Tomatoes |[88631](https://bioshi.pl/pl/products/pomidory-okragle-swieze-tacki-bio-polska-88631) |New quantity cannot be treated as covered merely because357 exists. |
| Arugula |[44667](https://bioshi.pl/pl/products/rukola-swieza-niemyta-bio-okolo-0-10-kg-44667) |No current Bioshi route. The historical price also exceeded the comparison cap; refresh an alternative rather than inherit an old pass. |

Other explicit exact-route gaps are Sante6% Bran, Alpro fortified unsweetened Soy Milk/Mlekovita lactose-free Milk, retained Robico Kefir/Maluta Skyr, Kimchi, Pamako, fresh Leafy/Microgreen completeness and exact Lunch Proteins/skinless Salmon. Ordinary retailer access and saved grocery lists remain useful preparation but do not close native automation gaps. See the [route audit](DIET_AUTOMATION_GAPS.md); its older dates do not override the current stock findings above.

## Existing commitments and startup

The5November account recheck records six ACTIVE profiles:357/399/Oil-Fish/370 plus exact P60 and P90;361 remains PAUSED with Tempeh and no removal controls. P60 repeats60days, next27December; P90 repeats90days, next26January2027. Profile IDs and separate renewal prices/fees were not exposed. The pantry500156/258958 is one paid344.52zł lot with14SKU/18 ordered packs; its linked parcel520000012680462133044051 records delivery2November10:02, with no timezone printed. Contents, labels and usable balance remain uninspected. **257757 is fully cancelled, verified18November, and contributes no incoming or received food.** Its99.25zł refund is unresolved. Profile399's cancellation is not established, and its historical automatic debit does not establish unattended P60/P90 collection. [Current refund evidence](DIET_PAYMENT_HANDOFF.md#18-november-order257757-cancelled-refund-action).

- **Nut transfer:** replace370 and the old Nut B plan with P60/P90 quantities only after their actual account changes are verified. Existing Nut A's paid800g delivered25September and its later scheduled renewal are not erased by this document. Offset500156/258958 as one paid, carrier-delivered pantry lot with uninspected contents; reconcile actual present Nuts and verify future migration before any further overlapping renewal. The former saved-cart submission step is superseded: do not recreate or repay500156.
- **Oats/Spices:** the paid first order243898 included1kg Oats and first-only Cinnamon/Cloves/Cardamom. Carrier delivery does not establish today's remainder.500156 ordered another1.5kg Oats and is carrier-delivered; inspect the actual packs/labels and count usable stock before any further overlapping purchase. Do not infer that the ordered mass was received intact or remains unused.
- **Oil/Fish500125:**163.53zł is paid; GLS33685101618 displays DELIVERED28October12:29, checked29October, with no timezone printed. Merchant“W drodze” is an older fulfillment status, not a new failure. Contents/condition/current usable balance remain uninspected. Offset overlapping purchases without inventing remaining stock. At the model's illustrative0.915g/ml,1L Phileos/30days supplies915g against405g fixed demand: **510g excess per30days**. Its recurrence needs a stock-balanced quantity/cycle; optional Dinner Nothing does not consume that excess. Pamako is separate, and the new Fish jars do not silently change canonical products/portions.
- **Produce/Egg pipeline:**357 and399's accepted renewals are separate from new public-page availability. Use their actual fulfilled quantities and arrival/quality evidence before adding overlapping fresh lines.361 remains paused; removing Tempeh/Tofu from the Diet is not a claim that its stored merchant template was edited.
- **Older stock:** seven unopened Sauerkraut jars, Seeds, Milk, Kefir, Fish and produce were reported in September; later Egg/Blueberry counts are from6October. Those are dated observations, not27October measured balances and not proof of consumption. September's Matcha200g report is superseded by the user's2November0g report. One current stock/expiry inventory should set other first purchases; do not use invented depletion dates.

## Phase validation and activation sequence

1. Do not recreate or repay500156/258958: its14-SKU/18-pack ordered pantry lot is paid and carrier-delivered2November10:02, verified5November with no carrier timezone printed. Inspect actual received quantities, condition and labels before assigning usable portions. Reconcile still-active370 with the verified ACTIVE P60/P90 cycles, and qualify their unquoted renewal prices, isolated home fees and unattended payment before any further overlapping commitment.
2. Prepare the Egg/Berry14day candidate only as part of the complete Egg and Berry allocation. Add the other Egg streams to independently qualifying fresh groups; do not activate all first cartons together.
3. Source the uncovered weekly protein/vegetable/Microgreen/fruit/ferment/milk categories using approved foods and actual available native routes. Record ordinary manual routes as gaps, not subscriptions. Prioritize Turkey and skinless Salmon as the user selected28October; keep the deferred Trout candidate outside active quantities and purchases.
4. Model actual arrival events, edible yields, openings, expiry and full portions. Use210days for7/14/21/30-day phase comparisons and420days when60-day lines join those streams. P60/P90 pantry arithmetic repeats over180days; including28/90-day streams can require a1,260-day combined horizon. A shorter demand table or84-day rate equivalent is not that arrival-calendar proof.
5. Check every resulting actual shipment, including isolated renewals, against approximately100zł net goods, logistics≤10% of goods and the per-product25% delivered-price cap. Do not rely on first-checkout consolidation carrying over to different renewal cycles.

**Ready conclusion:** the complete consumption requirements and a better qualifying pantry replacement are specified. The matching first pantry purchase is now confirmed paid as500156. P60/P90 profiles and cycles are now verified ACTIVE. Remaining work is370 overlap resolution, renewal-price/fee/payment qualification, exact-route coverage, stock/arrival allocation and phase/expiry validation. Six active profiles do not establish full unattended Diet coverage or a globally optimal freshness schedule.
