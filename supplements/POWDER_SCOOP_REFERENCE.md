# Powder scoop reference

Research checked **2026-11-13**, including the deeper verification requested in [PR #53](https://github.com/PawelTroka/health-protocol/pull/53). The original audit used [main commit bba87301](https://github.com/PawelTroka/health-protocol/blob/bba87301bbdc61d441de30173df9354a1ec7b49f/README.md); the review explicitly changed EAA to 15g and made exactly 4scoops the standalone Collagen target.

**Four manufacturer scoop capacities are verified: WPI 70ml, EvoBomb 15ml, Cluster Dextrin 50ml and RawSeries EAA 25ml.** MicroVitamin+, KFD Collagen, KFD Creatine and ALLHydrate still have unverified physical capacities. Psyllium uses a standard measuring tablespoon, which is a separate kind of measurement.

## How to read the annotations

- `30g — 1scoop (70ml)`: the powder dose is 30g; the manufacturer's specified scoop capacity is 70ml.
- `20g — 2scoops (2x15ml)`: each scoop holds 15ml; two measures have a combined nominal volume of 30ml.
- `15g — 1scoop (25ml)`: the revised EAA dose matches the manufacturer's full serving.
- `~13.33g — 4scoops (ml unverified)`: exactly four product-specific Collagen scoops are the target; the approximate mass is calculated from the manufacturer's mass/count ratio.
- `ml unverified`: the checked evidence establishes a powder mass or scoop count without establishing the physical capacity. It does not mean zero volume or permission to assume a common size.
- `ml` and `cc` denote the same volume. Powder grams are a different quantity. The water used to prepare a drink is also separate. HSN explains these distinctions in its [measuring guide](https://www.hsnstore.eu/hsn-scoops).

Keep the written gram targets, except for Collagen, whose target is exactly 4scoops. Scoop-to-mass ratios can vary with powder, flavour, batch and filling. KFD explicitly specifies a level scoop for creatine; the other active-product directions checked here do not establish a level/heaped convention. Check powder mass with the actual measure before relying on an approximation, especially after replacing a scoop. For Collagen, weighing four scoops can refine the nutrition estimate; it does not replace the chosen count with a 13g target.

## Active products

The table covers all nine distinct supplement powders in the active drink sections. WPI occurs twice; the existing ALLHydrate sauna addition is also included. Capacities below describe the manufacturer's specified measure, not a guarantee that a scoop is supplied.

| Protocol code | Exact selected product | Scheduled protocol dose | Physical capacity of one measure | Manufacturer mass/count evidence and practical use |
| --- | --- | --- | --- | --- |
| M.0.2 | GymBeam Psyllium Husks | 7.5g | **15ml metric measuring tablespoon**; not a manufacturer scoop claim | GymBeam gives 5g per 2tsp. Three metric teaspoons equal 1tbsp; the 7.5g relationship is approximate. Weigh the retained dose. [Product](https://gymbeam.pl/psyllium-husks-gymbeam.html) · [Metric units](https://www.nist.gov/pml/owm/metric-si/metric-kitchen/metric-kitchen-cooking-measurement-equivalencies) |
| M.0.4 / A.0.1 | HSN RawSeries 100% Whey Protein Isolate, Unflavored, 2kg | 30g Morning + 30g After Workout | **70ml** | One 70ml scoop corresponds to approximately 30g. Annotate both entries `1scoop (70ml)`. [Exact 2kg label](https://www.hsnstore.at/en/brands/raw-series/100-whey-protein-isolate-2kg-unflavoured) |
| M.0.3 | MicroVitamin+ Powder, Unflavored v8; variant 50000745464093 | 26g | **Unverified** | The exact official label specifies 26g as approximately one scoop. Use `~1scoop (ml unverified)` in the active entry and Diet summary; do not substitute another flavour or an older formula. [Exact variant](https://microvitamin.com/products/microvitamin-plus?variant=50000745464093) · [Facts image](https://microvitamin.com/cdn/shop/files/MixedBerryv8UNFLAVORED-Back2.webp?v=1778185196&width=1946) |
| B.0.3 | KFD Ultra Pure Joint Collagen, 300g; EAN 5905255800854 | **Exactly 4scoops (~13.33g)** | **Unverified** | Manufacturer: 5g per 1.5scoops. Four actual scoops are the chosen target; their mass is an estimate. No level/heaped convention is specified. [Directions](https://sklep.kfd.pl/kfd-ultra-pure-joint-collagen-300-g-p-8440.html) · [Manufacturer sheet](https://storage.googleapis.com/allegro-offer-attachments/7833abb2a7816a0f7ee37c35cdbc30b2d04041b0abb74e56f88a960edbdf4719) |
| B.0.1 | KFD Premium Creatine, 500g; pure monohydrate / natural-flavour interpretation | 5g | **Unverified** | Ordinary variants use 5g per level scoop. The generic product link does not lock a flavour; the raspberry-jelly variant has different instructions. Retain the 5g target and level-fill instruction. [Directions](https://sklep.kfd.pl/kfd-premium-creatine-500-g-kreatyna-monohydrat-p-4139.html) |
| B.0.2 | HSN EvoBomb 2.0, Lemon | 20g | **15ml** | Dedicated manufacturer serving panels specify two 15ml scoops per approximately 20g. Annotate `2scoops (2x15ml)`. [Serving panel](https://www.hsnstore.eu/brands/sport-series/evobomb) · [Scoop mapping](https://www.hsnstore.eu/brands/hsn-accessories/scoop-hsn-25cc) |
| IW.0.2 | ALLHydrate Electrolytes Neutral, 205g; EAN 5903242584015 | 2.73g; existing sauna addition +2.73g | **Unverified** | Official serving: 4.1g per 1.5scoops. One scoop's approximately 2.73g is the rounded calculation, not a volume. The Diet summary, active drink and sauna addition all retain `1scoop (ml unverified)`. [Aliness](https://aliness.pl/allhydrate-elektrolity-neutral-205-g-50-porcji/) · [Brand page](https://allhydrate.pl/product/elektrolity-neutral/) |
| IW.0.3 | HSN RawSeries Cluster Dextrin, unflavoured pure HBCD | 25g | **50ml** | One 50ml scoop corresponds to approximately 25g. Annotate `1scoop (50ml)`. [Manufacturer panel](https://www.hsnstore.at/marken/raw-series/cluster-dextrin-hochverzweigtes-zyklisches-dextrin-pulver) |
| A.0.2 | HSN RawSeries Essential Amino Acids, Unflavored, 1kg | **15g — 1scoop** | **25ml** | One full 25ml scoop corresponds to approximately 15g. The review adopts that full serving. [Exact 1kg label](https://www.hsnstore.com/marcas/raw-series/aminoacidos-esenciales-eaa-s-en-polvo-1kg-sin-sabor) |

## Product-specific findings and exclusions

### HSN: exact products and serving panels

The WPI source is the selected unflavoured RawSeries isolate in the 2kg pack. A scoop value for Evowhey concentrate or flavoured Evolate is not needed to establish it. Cluster Dextrin evidence refers to pure RawSeries HBCD, not flavoured EvoDextrin or a recovery blend.

For **EAA**, the review changes the scheduled powder dose from 10g to **15g — 1scoop (25ml)**. The exact manufacturer's full-serving panel supplies 4.71g Leucine, 2.526g Lysine base, 1.686g each Isoleucine and Valine, 1.551g Threonine, 765mg Histidine base and 421.5mg each Methionine, Phenylalanine and Tryptophan. These sum to 14.1885g amino-acid bases, displayed as ~14.189g. Lysine/Histidine hydrochloride masses are not added again. The [official accessory table](https://www.hsnstore.eu/brands/hsn-accessories/scoop-hsn-25cc) distinguishes the selected RawSeries EAA's 25ml scoop from **EvoEAA's 10ml scoop**.

For **EvoBomb**, the dedicated use instructions and serving panels agree on 2x15ml per 20g. Some generic narrative text says one scoop, including on the [Lemon page](https://www.hsnstore.eu/brands/sport-series/evobomb-500g-lemon); it conflicts with the more specific panels. The exact Lemon dynamic nutrient panel was not exposed in retrieval. The official 15ml product-to-scoop mapping and [tasting-pack directions covering Lemon](https://www.hsnstore.pl/marki/hsn-packs/evobomb-zestaw-degustacyjny) corroborate the selected annotation. No flavour-dependent ingredient changes are made here.

Some HSN pages omit their dynamic nutrition fields from a normal text rendering while search retrieval of the same official URL exposes the dose panel. The linked manufacturer panels, exact product identity and corroborating scoop table provide the evidence.

The current [HSN scoop policy](https://www.hsnstore.eu/hsn-scoops) distinguishes powdered foods/proteins, which no longer come with a free scoop, from eligible powdered supplements for which a scoop can be selected at ordering. These capacities therefore mean **manufacturer-specified**, not necessarily **included**.

### KFD: grams are documented; ml remains unresolved

The collagen ratio gives `4 x 5 / 1.5 = 13.333...g`. The review makes **exactly four scoops** the operational target and uses ~13.33g only as the estimated powder mass. There is no approximation marker on the four-scoop count, and no remaining instruction to weigh 13g instead.

KFD's current creatine directions distinguish raspberry-jelly flavour, which uses 4.2g per four-fifths of a scoop, from ordinary variants using 5g per level scoop. The protocol's pure-monohydrate identity should not be interpreted as an arbitrary flavoured mixture.

The [official KFD scoop set](https://sklep.kfd.pl/kfd-komplet-miarek-p-6803.html) lists several accessory sizes; that does not identify either product's supplied scoop. Old purchaser reports of a 10ml creatine scoop are not current SKU/batch confirmation and were excluded.

The direct KFD label attachments for [collagen](https://sklep.kfd.pl/index.php?controller=attachment&id_attachment=716) and [natural creatine](https://sklep.kfd.pl/index.php?controller=attachment&id_attachment=994) remained inaccessible. The review follow-up recovered complete manufacturer sheets through the [official KFD Allegro store](https://allegro.pl/uzytkownik/SMA-KFD): [collagen listing](https://allegro.pl/produkt/kfd-pure-joint-collagen-hydrolizat-kolagenowy-300-g-ffc822b9-b785-4d25-87e7-84f59ccaaed9?offerId=18578260685) / [PDF](https://storage.googleapis.com/allegro-offer-attachments/7833abb2a7816a0f7ee37c35cdbc30b2d04041b0abb74e56f88a960edbdf4719), and [natural-creatine listing](https://allegro.pl/produkt/kreatyna-proszek-naturalny-kfd-500-g-fa5e7d5a-72af-49e4-9d1d-57bc153fd7d5?offerId=15712768128) / [PDF](https://storage.googleapis.com/allegro-offer-attachments/25f87b809968df56a31a8deacaa859bf33b05ff8e97fa41cee6b5bfc6daae79c).

Both complete sheets were rendered and visually inspected. They match collagen EAN **5905255800854** and natural-creatine EAN **5901947663547**, confirm the mass/count instructions, and provide no ml/cc capacity. Their batch/date fields are blank templates, so they also cannot identify the scoop supplied with a particular tub. Current exact-product rear-label and scoop/photo leads supplied no readable capacity marking.

### MicroVitamin+: exact unflavoured v8 label

The exact product variant maps to Unflavored, SKU/barcode **00199284018150**. The [facts image](https://microvitamin.com/cdn/shop/files/MixedBerryv8UNFLAVORED-Back2.webp?v=1778185196&width=1946) was visually inspected and specifies 26g, approximately one scoop. Despite its filename containing “MixedBerry”, the image and exact-variant mapping identify the Unflavored label.

The [rear label](https://microvitamin.com/cdn/shop/files/Unflavoredv8Template-Back1.webp?v=1778185612&width=1946) gives 300–500ml of mixing liquid. The [Unflavored v8 certificate image](https://microvitamin.com/cdn/shop/files/certificateofanalysis_coa_MicroVitamin_v8unflavored-1.webp?v=1778185201&width=1946) confirms a 26000mg serving, product 20562, lot 2512065. Neither establishes scoop capacity. The [FAQ](https://microvitamin.com/pages/microvitamin-plus-faq) also does not resolve ml.

The review follow-up enumerated and visually inspected all 13 official gallery assets from the [public product data](https://microvitamin.com/products/microvitamin-plus.json), plus both pages of the [original Unflavored v8 CoA PDF](https://cdn.shopify.com/s/files/1/0736/2907/3693/files/coa-microvitamin-plus-unflavoured-v8.pdf). None gives scoop capacity or a readable marked scoop; the CoA's physical-characteristics fields do not supply volume or bulk density. Manufacturer FAQ/changelog and exact-SKU searches did not close the gap. Manufacturer-linked video metadata/thumbnails were checked, but full video contents were not verified. A retailer image described as showing a scoop was actually an older Mixed Berry label. The active entry and Diet summary now preserve the label's **approximate** one-scoop relationship as `26g — ~1scoop (ml unverified)`.

### ALLHydrate: keep scoop and serving distinct

Both official sources agree on **4.1g = 1.5scoops** for Neutral 205g. The calculation `4.1 / 1.5 = 2.733...` explains the protocol's rounded 2.73g. The manufacturer's litre of water is dilution, not capacity.

Retailer descriptions simplifying the full serving to one scoop, and catalogue fields listing 205ml for a 205g package, do not establish scoop volume. Other ALLHydrate products and flavours are different formulations. The existing sauna addition and hydration review note remain in the protocol.

The review follow-up inspected official media attachments, including the [September 2025 image](https://aliness.pl/wp-content/uploads/2025/09/961.jpg) and [January 2026 image](https://aliness.pl/wp-content/uploads/2026/01/ele_neutral-kopia.jpg), the brand-page media, exact-product pharmacy galleries and UK listing. These show the front of a closed tub, without a scoop or capacity marking. Two retailer-generated product cards repeat 4.1g/1.5scoops without ml. No exact-product rear-label or scoop specification was recovered; manufacturer, catalogue and video searches also left this unresolved. The 2.73g dose, sauna addition and three README scoop mentions stay synchronized.

### Psyllium: a measuring spoon, not a branded scoop

GymBeam's [Polish instructions](https://gymbeam.pl/psyllium-husks-gymbeam.html) and [English instructions](https://gymbeam.com/psyllium-husks-gymbeam.html?tab=detail) agree on **5g per 2tsp**. Scaling this published mass/count relationship gives `7.5 / 5 x 2 = 3tsp`. With the [metric cooking convention](https://www.nist.gov/pml/owm/metric-si/metric-kitchen/metric-kitchen-cooking-measurement-equivalencies), three 5ml teaspoons occupy one 15ml tablespoon. The manufacturer does not specify a level/heaped convention, so the active entry is **`7.5g — ~1tbsp (15ml measuring spoon)`**. The 7.5g remains a weighed target; this does not establish an exact 7.5g-per-15ml density or a supplied GymBeam scoop.

## Retired scoop entry

The Removed section still identifies **Transparent Labs BULK “White Cherry” 1scoop**. It remains annotated `ml unverified` and retired. The [current manufacturer page](https://www.transparentlabs.com/products/bulk-preworkout) describes a level scoop.

The review follow-up matched the [current White Cherry variant 44248689082461](https://www.transparentlabs.com/products/bulk-preworkout?variant=44248689082461), SKU **TPL001122**, barcode **874659003336**, through the [official public product data](https://www.transparentlabs.com/products/bulk-preworkout.js). Both the [White Cherry facts panel](https://cdn.shopify.com/s/files/1/0866/7664/files/Bulk_White_Cherry_SFP_1.png?v=1773067066) and [second official White Cherry graphic](https://cdn.shopify.com/s/files/1/0866/7664/files/02_white_cherry_92f38de7-126d-4f9d-8ae3-cbf51948e041.jpg?v=1782244641) were visually inspected and specify **1scoop = 20.6g**. Neither gives ml/cc. This verifies the current flavour's mass instead of borrowing another flavour's 20.8g, but it does not identify the user's retired tub/formula or establish its physical scoop capacity. Mixing water and powder mass remain separate from scoop volume.

## Closing the remaining capacity gaps

For MicroVitamin+, both KFD powders and ALLHydrate, and the retired BULK scoop if historical documentation is needed:

1. Match the actual scoop to the product, flavour and tub/lot. Read or photograph any moulded **ml/cc** marking.
2. If there is no marking, obtain the manufacturer's specification for the scoop's brimful capacity and whether its serving is level or heaped.
3. A direct water-volume measurement of the actual scoop can provide a practical replacement size. Repeat the measurement using a graduated measure, record it as **measured**, and dry the scoop completely before returning it to powder.
4. Verify powder mass with the replacement scoop. For Collagen, measure the mass of four original scoops to calibrate an equivalent replacement; do not silently redefine the target as four arbitrary scoops or 13g. Record the evidence, method and date before replacing `ml unverified` with a numerical capacity.

No numerical capacity was inferred from powder grams, typical bulk density, another product's scoop or the amount of mixing water.

## Scope and verification

Research used official product instructions, multilingual HSN panels, official accessory mappings, exact-variant packaging images and public product data, manufacturer CoA/product-sheet PDFs, FAQs and targeted capacity searches. The review added recovered KFD sheets, the complete MicroVitamin+ CoA and gallery, expanded ALLHydrate media checks, the exact White Cherry panel and a recheck of GymBeam's teaspoon instructions. Retailer and historical leads were checked for conflicts but did not override matching primary evidence.

The PR annotates all active product scoop counts, both WPI entries, the sauna addition, the Diet scoop summaries and the retired BULK entry. The review authorizes two dose changes: **EAA 10g→15g** and **Collagen 13g→exactly 4scoops (~13.33g)**. README amino-acid quantities, meal estimates, daily totals, Diet rotations and replacement notes are reconciled: After Workout becomes 176kcal, Before Workout ~120kcal, and the reference day ~2,417kcal with ~195.8g dietary Protein, including ~25.8g Collagen. The EAA allowance remains the existing 4kcal/g-powder model, now 60kcal. Other doses, timing, product/BJ links and physical pillbox entries are preserved.
