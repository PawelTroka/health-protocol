# Powder shopping and subscription audit

**Checked 2026-11-08 · Poland · source protocol: [README](../README.md), main commit `ce7915837cc47fa23b728b22afd7b1d2fd55dc4b`.**

## Decision

**MicroVitamin+ is the strongest exact-product subscription candidate: the Polish storefront advertises 400 PLN for a one-time purchase and subscriptions from 360 PLN.** Its subscription policy explicitly allows recurring deliveries and automatic charging. The remaining problem is delivery: the shipping policy lists **29 PLN for Poland**, while the site advertises free shipping for “3+ bottles.” Free home delivery for three **powder tubs**, and the exact recurring plan behind “from 360 PLN,” were not established. Treat it as a conditional candidate until those two conditions are visible in checkout. [MV1][MV2][MV3]

**None of the nine powder lines was fully verified to meet all four shopping requirements simultaneously:** the exact selected formulation, automatic repeat orders/payment, free home courier delivery in Poland, and no more than a 25% delivered-price premium. This audit therefore retains the current protocol links and provides the best verified manual prices, subscription candidates and explicit rejection reasons. A stock notification, paid discount membership or email asking for payment does not complete an automatic order.

A second useful finding is **GymBeam's natural creatine monohydrate, 1 kg for 53.90 PLN**. At the existing standalone 5 g/day it costs 8.09 PLN/30 days before shipping, below both KFD's regular price and its observed promotion. GymBeam has a genuine subscription service, but the required subscription selector was not exposed for this exact SKU. It is a promising candidate, **not a verified subscription recommendation or an implemented brand replacement**. [G1][G2]

“Lowest checked” below means lowest among the specified comparable listings checked during this audit. It does not mean a guaranteed lowest price across every Polish seller. Dynamic selectors, stock, sales and delivery conditions can change; unresolved quotes remain unresolved rather than being estimated from a different size, flavour or country.

## Scope and comparison rules

This covers every active drink/supplement powder: nine purchased products across ten slot references, because the same WPI is used twice. Culinary powders such as Cocoa, Matcha, spices and seed flours belong to the food audit; capsules, tablets and TODO/Removed products do not belong in this audit. The [canonical protocol](../README.md) owns all doses and timing.

- **Quality comes first:** preserve the selected identity, active amount, flavour and label. FORTIGEL®, Cluster Dextrin®, MicroVitamin+, EvoBomb 2.0 Lemon and ALLHydrate Neutral are not interchangeable with generic lookalikes. WPI remains unflavoured isolate; EAA remains the complete unflavoured formula without additional B6. Manufacturer testing claims are useful procurement information, not proof that every purchased lot has been independently checked or that a more expensive brand improves longevity, appearance or sexual outcomes.
- **Automatic means automatic:** the merchant must generate and charge subsequent orders without a manual confirmation or new checkout. A store-wide programme alone does not prove the selected pack participates.
- **Price means repeat price:** keep introductory coupons and current sales separate from the ongoing subscription price. “From” pricing without the matching plan is not a firm quote.
- **Delivery means home courier:** lockers, collection points and click-and-collect do not satisfy the protocol's shopping requirement. Free-delivery thresholds apply to each shipment, not lifetime spending. Do not add unnecessary products merely to reach a threshold.
- **Premium flags:** flag an increase of **at least 10% or 10 PLN/30 days**; exclude a subscription route with a verified delivered-price premium above **25%**. Compare the same usable powder dose and report both the existing regular-price and promotion benchmarks where known.

The recurring delivered unit price is `(pack count × recurring pack price + home-delivery charge + checkout taxes/duties) / total usable grams`. Multiply it by actual consumption over 30 days. Allocate a shared parcel fee once across the basket; do not charge the entire fee to each product in a basket comparison. Prices in the tables are **merchandise prices unless expressly described as delivered**.

## Complete active inventory and recommended route

| Protocol item | Exact product link and pack | Consumption and pack life | Price evidence, PLN | Subscription decision |
|---|---|---|---|---|
| **M.0.2 — Psyllium Husk** | [GymBeam Psyllium Husks, 500 g](https://gymbeam.pl/psyllium-husks-gymbeam.html) | 7.5 g/day standalone; **225 g/30 days**; 66.7 days/pack. The 2.5 g in MicroVitamin+ is separate. | **44.90 estimated**, currently out of stock; expected restock 13 November. At that indicative price: 89.80/kg and **20.21/30 days**. This is **not an available purchase quote**. | Retain current product pending stock. Its “Subskrybuj” stock alert is not autoship. Exact iHerb alternatives below are substantially dearer. [G3] |
| **M.0.4 + A.0.1 — Grass-fed Whey Protein Isolate (WPI) Unflavored** | [HSN RawSeries, 2 kg unflavoured](https://www.hsnstore.pl/marki/raw-series/100-whey-protein-isolate-2-kg-bez-smaku) | 30 g morning + 30 g after workout; **1,800 g/30 days**; 33.3 days/pack. | Exact Polish **2 kg** price was not accessible in the dynamic selector. Monthly merchandise budget = **0.9 × the 2 kg price**. | Keep exact HSN formulation. No true autoship verified. Do not substitute a category “from” price for 500 g, a flavoured isolate, concentrate or a foreign checkout quote. [H1][H5] |
| **M.0.3 — MicroVitamin+ Powder Unflavored** | [Original selected variant, 26 g serving](https://microvitamin.com/en-pl/products/microvitamin-plus?variant=50000745464093); 30 servings/780 g | **780 g/30 days**; 30 days/tub. | Polish storefront **400 one-time / from 360 subscription**. Advertised merchandise saving **40/30 days, 10%**, if that plan applies to the selected powder. | **Conditional first choice.** Actual automatic billing verified; selected plan/cadence and free home shipping for powder tubs require checkout evidence. Preserve the entire blend. [MV1–MV4] |
| **B.0.3 — Collagen Peptides** | [KFD Ultra Pure Joint Collagen, 300 g](https://sklep.kfd.pl/kfd-ultra-pure-joint-collagen-300-g-p-8440.html), pure FORTIGEL® | 13 g/day; **390 g/30 days**; 23.1 days/pack. | **38.99/300 g** direct; **129.97/kg**, **50.69/30 days**. Lowest checked comparable merchandise price; other checked listings were higher. | Keep original direct link. No automatic plan established. Generic hydrolysed collagen, flavoured Collagen PLUS or a blend with MSM is not an exact replacement. [K1][K3] |
| **B.0.1 — Creatine monohydrate** | [KFD Premium Creatine, natural, 500 g](https://sklep.kfd.pl/kfd-premium-creatine-500-g-kreatyna-monohydrat-p-4139.html) | 5 g/day standalone; **150 g/30 days**; 100 days/pack. The 5 g in MicroVitamin+ is separate. | **35.99 regular / 27.72 observed sale**; 71.98 / 55.44 per kg; **10.80 / 8.32 per 30 days**. [GymBeam natural 1 kg](https://gymbeam.pl/100-monohydrat-kreatyny-gymbeam.html) **53.90**, **8.09/30 days**, is the lower checked manual alternative. | No exact-SKU automatic plan proved for KFD or GymBeam. GymBeam is a price candidate only. Keep the canonical KFD link until a specific change is chosen; do not replace with flavoured creatine of a different concentration. [K2][G1][G2] |
| **B.0.2 — HSN EvoBomb 2.0 “Lemon”** | [HSN EvoBomb](https://www.hsnstore.pl/marki/sport-series/evobomb), select **Lemon**, 500 g if available | 20 g every day; **600 g/30 days**; 25 days per 500 g. | Exact current **Lemon** price unavailable. For a 500 g tub, budget **1.2 × its verified price/30 days**. | Keep exact formulation and flavour. No automatic plan established. The visible Exotic Fruits offer and smaller-pack “from” prices are not valid Lemon price evidence. [H2][H5] |
| **IW.0.2 — ALLHydrate Electrolytes Neutral** | [Current Allegro 205 g listing](https://allegro.pl/oferta/allhydrate-by-aliness-neutral-elektrolity-205-g-50-porcji-17359439491); [official Aliness 205 g](https://aliness.pl/allhydrate-elektrolity-neutral-205-g-50-porcji/) | 2.73 g/day plus 2.73 g per sauna; baseline **81.9 g/30 days** and 75.1 days/pack. | Both checked listings **59.90/205 g**; **23.93/30 days** before extra sauna use; **+0.80 per extra scoop**. | Retain exact neutral blend; no autoship established. “50 portions” on the pack uses the manufacturer's larger serving, not the protocol's 2.73 g scoop. Home-shipping eligibility must be distinguished from a generic free-delivery banner. [A1][A2] |
| **IW.0.3 — Highly Branched Cyclic Dextrin (Cluster Dextrin®)** | [HSN RawSeries Cluster Dextrin®](https://www.hsnstore.pl/marki/raw-series/cluster-dextrin-silnie-rozgaleziona-cykliczna-dekstryna-w-proszku), choose the quoted pack size | 25 g on days it is used; **25 × qualifying days** in a 30-day period, maximum 750 g. A 1 kg pack lasts 40 uses. No second serving for sauna. | Exact selected-pack Polish price unavailable. With a verified 1 kg quote, maximum monthly budget is **0.75 × that quote**; scale to actual use. | Preserve branded HBCD; no automatic plan verified. Generic maltodextrin is not a comparable substitute. Do not use an unlabelled category minimum as a 1 kg price. [H3] |
| **A.0.2 — Essential Amino Acids (EAA) Unflavored** | [HSN RawSeries EAA, 1 kg unflavoured](https://www.hsnstore.eu/brands/raw-series/essential-amino-acids-eaa-s-powder-1kg-unflavoured) | 10 g/day; **300 g/30 days**; 100 days/pack. | Exact current price for this selected pack/destination unavailable. Monthly merchandise budget = **0.3 × the 1 kg price**. | Keep all nine EAA and the current formula, including 3.14 g Leucine and approximately 9.459 g amino-acid bases per 10 g. BCAA, a different ratio or an added-B6 formula is not an exact substitute. No autoship established. [H4][H5] |

The two WPI servings, standalone Creatine and Psyllium, and ingredients embedded in MicroVitamin+ are counted without adding a second purchase for the embedded amounts. The existing daily EvoBomb, pre-workout Collagen, post-workout WPI/EAA and pill-before-drink sequence remain as written in the protocol.

## Subscription candidates and meaningful premium flags

### MicroVitamin+: actual subscription, exact shipping/plan still conditional

Use the [original unflavoured powder variant](https://microvitamin.com/en-pl/products/microvitamin-plus?variant=50000745464093), not MicroVitamin capsules. The Polish homepage displays the powder at **400 PLN / from 360 PLN**; the cheaper capsule prices elsewhere on that page do not apply. Its [subscription policy](https://microvitamin.com/policies/subscription-policy) states that recurring payments are charged to the stored method and explains changes/cancellation. The [shipping policy](https://microvitamin.com/policies/shipping-policy) lists Poland at 29 PLN, an international dispatch-processing window of 2–5 business days, and delivery in 5–7 business days after dispatch. The separate “free shipping on 3+ bottles” banner does not settle whether powder tubs qualify. [MV1–MV3]

**Illustration, not a verified checkout quote:** if the selected plan really costs 360 PLN/tub and sends one tub every 30 days with a 29 PLN fee, it would be **389 PLN/30 days**, versus **429 PLN** for the same one-time order: 40 PLN saved, or 9.3% delivered. If three tubs can be delivered together every 90 days at that same unit price and one 29 PLN charge, the amortised figures would be **369.67 versus 409.67 PLN/30 days**. If the banner actually makes that parcel free, these become 360 versus 400. These scenarios show why the exact quantity, frequency and courier cost must be captured before enabling the plan; they do not assert that all three configurations are offered.

**Procurement check:** retain 26 g/serving and the matching unflavoured label. The readable product text includes Collagen 12.5 g, Creatine monohydrate 5 g, Psyllium 2.5 g, Taurine 1 g and TMG 500 mg, alongside the rest of the existing micronutrient blend. The manufacturer publishes powder testing documents; match the document to the actual flavour and lot/version, rather than applying a capsule score to the powder. [MV4][MV5]

### iHerb: genuine product selectors, but the checked alternatives exceed the price cap

The following exact product pages expose **Subscribe & Save / delivery-frequency selection**. Their recurring discount was not visible without the cart, so the numbers below are the **displayed merchandise prices before any unverified subscription discount**, not fabricated guaranteed repeat prices. The Polish shipping page currently advertises free **InPost home courier** above 150 PLN for a limited time and 22 PLN below the threshold, with item/carrier restrictions and applicable checkout adjustments. A single cheap-looking product does not necessarily produce a free shipment. [I1–I4]

| Exact candidate | Displayed pack price and equivalent 30-day cost | Premium against existing/manual route | Decision |
|---|---|---|---|
| [California Gold Nutrition Sport Pure Creatine Monohydrate, unflavoured, 1 kg](https://pl.iherb.com/pr/california-gold-nutrition-sport-pure-creatine-monohydrate-unflavored-2-2-lbs-1-kg/143718) | **122.60 PLN/kg**; **18.39 PLN/30 days** at 5 g/day | Against KFD regular: **+70.3%, +7.59 PLN/30 days**. Against KFD's observed sale: **+121.1%, +10.07 PLN/30 days**. Against GymBeam manual 53.90/kg: **+127.5%, +10.31 PLN/30 days**. | **Flagged; do not select at this price.** Exceeds 25% when both the shared subscription parcel and the comparable manual basket qualify for free delivery. A single pack is below the 150 PLN shipping threshold. [I2] |
| [Nutricost Psyllium Husk, unflavoured, 454 g](https://pl.iherb.com/pr/nutricost-psyllium-husk-unflavored-16-2-oz-454-g/129089) | **92.96 PLN**; 204.76/kg; **46.07 PLN/30 days** at 7.5 g/day | Against GymBeam's **out-of-stock estimated** 44.90/500 g: **+128.0%, +25.87 PLN/30 days**. Benchmark remains provisional until stock returns. | **Flagged; do not select at this price.** No demonstrated quality benefit warrants treating this premium as acceptable. Its single-pack order also falls below free shipping. [I3][G3] |
| [Organic India Psyllium Whole Husk Fiber, 340 g](https://pl.iherb.com/pr/organic-india-psyllium-whole-husk-fiber-12-oz-340-g/8760) | **85.55 PLN**; 251.62/kg; **56.61 PLN/30 days** | Against the same provisional GymBeam benchmark: **+180.2%, +36.41 PLN/30 days**. | **Flagged; do not select.** Organic certification is a traceable sourcing attribute, not proof of superior health outcomes or a substitute for contaminant testing. [I4][G3] |

For the creatine candidate to fit the 25% merchandise cap, its confirmed recurring price would have to be at most **89.98 PLN/kg against KFD's regular price**, **69.30 against the observed KFD sale**, or **67.38 against the lower GymBeam manual option**. These are merchandise-price comparisons. Adding delivery to the subscription candidate while holding the manual basket fixed increases its premium; final delivered comparisons must also include manual shipping, compulsory fees and actual qualifying baskets. A modest unverified discount cannot be assumed to close those gaps.

Other checked iHerb creatines were not better-priced substitutes: Nutricost Performance 454 g at 86.96 PLN, NOW Sports 500 g at 111.65 PLN, and Metabolic Nutrition 500 g at 104.36 PLN all had higher merchandise cost per kilogram than the 122.60 PLN CGN option. These comparisons establish the screened alternatives, not every possible account-specific promotion. [I5–I7]

## Merchant delivery and repeat-order audit

| Merchant | What was actually verified | Practical consequence |
|---|---|---|
| **MicroVitamin** | Real recurring charge policy; Polish powder 400/from 360 PLN; Poland shipping 29 PLN; generic free 3+ bottles banner. [MV1–MV3] | Best exact-product candidate. Confirm the chosen powder plan, quantity, repeat price and **free home** shipment before activation. Do not silently treat a generic bottle banner as a checkout result. |
| **GymBeam Poland** | FAQ describes automated orders/payment, cancellation, pauses and combined shipments for coinciding delivery dates. It uses an example discount rather than promising one universal rate. Exact creatine/psyllium eligibility not established. [G2] | A product must offer the actual **“Subskrypcja z rabatem”** option. “Subskrybuj” beside an out-of-stock notification is insufficient. The generic free-delivery-from-179-PLN banner does not independently establish the applicable home-courier method. |
| **HSN Poland** | [Plan oszczędnościowy](https://www.hsnstore.pl/plan-oszczednosciowy) is a paid membership: 3.99 EUR/year or 5.99 EUR/three years plus applicable VAT, an additional 3% discount under its conditions, and no automatic renewal. It does not schedule product orders. [Delivery page](https://www.hsnstore.pl/dostawa) lists home delivery at 42.43 PLN and a free-delivery banner from **374.95 PLN**, with the table rounding the threshold to 374 PLN. Estimated transit 3–5 business days. [H5][H6] | Useful for a consolidated **manual** WPI/EvoBomb/HBCD/EAA basket, not a solution to automatic reordering. Use the higher stated threshold and the actual home courier option; do not assume a collection-point choice is home delivery. Exact basket prices remain to be quoted. |
| **KFD** | Collagen and Creatine direct prices above. The free-from-99-PLN code/banner names **Pocztex PUNKT/AUTOMAT**; generic delivery starts at 10.90 PLN. No exact automatic programme verified. [K1][K2] | The advertised free threshold does not satisfy free home courier. Compare the actual courier quote for a larger basket before calling a direct order “delivered cheapest.” |
| **Aliness / ALLHydrate** | Official 205 g neutral tub at 59.90 PLN; generic free shipping over 300 PLN. Existing Allegro offer also 59.90 PLN. No autoship verified. [A1][A2] | Existing link remains reasonable. Do not buy six electrolyte tubs just to cross a threshold; at baseline that is well over a year's supply. Combine only products already needed, and confirm home courier. |
| **iHerb Poland** | Exact candidate selectors above; current limited-time home-courier threshold 150 PLN, 22 PLN below. [I1–I4] | Combine with already-needed eligible supplements only when shipment dates match. Free delivery does not rescue the checked powder premiums. Do not represent a first-order coupon as the repeat discount. |
| **Liki24** | The dedicated [Polish delivery page](https://liki24.pl/about/delivery-and-payments/) documents UPS/DHL home courier, free delivery from **199 PLN**, UPS Standard from 24.99 PLN below the threshold, and a 14.99 PLN small-order charge below 100 PLN. The generic About Us country list omits Poland, but that omission does not outweigh these destination-specific terms. Selected powder pages did not provide a usable exact recurring quote. [L1] | **Exact powder route unresolved.** Polish delivery is documented; selected formulation/pack, recurring price, stock, subscription participation and any compulsory item-specific fees still require verification. A store-wide “Auto-dostawa” badge does not establish the exact SKU. No selected powder route relies on it. |
| **Bioshi** | Current [terms §5](https://bioshi.pl/pl/terms), effective 23 October 2026, require manual confirmation/payment for recurring proposals and end automatic orders/saved-card charging. [B1] | “Regularnie z potwierdzeniem” does not meet the automatic purchasing requirement, even where a repeat-order discount is advertised. |

## Quantities and reorder cadence

The following are **stock-consumption intervals**, not invented subscription settings. Choose the nearest supported delivery interval only after checking actual pack sizes, expiry dates and inventory. Calendar months vary; a small existing stock buffer is preferable to rounding an interval so far upward that the product runs out.

| Product | Sensible quantity to price | Consumption interval at the unchanged protocol |
|---|---|---|
| MicroVitamin+ | 1 tub, or 3 tubs if the actual plan and shipping support it | 30 / 90 days |
| WPI | 2 kg | 33.3 days; 6 kg would cover 100 days, subject to storage/expiry |
| EvoBomb Lemon | 2 × 500 g, if this exact pack is available | 50 days |
| KFD FORTIGEL | 3 × 300 g | 69.2 days |
| Psyllium | 500 g | 66.7 days; stock currently unavailable |
| Standalone Creatine | Current KFD 500 g | 100 days; GymBeam 1 kg would last 200 days |
| EAA | 1 kg | 100 days |
| ALLHydrate | 205 g | 75.1 days with no sauna; with `s` sauna sessions per 30 days, pack life = `205 / [2.73 × (1 + s/30)]` days |
| HBCD | 1 kg, if selected | 40 actual uses; at `t` qualifying days/30 days, pack life = `1200/t` days |

**Budget that can be calculated now:** the priced original standalone Collagen, Creatine and base ALLHydrate lines total **85.41 PLN/30 days at KFD regular Creatine pricing**, or **82.93 PLN at the observed sale**, before delivery. Add the Psyllium estimate of 20.21 only as a provisional restock allowance, and add MicroVitamin+ at its confirmed checkout plan price. The four HSN exact quotes are missing, so this document deliberately does not present a misleading complete powder total.

## What would make the remaining choices actionable

1. **MicroVitamin+:** capture the exact unflavoured powder plan and repeat unit price; check whether three tubs receive free home delivery to the Polish postcode. This is the highest-value remaining check because the exact-product subscription already exists.
2. **GymBeam:** select the exact natural 1 kg Creatine SKU and check for “Subskrypcja z rabatem,” its actual recurring price, supported cadence and free home courier threshold. Recheck Psyllium only after stock returns. Keep the stock alert separate.
3. **HSN:** quote the exact 2 kg unflavoured WPI, Lemon EvoBomb, selected Cluster Dextrin® pack and 1 kg unflavoured EAA in one Polish basket. The current membership does not automate that basket, regardless of its savings.
4. **Remaining manual items:** preserve FORTIGEL® and ALLHydrate Neutral. A future genuine exact-formula subscription should be compared with the documented manual benchmarks and the same delivered-cost cap.

No product, dose, timing, blend ingredient or physical pillbox entry is changed by this audit. It is purchasing research with identified checkout gaps, not a claim that an automatic order has already been configured.

## Sources

All links were checked on 2026-11-08. Manufacturer/merchant pages supply product, price and service claims; arithmetic is calculated from those claims and the unchanged protocol. Cached search prices, where inconsistent with current pages, were not used as live purchase quotes.

- **[MV1]** [MicroVitamin Polish storefront — powder one-time/subscription starting prices](https://microvitamin.com/en-pl).
- **[MV2]** [MicroVitamin subscription policy](https://microvitamin.com/policies/subscription-policy).
- **[MV3]** [MicroVitamin shipping policy](https://microvitamin.com/policies/shipping-policy).
- **[MV4]** [MicroVitamin+ unflavoured selected variant and product text](https://microvitamin.com/products/microvitamin-plus?variant=50000745464093).
- **[MV5]** [MicroVitamin published testing documents](https://microvitamin.com/en-eu/pages/third-party-testing).
- **[G1]** [GymBeam natural creatine monohydrate — pack price, ingredient and manufacturer testing claims](https://gymbeam.pl/100-monohydrat-kreatyny-gymbeam.html).
- **[G2]** [GymBeam Polish FAQ — subscription mechanics and product eligibility](https://gymbeam.pl/content/czesto-zadawane-pytania).
- **[G3]** [GymBeam Psyllium — current stock/estimated price and notification control](https://gymbeam.pl/psyllium-husks-gymbeam.html).
- **[H1]** [HSN RawSeries WPI 2 kg unflavoured](https://www.hsnstore.pl/marki/raw-series/100-whey-protein-isolate-2-kg-bez-smaku); [manufacturer nutrition panel in another HSN locale, not a Polish price quote](https://www.hsnstore.at/en/brands/raw-series/100-whey-protein-isolate-2kg-unflavoured).
- **[H2]** [HSN EvoBomb](https://www.hsnstore.pl/marki/sport-series/evobomb); [manufacturer formula](https://www.hsnstore.eu/brands/sport-series/evobomb).
- **[H3]** [HSN RawSeries Cluster Dextrin®](https://www.hsnstore.pl/marki/raw-series/cluster-dextrin-silnie-rozgaleziona-cykliczna-dekstryna-w-proszku).
- **[H4]** [HSN RawSeries EAA 1 kg unflavoured](https://www.hsnstore.eu/brands/raw-series/essential-amino-acids-eaa-s-powder-1kg-unflavoured); [manufacturer composition](https://www.hsnstore.com/marcas/raw-series/aminoacidos-esenciales-eaa-s-en-polvo-1kg-sin-sabor).
- **[H5]** [HSN paid savings membership](https://www.hsnstore.pl/plan-oszczednosciowy).
- **[H6]** [HSN Poland home-delivery conditions](https://www.hsnstore.pl/dostawa).
- **[K1]** [KFD Ultra Pure Joint Collagen 300 g](https://sklep.kfd.pl/kfd-ultra-pure-joint-collagen-300-g-p-8440.html).
- **[K2]** [KFD Premium Creatine 500 g](https://sklep.kfd.pl/kfd-premium-creatine-500-g-kreatyna-monohydrat-p-4139.html).
- **[K3]** [Skąpiec comparable KFD Ultra Pure Joint Collagen listings](https://www.skapiec.pl/site/cat/2366/comp/970765294); [Allegro comparable 300 g listing](https://allegro.pl/oferta/kfd-ultra-pure-joint-collagen-300-g-17938599784).
- **[A1]** [Official Aliness ALLHydrate Neutral 205 g](https://aliness.pl/allhydrate-elektrolity-neutral-205-g-50-porcji/).
- **[A2]** [Existing ALLHydrate Allegro listing](https://allegro.pl/oferta/allhydrate-by-aliness-neutral-elektrolity-205-g-50-porcji-17359439491); [Ceneo comparison](https://www.ceneo.pl/177945583).
- **[I1]** [iHerb Poland shipping](https://pl.iherb.com/shipping/pl); [Subscribe & Save programme](https://pl.iherb.com/info/subscribe-save).
- **[I2]** [CGN Sport Pure Creatine Monohydrate unflavoured 1 kg](https://pl.iherb.com/pr/california-gold-nutrition-sport-pure-creatine-monohydrate-unflavored-2-2-lbs-1-kg/143718).
- **[I3]** [Nutricost Psyllium Husk unflavoured 454 g](https://pl.iherb.com/pr/nutricost-psyllium-husk-unflavored-16-2-oz-454-g/129089).
- **[I4]** [Organic India Psyllium Whole Husk Fiber 340 g](https://pl.iherb.com/pr/organic-india-psyllium-whole-husk-fiber-12-oz-340-g/8760).
- **[I5]** [Nutricost Performance Creatine 454 g](https://pl.iherb.com/pr/nutricost-performance-creatine-monohydrate-unflavored-1-lb-454-g/145338).
- **[I6]** [NOW Sports Creatine 500 g](https://pl.iherb.com/pr/now-foods-sports-micronized-creatine-monohydrate-1-1-lbs-500-g/687).
- **[I7]** [Metabolic Nutrition Creatine 500 g](https://pl.iherb.com/pr/metabolic-nutrition-creatine-unflavored-17-64-oz-500-g/129719).
- **[L1]** [Liki24 dedicated Polish delivery and payment terms](https://liki24.pl/about/delivery-and-payments/); [generic About Us FAQ with an inconsistent country list](https://liki24.pl/about-us/); searched powder candidates: [Intenson natural Creatine 255 g](https://liki24.pl/p/intenson-kreatyna-monohydrat-pure-smak-naturalny-255-g/) and [Dr. Popov Psyllium 200 g](https://liki24.pl/p/dr-popov-blonnik-rozpuszczalny-psyllium-200-g/).
- **[B1]** [Bioshi current terms, §5](https://bioshi.pl/pl/terms).
