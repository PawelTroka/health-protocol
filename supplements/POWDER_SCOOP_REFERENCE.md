# Powder scoop reference

Research checked **2026-11-14** for [PR #53](https://github.com/PawelTroka/health-protocol/pull/53). The original audit used [main commit bba87301](https://github.com/PawelTroka/health-protocol/blob/bba87301bbdc61d441de30173df9354a1ec7b49f/README.md). The review changed EAA to 15g and made exactly 4scoops the standalone Collagen target. This follow-up adds numerical estimates wherever the public evidence does not specify capacity, as requested; it makes no further dose changes.

**Four active HSN capacities are manufacturer-specified: WPI 70ml, EvoBomb 15ml, Cluster Dextrin 50ml and RawSeries EAA 25ml.** The other four active product scoops and the retired BULK scoop now have explicit working estimates. Psyllium uses a standard measuring tablespoon.

## How to read the annotations

- `30g — 1scoop (70ml)`: the manufacturer's specified scoop capacity is 70ml.
- `20g — 2scoops (2x15ml)`: two separate 15ml measures, with a combined nominal volume of 30ml.
- `26g — ~1scoop (~60ml est.)`: the label's approximate scoop count is preserved; the ml value is an estimate.
- `~13.33g — 4scoops (4x~10ml est.)`: exactly four original KFD Collagen scoops remain the target. Only their mass and capacity are approximate.
- `est.` distinguishes an estimate from a manufacturer specification or direct measurement. All ranges below are **sensitivity scenarios, not confidence intervals, manufacturer tolerances, dosing tolerances or guaranteed bounds**.
- `ml` and `cc` denote the same volume. Powder grams and preparation-water volume are separate quantities. [HSN measuring guide](https://www.hsnstore.eu/hsn-scoops)

Keep the written gram targets except Collagen, whose target is exactly four original product scoops. A numerical estimate helps identify a scoop's likely scale; it is not a calibrated replacement measure. Check powder mass when changing scoops. For Collagen, use the mass of four original scoops to calibrate an equivalent replacement; weighing the original serving can refine its nutrition estimate without changing the chosen count.

## Active products

The table covers all nine distinct active supplement powders. WPI appears twice; ALLHydrate also has the existing sauna addition.

| Protocol code | Selected product and retained dose | Capacity of one measure | Evidence status and annotation |
| --- | --- | --- | --- |
| M.0.2 | GymBeam Psyllium Husks, 7.5g | **15ml metric tablespoon** | Standard measuring spoon; approximate powder equivalence, not a supplied-scoop claim. `~1tbsp (15ml measuring spoon)`. [Method](#psyllium-a-measuring-spoon-not-a-branded-scoop) |
| M.0.4 / A.0.1 | HSN RawSeries 100% Whey Protein Isolate, Unflavored, 2kg; 30g Morning + 30g After Workout | **70ml** | Manufacturer panel: approximately 30g per scoop. Both entries: `1scoop (70ml)`. [Exact label](https://www.hsnstore.at/en/brands/raw-series/100-whey-protein-isolate-2kg-unflavoured) |
| M.0.3 | MicroVitamin+ Unflavored v8, variant 50000745464093; 26g | **Estimated ~60ml**; broad model ~40–100ml | Low confidence in physical capacity; label says approximately one scoop. `~1scoop (~60ml est.)`. [Calculation](#microvitamin-estimate) |
| B.0.3 | KFD Ultra Pure Joint Collagen, 300g; **exactly 4scoops (~13.33g)** | **Estimated ~10ml each**; ~5–15ml | Low confidence; FORTIGEL density proxy and explicit fill sensitivity. `4scoops (4x~10ml est.)`. [Calculation](#kfd-collagen-estimate) |
| B.0.1 | KFD Premium Creatine, 500g; natural/pure-monohydrate interpretation; 5g | **Estimated ~10ml**; ~7–12ml | Moderate confidence as a working estimate: historical marked-scoop reports plus density cross-check. Current lot not confirmed. `1scoop (~10ml est.; level)`. [Evidence](#kfd-creatine-estimate) |
| B.0.2 | HSN EvoBomb 2.0, Lemon; 20g | **15ml** | Dedicated manufacturer panels specify 2x15ml per approximately 20g. `2scoops (2x15ml)`. [Panel](https://www.hsnstore.eu/brands/sport-series/evobomb) |
| IW.0.2 | ALLHydrate Electrolytes Neutral, 205g; 2.73g and sauna +2.73g | **Estimated ~3ml**; ~2–4ml | Low confidence in physical capacity; ingredient bulk-volume model. All three README mentions: `1scoop (~3ml est.)`. [Calculation](#allhydrate-estimate) |
| IW.0.3 | HSN RawSeries Cluster Dextrin, unflavoured pure HBCD; 25g | **50ml** | Manufacturer panel: approximately 25g per scoop. `1scoop (50ml)`. [Panel](https://www.hsnstore.at/marken/raw-series/cluster-dextrin-hochverzweigtes-zyklisches-dextrin-pulver) |
| A.0.2 | HSN RawSeries Essential Amino Acids, Unflavored, 1kg; **15g** | **25ml** | Exact manufacturer's full serving. `1scoop (25ml)`. [Label](https://www.hsnstore.com/marcas/raw-series/aminoacidos-esenciales-eaa-s-en-polvo-1kg-sin-sabor) |

## Estimation method and limitations

Powder **bulk density** includes the spaces between particles and depends on how they pack. Solid/crystal density does not describe the volume occupied by loose powder. [USP bulk-density definition](https://doi.usp.org/USPNF/USPNF_M99375_03_01.html)

For blends, the starting calculation is `V ≈ sum(ingredient mass / ingredient bulk-density proxy)`. This assumes additive bulk volumes. Real mixtures can pack differently because small particles fill spaces between larger ones; particle size, moisture and settling also matter. Suppliers cited below are comparison sources, not established suppliers of these finished products. Residual-blend densities and packing multipliers are identified as assumptions.

The models principally estimate the volume occupied by a label-equivalent mass. Interpreting that as a physical scoop capacity assumes level or near-level filling. KFD explicitly specifies a level creatine scoop; the current BULK page also describes a level scoop. The checked MicroVitamin+, Collagen and ALLHydrate material does not establish that convention. A heaped serving can occupy more powder volume than the scoop bowl's capacity. The Collagen sensitivity includes an explicit fill factor; the other broad ranges do not guarantee coverage of every possible fill convention.

The rounded values in README deliberately avoid presenting model decimals as measured dimensions. Confidence descriptions are qualitative judgments about the evidence, not calculated probabilities.

## Product-specific findings

### HSN: exact products and serving panels

The WPI source is the selected unflavoured RawSeries isolate in the 2kg pack. A scoop value for Evowhey concentrate or flavoured Evolate is not needed to establish it. Cluster Dextrin evidence refers to pure RawSeries HBCD, not flavoured EvoDextrin or a recovery blend.

For **EAA**, the review changes the scheduled powder dose from 10g to **15g — 1scoop (25ml)**. The exact manufacturer's full-serving panel supplies 4.71g Leucine, 2.526g Lysine base, 1.686g each Isoleucine and Valine, 1.551g Threonine, 765mg Histidine base and 421.5mg each Methionine, Phenylalanine and Tryptophan. These sum to 14.1885g amino-acid bases, displayed as ~14.189g. Lysine/Histidine hydrochloride masses are not added again. The [official accessory table](https://www.hsnstore.eu/brands/hsn-accessories/scoop-hsn-25cc) distinguishes the selected RawSeries EAA's 25ml scoop from **EvoEAA's 10ml scoop**.

For **EvoBomb**, the dedicated use instructions and serving panels agree on 2x15ml per 20g. Some generic narrative text says one scoop, including on the [Lemon page](https://www.hsnstore.eu/brands/sport-series/evobomb-500g-lemon); it conflicts with the more specific panels. The exact Lemon dynamic nutrient panel was not exposed in retrieval. The official 15ml product-to-scoop mapping and [tasting-pack directions covering Lemon](https://www.hsnstore.pl/marki/hsn-packs/evobomb-zestaw-degustacyjny) corroborate the selected annotation. No flavour-dependent ingredient changes are made here.

Some HSN pages omit their dynamic nutrition fields from a normal text rendering while search retrieval of the same official URL exposes the dose panel. The linked manufacturer panels, exact product identity and corroborating scoop table provide the evidence.

The current [HSN scoop policy](https://www.hsnstore.eu/hsn-scoops) distinguishes powdered foods/proteins, which no longer come with a free scoop, from eligible powdered supplements for which a scoop can be selected at ordering. These capacities therefore mean **manufacturer-specified**, not necessarily **included**.


### KFD collagen estimate

**Working estimate: ~10ml per original scoop; broad sensitivity ~5–15ml.** Four scoops therefore correspond to an estimated combined nominal volume of ~40ml, with a broad ~20–60ml scenario range. Repeating the same scoop four times does not reduce uncertainty in its capacity.

The [KFD product](https://sklep.kfd.pl/kfd-ultra-pure-joint-collagen-300-g-p-8440.html) identifies FORTIGEL collagen and specifies 5g per 1.5scoops. The recovered [manufacturer sheet](https://storage.googleapis.com/allegro-offer-attachments/7833abb2a7816a0f7ee37c35cdbc30b2d04041b0abb74e56f88a960edbdf4719), EAN **5905255800854**, confirms that ratio. Thus one nominal scoop represents `5 / 1.5 = 3.333g`, and the retained four-scoop target represents `4 x 5 / 1.5 = ~13.33g`.

The [GELITA FORTIGEL B specification, version 6, May 2018][fortigel-spec] gives an approximate bulk density of **300g/L = 0.30g/ml** for its bovine agglomerated powder. At level fill, `3.333 / 0.30 = 11.11ml`. This supports a coarse working annotation of **~10ml**, not an exact 11.11ml moulded scoop.

KFD does not identify the FORTIGEL grade in the checked sheet. [GELITA's ST discussion](https://www.gelita.com/en/knowledge/blog/benefits-smart-collagen-peptides) explains that processing can increase bulk density. Therefore the 0.30g/ml FORTIGEL B figure is an ingredient-family proxy, not proof of KFD's finished-product density.

The broad sensitivity uses an **analyst-selected** density bracket of 0.25–0.50g/ml and fill factor `f = 0.90–1.30`, where `f = powder volume / brimful scoop capacity`. These are scenario assumptions, not KFD specifications. With `capacity = 3.333 / (density x f)`, the endpoints are **5.13–14.81ml**, reported as **~5–15ml**. For comparison, a level-only 0.25–0.40g/ml scenario gives 8.33–13.33ml.

The exact count remains **4scoops**, without an approximation marker. Neither the working ~10ml nor the calculated ~13.33g authorizes replacing that target with four arbitrary spoons or a new gram dose.

### KFD creatine estimate

**Working estimate: ~10ml per level scoop; analogue range ~7–12ml.** This has stronger direct support than the other estimates, but the current supplied scoop is not manufacturer-confirmed.

The [KFD page](https://sklep.kfd.pl/kfd-premium-creatine-500-g-kreatyna-monohydrat-p-4139.html) uses 5g per level scoop for ordinary variants; raspberry-jelly instructions differ. The [natural-creatine manufacturer sheet](https://storage.googleapis.com/allegro-offer-attachments/25f87b809968df56a31a8deacaa859bf33b05ff8e97fa41cee6b5bfc6daae79c), EAN **5901947663547**, confirms 5g per level scoop and 4999mg monohydrate per serving, without ml/cc capacity. The protocol retains the pure-monohydrate interpretation, not an arbitrary flavoured mixture.

Two separate purchaser discussions from 2020 report **10ml markings on KFD creatine scoops**: [January report](https://wykop.pl/wpis/46914781/kreatyna-kfd-mikrokoksy-czy-miarka-w-kreatynie-kfd) and [April report](https://wykop.pl/wpis/49107499/czy-w-kreatynie-z-kfd-w-opakowaniu-jest-dolaczona-). They are historical firsthand observations, not a current SKU/lot specification. Their usefulness here is as supporting evidence for an explicitly estimated number.

A loose-bulk-density cross-check gives:

| Comparable creatine source | Published loose bulk density or portion | Calculated volume for 5g |
| --- | --- | ---: |
| [Yurun Chemical](https://www.yurunchemical.com/products_details/201.html) | 475g/L = 0.475g/ml | 10.53ml |
| [HCS Chemical](https://hcschem.com/en/products/creatine-monohydrate/) | 488g/L = 0.488g/ml | 10.25ml |
| [Foodcom specification](https://foodcom.pl/wp-content/uploads/2023/09/Foodcom-CM_1_CHE_E1.1.pdf) | Minimum 430g/L = 0.43g/ml | 11.63ml at that minimum |
| [HSN 200-mesh monohydrate](https://www.hsnstore.eu/brands/raw-series/creatine-monohydrate-powder-200-mesh-1kg) | 3.4g per half of a 10ml scoop, approximately 0.68g/ml | 7.35ml |

The comparison bracket **0.43–0.68g/ml** implies **7.35–11.63ml**, rounded outward to **~7–12ml**. Different milling grades explain why another brand's scoop is not a direct substitute. Tapped-density values are excluded from this loose-powder calculation.

Both complete KFD manufacturer sheets were recovered through the [official KFD Allegro store](https://allegro.pl/uzytkownik/SMA-KFD), rendered and visually checked. Their batch fields are blank templates and neither gives capacity. The [KFD accessory scoop set](https://sklep.kfd.pl/kfd-komplet-miarek-p-6803.html) also does not establish which scoop accompanies either product.

### MicroVitamin estimate

**Working estimate: ~60ml for the 26g / approximately one-scoop serving. Broad additive-model sensitivity: ~40–100ml; a narrower common-density scenario gives ~45–80ml.** Confidence in the physical moulded scoop size is low.

The [exact Unflavored v8 variant](https://microvitamin.com/products/microvitamin-plus?variant=50000745464093), SKU/barcode **00199284018150**, maps to the [official facts image](https://cdn.shopify.com/s/files/1/0736/2907/3693/files/MixedBerryv8UNFLAVORED-Back2.webp?v=1778185196). Despite the filename's “MixedBerry” text, the image and variant mapping identify Unflavored. It declares 26g as approximately one scoop, including 12.5g Collagen, 5g Creatine and 2.5g Psyllium powder. Those three ingredients account for 20g; the residual is 6g.

The calculation uses manufacturers' household-measure portions for comparable single-ingredient powders, with 15ml tablespoons and 5ml teaspoons under the [metric measuring convention](https://www.nist.gov/pml/owm/metric-si/metric-kitchen/metric-kitchen-cooking-measurement-equivalencies):

| Component in the 26g serving | Central comparison/assumption | Model volume |
| --- | --- | ---: |
| Collagen peptides 12.5g | [Vital Proteins UK](https://www.vitalproteins.co.uk/collagen-peptides-uk.html): approximately 20g in four level tablespoons; 0.333g/ml | 37.50ml |
| Creatine monohydrate 5g | [NOW Foods](https://www.nowfoods.com/products/sports-nutrition/creatine-monohydrate-powder): approximately 5g in 1.5 level teaspoons; 0.667g/ml | 7.50ml |
| Psyllium husk powder 2.5g | [NOW Foods powder](https://www.nowfoods.com/products/supplements/psyllium-husk-powder): 9g per level tablespoon; 0.600g/ml | 4.17ml |
| Remaining blend 6g | **Assumed** effective bulk density 0.600g/ml | 10.00ml |
| **Total** | Additive bulk-volume model | **59.17ml → ~60ml** |

The residual includes the other ingredients, salts and carriers. Keeping it as one mass balance avoids double-counting elemental minerals, their salts and taurine already within magnesium taurate. No extra 3g of free Glycine is added: the exact v8 label does not declare that ingredient separately, and collagen's amino acids are already included in its 12.5g.

The residual-density assumption is informed by, but not identified with, [BulkSupplements TMG](https://www.bulksupplements.com/products/betaine-anhydrous-trimethylglycine-tmg-powder) at approximately 1.5g per half teaspoon (~0.60g/ml), [NOW Taurine](https://www.nowfoods.com/products/supplements/taurine-powder) at 0.9g per quarter level teaspoon (~0.72g/ml), and [Total Ingredients magnesium taurate](https://total-ingredients.com/products/magnesium-taurate) at 0.30–0.60g/ml.

For a reproducible sensitivity check, use the following **proxy brackets**, not MicroVitamin material specifications:

| Component | Density bracket used | Evidence informing the bracket |
| --- | ---: | --- |
| Collagen | 0.20–0.50g/ml | [Bovine collagen offer/CoA packet](https://solvent-systems.com/pdf/OfferPacketBovineCollagenPeptide.pdf): free-flow specification 0.20–0.60g/ml, example lots around 0.41–0.42; [Foodcom](https://fdcm.eu/wp-content/uploads/2025/12/bovine-collagen-powder.pdf): 0.30–0.50g/ml. The model bracket is selected within these examples, not exhaustive. |
| Creatine | 0.40–0.667g/ml | [Foodcom 200-mesh specification](https://foodcom.pl/wp-content/uploads/2023/09/Creatine-Monohydrate-200-mesh.pdf): minimum 0.40g/ml; NOW household-measure proxy above supplies the high endpoint. |
| Psyllium powder | 0.30–0.60g/ml | [Agroni powder grades](https://www.agroniinternational.com/products/psyllium-husk-powder.html): 0.30–0.50g/ml; NOW powder above supplies the high endpoint. Hydrated swelling volume is excluded. |
| Residual | 0.40–0.80g/ml | Analyst-selected bracket around the 0.60g/ml central assumption. |

Putting all densities at their high endpoints gives **44.17ml**; putting them at their low endpoints gives **98.33ml**. Round this to **~40–100ml**. If collagen is limited to the commonly published 0.30–0.50g/ml bracket, the upper result becomes **77.50ml**, giving the narrower **~45–80ml** scenario. A separate midpoint-density calculation (0.40, 0.55, 0.45 and 0.60g/ml) gives **55.90ml**, consistent with the rounded central scale.

Mixture packing remains unmeasured. For illustration, an assumed 20% reduction of the central additive volume would give 47.33ml; that is sensitivity, not a measured correction. The model therefore does not distinguish confidently between, for example, 50ml, 60ml or 70ml moulded scoops.

The prior audit visually checked all 13 official gallery assets and both pages of the [original Unflavored v8 CoA](https://cdn.shopify.com/s/files/1/0736/2907/3693/files/coa-microvitamin-plus-unflavoured-v8.pdf), which confirms 26000mg per serving, product 20562, lot 2512065. The gallery, CoA and [FAQ](https://microvitamin.com/pages/microvitamin-plus-faq) supplied no capacity, finished-blend density or readable scoop marking. Preparation water of 300–500ml is not scoop volume. The estimate retains the label's approximate scoop count and the existing 26g target.

### ALLHydrate estimate

**Working estimate: ~3ml per scoop; broad sensitivity ~2–4ml.** The central ingredient model gives 2.669ml. The physical scoop and its fill convention remain unconfirmed.

The exact Neutral 205g product, EAN **5903242584015**, is documented by [Aliness](https://aliness.pl/allhydrate-elektrolity-neutral-205-g-50-porcji/) and [ALLHydrate](https://allhydrate.pl/product/elektrolity-neutral/). Both give **4.1g per 1.5scoops**, so the retained one-scoop mass is `4.1 / 1.5 = 2.733...g`, rounded to 2.73g.

The manufacturer table assigns 2.650g to salt, 0.858g to potassium citrate and 0.400g to magnesium citrate. These total 3.908g, or 95.3% of the 4.1g serving. Model the remaining 0.192g as an unresolved calcium-salt balance.

| Component per 4.1g serving | Central loose bulk-density proxy | Calculated volume per 1.5scoops |
| --- | ---: | ---: |
| Salt 2.650g | 1.20g/ml | 2.208ml |
| Potassium citrate 0.858g | 0.95g/ml | 0.903ml |
| Magnesium citrate 0.400g | 0.70g/ml | 0.571ml |
| Calcium-salt balance 0.192g | **Assumed** 0.60g/ml | 0.320ml |
| **Total** | — | **4.003ml / 1.5 = 2.669ml per scoop → ~3ml** |

The density inputs come from comparison grades, not confirmed Medicaline suppliers:

| Component | Sensitivity bracket | Primary evidence |
| --- | ---: | --- |
| Salt | 0.975–1.30g/ml | [Qemetica food salt](https://qemeticasol.pl/uploads/media/default/0001/01/33dd89b21bd6015d42a3222fd7dc0c3d385cf080.pdf): 1.20±0.10kg/dm³; [Cargill Microsized Fine Salt](https://www.cargill.com/doc/1432109009073/salt-3905-microsized-product-information-sheet.pdf): 975–1075g/L. These differ from the product's unconfirmed Kłodawa rock-salt grade. |
| Potassium citrate | 0.95–1.20g/ml | [Merck](https://www.merckmillipore.com/AR/en/product/tri-Potassium-citrate-monohydrate,MDA_CHEM-104956): bulk density 950kg/m³; [Jungbunzlauer sheet](https://www.chimieplus.com/wp-content/uploads/import-data/files/ft_24112.pdf): 950–1200g/L. Crystal density is excluded. |
| Magnesium citrate | 0.50–0.70g/ml | [Lohmann DC100](https://www.lohmann-minerals.com/en-us/products/product-finder/trimagnesium-dicitrate-anhydrous-dc-100/): bulk density ~700g/L; [Lab Alley CoA](https://www.laballey.com/attachment/magnesium-citrate-usp-fcc-grade_COA_7215_5001471-13-1.pdf.pdf?product=43786): 0.50–0.70g/ml specification, 0.60g/ml result. No tapped-density endpoint is used. |
| Calcium-salt balance | 0.20–1.10g/ml | [PCCA calcium lactate](https://www.pccarx.com/Documents/msds_pdf/30-1582.pdf?d=638993820571314340): 600–800kg/m³; [Merck calcium phosphate](https://www.merckmillipore.com/INTL/en/product/Calcium-phosphate,MDA_CHEM-102143): 0.20–0.40g/ml; [Morgan monocalcium phosphate](https://morgan.com.eg/datasheet.aspx?id=347): 1.10g/cc. The precise salt split is unknown. |

The calcium/phosphorus panel does not close as a reliable recipe: it lists 122mg calcium lactate alongside 120mg calcium; the named ingredient masses leave only 70mg after that lactate while phosphorus is listed as 105mg. The 70mg remainder is therefore **not** treated as a verified phosphate mass. Using a broad residual prevents inventing a corrected formula. This is a limitation of the volume model; no existing protocol nutrient amount is changed.

Using all high-density endpoints gives **2.333ml per scoop**; all low-density endpoints give **3.587ml**. Apply an **assumed** blend-packing multiplier of 0.90–1.10 around additivity: **2.100–3.946ml**, rounded to **~2–4ml**. This ±10% is an explicit sensitivity choice, not a measured property or universal packing rule. Both 2.5ml and 3ml commercial scoops fit the estimated scale.

The prior image audit covered the official [2025](https://aliness.pl/wp-content/uploads/2025/09/961.jpg) and [2026](https://aliness.pl/wp-content/uploads/2026/01/ele_neutral-kopia.jpg) attachments, brand media and exact-product retailer galleries. These showed closed tubs without a readable scoop marking. A litre of mixing water, a 205ml catalogue field for a 205g tub and other same-brand liquid measures do not establish this scoop's volume. The Diet summary, IW.0.2 entry and sauna +2.73g addition all use the same ~3ml estimate.

### Psyllium: a measuring spoon, not a branded scoop

GymBeam's [Polish instructions](https://gymbeam.pl/psyllium-husks-gymbeam.html) and [English instructions](https://gymbeam.com/psyllium-husks-gymbeam.html?tab=detail) agree on **5g per 2tsp**. Scaling this published mass/count relationship gives `7.5 / 5 x 2 = 3tsp`. With the [metric cooking convention](https://www.nist.gov/pml/owm/metric-si/metric-kitchen/metric-kitchen-cooking-measurement-equivalencies), three 5ml teaspoons occupy one 15ml tablespoon. The manufacturer does not specify a level/heaped convention, so the active entry is **`7.5g — ~1tbsp (15ml measuring spoon)`**. The 7.5g remains a weighed target; this does not establish an exact 7.5g-per-15ml density or a supplied GymBeam scoop.


## Retired scoop entry

**Transparent Labs BULK “White Cherry”: estimated ~35ml per scoop; broad model ~25–50ml.** This is a proxy based on the **current 20.6g formula**, not verification of the historical tub. The product remains in Removed.

The [current White Cherry variant 44248689082461](https://www.transparentlabs.com/products/bulk-preworkout?variant=44248689082461), SKU **TPL001122**, barcode **874659003336**, was matched through the [official public product data](https://www.transparentlabs.com/products/bulk-preworkout.js). Both the [facts panel](https://cdn.shopify.com/s/files/1/0866/7664/files/Bulk_White_Cherry_SFP_1.png?v=1773067066) and [second White Cherry graphic](https://cdn.shopify.com/s/files/1/0866/7664/files/02_white_cherry_92f38de7-126d-4f9d-8ae3-cbf51948e041.jpg?v=1782244641) specify **1scoop = 20.6g**. Neither supplies ml/cc. Another flavour's serving mass is not substituted.

The five major ingredients account for 16.8g; the residual is 3.8g:

| Component | Central bulk-density proxy | Calculated volume |
| --- | --- | ---: |
| Citrulline Malate 2:1, 8g | [HSN](https://www.hsnstore.at/en/brands/raw-series/citrulline-malate-powder): 5g per 10ml; 0.50g/ml | 16.00ml |
| Beta-Alanine 4g | [HSN](https://www.hsnstore.at/en/brands/raw-series/beta-alanine-powder): 2g per half of a 5ml scoop; 0.80g/ml | 5.00ml |
| Betaine 2.5g | [Health Sources specification](https://v4.cecdn.yun300.cn/100001_1911185238%2F090009%20Specification%20of%20Betaine%20Anhydrous.pdf): bulk density 0.60–0.80g/ml; assumed midpoint 0.70g/ml | 3.57ml |
| Taurine 1.3g | [HSN](https://www.hsnstore.at/en/brands/raw-series/l-taurine-powder-1kg): 1g per two 0.5ml scoops; 1.00g/ml | 1.30ml |
| Tyrosine 1g | [HSN](https://www.hsnstore.pl/en/brands/raw-series/l-tyrosine-powder): 1g per half of a 5ml scoop; 0.40g/ml | 2.50ml |
| Residual blend 3.8g | **Assumed** 0.60g/ml, including remaining actives, mineral compounds, flavours and excipients | 6.33ml |
| **Total** | Additive model | **34.70ml → ~35ml** |

The betaine comparison is not established as the specification of the formula's branded BetaPure ingredient. A [second betaine specification](https://gojirafc.com/wp-content/uploads/2020/05/Betaine-Anhydrous.pdf) gives loose density 0.45–0.55g/ml separately from tapped density, supporting the need for a broader grade sensitivity.

For reproducibility, the **analyst-selected** density brackets in g/ml are: Citrulline Malate 0.45–0.65, Beta-Alanine 0.70–0.85, Betaine 0.45–0.80, Taurine 0.70–1.00, Tyrosine 0.35–0.50 and residual 0.40–0.80. These brackets probe plausible departures from the proxies; they are not supplier-certified bounds for BULK. An additional **assumed** blend-packing multiplier of 0.85–1.15 gives **23.96–49.75ml**, coarsely reported as **~25–50ml**.

The current manufacturer page describes a level scoop. The estimate does not establish the historical serving's formula, mass or moulded scoop capacity. It must not be used to reconstruct a stimulant serving by volume; any replacement measure needs calibration to the matching product's labelled powder mass.

## Replacing an estimate with a measurement

1. Match the original scoop to its product, flavour and tub/lot. A readable moulded ml/cc marking or manufacturer specification can replace the estimate with a documented capacity.
2. If unmarked, measure the actual scoop's brimful water volume with a graduated measure; repeat and record the method. Dry it completely before returning it to powder. This measures bowl capacity independently of powder density.
3. Check powder mass with the actual fill convention. For Collagen, weigh four original scoops to calibrate an equivalent replacement without redefining the chosen count.
4. Record the product/lot, source or measurement and date. Distinguish **manufacturer-specified**, **directly measured** and **estimated** values.

## Scope and verification

This follow-up replaces every missing-volume annotation with a numerical estimate, including duplicate Diet mentions, the ALLHydrate sauna addition and retired BULK. The ingredient calculations and uncertainty ranges are reproducible above; central and endpoint arithmetic received independent review. No manufacturer contact or physical scoop measurement was performed.

The earlier review's authorized doses remain **EAA 15g — 1scoop (25ml)** and **Collagen exactly 4scoops (~13.33g)**. Its reconciled amino-acid quantities, meal estimates, daily totals, Diet rotations and replacement notes are retained: After Workout 176kcal, Before Workout ~120kcal and the reference day ~2,417kcal with ~195.8g dietary Protein, including ~25.8g Collagen. The existing EAA allowance remains 60kcal. This estimation follow-up changes no powder doses, nutrient totals, timing, product/BJ links or physical pillbox entries.

[fortigel-spec]: https://www.dkshdiscover.com/medias/FORTIGEL-B-PD-Version-6-05-2018.pdf?attachment=true&context=bWFzdGVyfGJhY2tvZmZpY2VleGNlbGltcG9ydHw0ODkwNTl8YXBwbGljYXRpb24vcGRmfGFHTXpMMmd3TWk4NU1ESXhPREUxTVRZd09EWXlMMFpQVWxSSlIwVk1JRUpmVUVRZ0xTQldaWEp6YVc5dUlEWWdMU0F3TlMweU1ERTRMbkJrWmd8NzM0ZThiNjFlOGU0MjY0ZDAzOWQ0MTcyOWE1NDFhNmY3NWVlNGU2ZWI2YmFhNWZlMDIxOThhNjY3MGI4MWE4Mg
