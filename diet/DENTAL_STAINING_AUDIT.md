# Dental-staining audit for PR #26

Reviewed: **2026-11-07 (Europe/Warsaw)**
Protocol baseline: [main `f9b6b71`](https://github.com/PawelTroka/health-protocol/commit/f9b6b71e4221655a037df03fed44f98a101b4edf)
Original proposal: [PR #26, `99dc7b1`](https://github.com/PawelTroka/health-protocol/pull/26)
Operational guidance: [README dental-staining Note](../README.md#dental-staining)

## Decision

Replace the original tooth symbol with **🟡**, a yellow **staining precaution**. Retain **9 food/drink rows and the Chlorhexidine row**. Remove the proposed badges from **Strawberries, Purple Sweet Potatoes at Lunch and Dinner, Purple Carrots and mild Kimchi**.

The badge means that an established staining-source category or relevant dental-material evidence warrants a simple contact reminder. It does **not** mean that the listed serving is proven to produce a visible stain, that all marked items carry equal risk, or that the food should be avoided. Yellow is the visual cue, not a prediction of the stain's colour. An unmarked item is not certified stain-free.

**Chlorhexidine and Tea deserve the clearest attention.** The fruit flags are increasingly indirect, and the culinary-spice flags are laboratory-only. Saffron 30mg is a particularly low-priority precaution at the written occasional serving. These distinctions are part of the marker's definition, not optional fine print.

## How the evidence was assessed

This is a targeted literature and formulation audit, not a registered systematic review. It rechecked the five papers cited in the original PR, searched PubMed/PMC and primary journal sources for corroborating and contrary findings, and checked the current product formulations. Searches included the individual foods with staining, discoloration, enamel, composite resin, plaque disclosure and whitening, including available 2025–2026 studies. Official dental/medicine guidance informed practical care. Manufacturer pages establish formulation and product instructions; they do not establish clinical staining outcomes.

For each assignment, the review separated:

- **Human clinical evidence** from extracted teeth, resin discs, hydroxyapatite discs and patents.
- **Natural teeth** from composite bonding and other restorative materials.
- **The listed serving/form** from juice, concentrated extract, isolated pigment or prolonged immersion.
- **Colour change** from actual pigment deposition and from acid erosion.
- **A difference from baseline** from a meaningful difference against Water or artificial Saliva.

The ADA recognizes Tea and dark fruits as extrinsic stain-source categories, but this does not quantify a particular berry serving or rank cultivars. [ADA overview][ada]

A positive laboratory finding can justify a modest precaution, especially for bonding. It cannot establish the chance of visible staining in a person. Many experiments continuously immerse samples for days or weeks; their proposed conversions to months or years of consumption are not used here as clinical predictions. A measurable ΔE colour difference also does not identify its mechanism. Different colour metrics and study-specific thresholds must not be compared as if they form one universal severity scale.

The retained fruit/spice badges are editorial precautions with explicitly limited confidence. The review did not impose a requirement for a clinical trial of every food, which would remove nearly all food-level annotations. Conversely, colour alone, concentrated plaque dyes, or a chemically different extract were not enough.

## Audit of every original food/drink assignment

| Original row and actual form | Updated decision | Evidence and applicability |
| --- | --- | --- |
| Matcha 2g in Latte | **Keep 🟡** | Recognized Tea category plus a direct Matcha/composite experiment. The exact Latte, Milk and ordinary drinking exposure remain untested. [M1][matcha] |
| Fresh Blueberries 150g | **Keep 🟡** | Dark-fruit category; Blueberry juice discoloured composite in a controlled experiment. Whole fruit remains an extrapolation. [F1][blueberry] |
| Frozen Wild Bilberries 100g | **Keep 🟡** | Dark-fruit category precaution. No matched clinical trial establishes the risk of this species/portion or superiority/inferiority to Blueberries. [ADA][ada] |
| Frozen Blackcurrants 100g | **Keep 🟡** | Dark-fruit category precaution. Pigment content and beverage acidity do not provide a quantified staining estimate. [ADA][ada] |
| Fresh Strawberries 150g | **Remove badge** | Retrieved artificial strawberry-drink studies have limited and mixed relevance to fresh fruit. One controlled study found no significant difference between immersion media. This does not prove fresh Strawberries cannot stain. [F5][strawberry] [F6][strawberry2] |
| Fresh Raspberries 100g | **Keep 🟡; lower confidence** | A 2026 Raspberry-juice experiment supports composite staining potential. Juice composition/pH and ordinary whole-fruit exposure were not established. [F4][raspberry] |
| Pomegranate arils 130g | **Keep 🟡; indirect** | Pomegranate-juice experiments support composite staining potential. Twelve days of immersion are not equivalent to eating arils. [F2][pomegranate] |
| Frozen Tart Cherries 100g | **Keep 🟡; indirect** | Sour-Cherry juice produced material-dependent colour changes in a laboratory experiment. The study does not establish severe staining from whole Cherries. [F3][cherry] |
| Steamed Purple Sweet Potatoes 100g, Lunch | **Remove badge** | Concentrated Purple-Sweet-Potato extract has been used to reveal plaque. That endpoint does not establish persistent tooth/bonding stains after eating cooked potatoes. [V1][potato] |
| Steamed Purple Sweet Potatoes 100g, Dinner | **Remove badge** | Same food/form and decision as Lunch. [V1][potato] |
| Steamed Purple Carrots 100g | **Remove badge** | A Purple-Carrot-extract plaque-disclosing patent is not a clinical food study. Generic Carrot juice cannot establish risk from this cultivar/preparation. [V2][carrot] [F3][cherry] |
| Sweet Paprika 1g | **Keep 🟡; laboratory-only** | Native-spice solution studies show composite discoloration potential, with material/finish-dependent effects. The ordinary culinary serving has no validated staining risk. [S1][paprika] [S3][spices2019] |
| Saffron Threads 30mg, occasional; steeped before blending | **Keep 🟡; laboratory-only, low priority** | The original 2018 study was negative against Water, but later studies were positive. Keeping a qualified precaution acknowledges both results; none establishes a visible stain from this small diluted serving. [S2][saffron2018] [S3][spices2019] [S4][saffron2025] |
| Old Friends onion-free vegan mild Kimchi 75g | **Remove badge** | Relevant Kimchi experiments exist, but involve other food liquids/stews and laboratory substrates. They do not establish this particular mild product/portion as a priority stain source. [K1][kimchi2014] [K2][kimchi2012] |

### What the original five citations actually support

**Blueberries — PMID 27814264 (2016).** Composite specimens spent 7 days in Blueberry juice, Acai juice or artificial Saliva. Blueberry produced substantially greater colour change than the control. This is useful hazard evidence for juice contacting composite, not a numerical risk estimate for fresh Blueberries 150g. [F1][blueberry]

**Pomegranate — PMID 28174359 (2017).** The study tested 175 discs from five composites in five liquids over 12 days. It supports material-dependent discoloration from Pomegranate juice. Its claimed equivalence to a year in the mouth is an accelerated-model assumption, not evidence about the protocol's arils. [F2][pomegranate]

**Tart Cherries — PMID 19262731 (2009).** Four composites were exposed to drinks for 24 hours. Sour-Cherry, Carrot and Lemon drinks produced smaller changes than Coffee/Wine in the reported comparisons. The appropriate conclusion is a modest, indirect precaution, not that Cherries are among the worst staining foods. [F3][cherry]

**Paprika — PMID 24320904 (2013).** Two composites and two finishing methods were exposed to 0.1% spice solutions for 24–168 hours. Effects were material-dependent and far smaller than Turmeric; some Paprika results overlapped control changes. The authors' general conclusion supports possible staining, but not a claim that every material/Paprika comparison exceeded Water. An independent 2019 experiment provides further support. [S1][paprika] [S3][spices2019]

**Saffron — PMID 29652015 (2018).** This is the clearest correction. After 72 hours, Saffron ΔE values were approximately **0.83 and 1.20**, versus **1.28 and 0.81** for Water. The full paper explicitly reports no statistically significant Saffron–Water difference. An abstract statement that all media changed colour cannot establish a meaningful staining effect when the control changed too. [S2 abstract][saffron2018] [S2 full paper, Table2 and Results][saffronfull]

### New evidence and the close calls

**Matcha has direct evidence.** A 2025 experiment tested three composites with Matcha prepared at 2g/100ml Water, using 7–28 days of continuous exposure. It supports retaining the marker, particularly for composite bonding. It does not establish that a daily Latte stains as much as Coffee in real life. [M1][matcha]

**Saffron is not a colour-only guess.** Positive 2019 and 2025 spice experiments counterbalance the negative 2018 result. The 2025 study used 0.1% spice preparations and 7-day immersion; its findings do not validate the much smaller, occasional 30mg serving. Keeping this as a low-priority bonding precaution is more consistent than retaining Paprika while ignoring Saffron's positive studies. [S3][spices2019] [S4][saffron2025]

**Raspberries remain a weak extrapolation.** The 2026 study used 150 discs, three composites and 7–30-day immersion. The exact Raspberry juice was poorly characterized. It supports a possible composite hazard, with less confidence in transfer to fresh fruit than a well-characterized replicated model would provide. The report's beverage ranking must not become a ranking of ordinary foods. [F4][raspberry]

**The Strawberry evidence does not justify a routine fresh-food badge.** The 2014 study used artificial KAPO drinks, not fresh berries, and found no significant difference between media. A separate positive 2018 artificial-drink experiment used prolonged exposure with limited formulation reporting. Neither supports a confident warning for the listed fresh serving. Removal means insufficiently applicable evidence, not a recommendation to use Strawberries to whiten teeth. [F5][strawberry] [F6][strawberry2]

**Plaque disclosure is a different endpoint.** Applying a concentrated dye to visible plaque can demonstrate its usefulness for locating plaque without demonstrating persistent discolouration of cleaned enamel or composite. That distinction explains the Purple-Potato and Purple-Carrot removals. [V1][potato] [V2][carrot]

**Kimchi is not unstudied.** A 2014 hydroxyapatite-disc experiment placed ordinary Kimchi in its lowest relative staining group while Kimchi stew ranked higher. A 2012 composite experiment included Kimchi liquid but highlighted other foods in its results. Neither establishes the selected mild product's everyday risk. The removal does not dismiss acidity or certify all Kimchi products stain-free. [K1][kimchi2014] [K2][kimchi2012]

## Current oral-contact products and potential omissions

| Current item | Decision | Reason and limit |
| --- | --- | --- |
| 0.2% Chlorhexidine/Curasept ADS DNA 220 | **Keep 🟡** | Human clinical evidence and official medicine information support staining of teeth/restorations. ADS aims to reduce, rather than eliminate, staining. [C1][chxtrial] [C2][curasept] [C3][chxlabel] |
| MicroVitamin+ Powder Unflavored | **Unmarked; assessed explicitly** | The manufacturer confirms natural carotenoid particles. These contact the mouth, so the intact-capsule exemption does not apply. Product colour alone is insufficient; no finished-product dental-staining study was identified. [P1][microvitamin] |
| EvoBomb 2.0 Lemon 20g | **Unmarked** | The retrieved Lemon ingredient panel has no colouring agent. It is not a Coffee beverage merely because its Caffeine originates from Coffee beans. No product-specific staining study or prepared-drink pH measurement was identified. Recheck a flavour change. [P2][evobomb] |
| Plain WPI/EAA/Collagen/Creatine, HBCD, ALLHydrate Neutral and Psyllium | **Unmarked** | Being a powder or drink does not itself justify a staining badge. No relevant evidence was identified for these current formulations. This is not proof of zero risk. |
| Intact swallowed Cocoa-Flavanol, Curcumin and other pigmented capsules/softgels | **Unmarked** | Their contents do not routinely bathe teeth like a drink. This exposure-based inference changes if capsules are opened, chewed or mixed into liquids. |
| Eludril Ortho | **Unmarked** | The official page's nonstaining claim concerns orthodontic components in a laboratory test. Polish pharmacy INCI lists identify O-cymen-5-ol/Fluorinol, without CHX/CPC; the official text retrieved did not expose full INCI. This composition check is not proof of stain-free enamel or bonding. [P3][eludril] [P4][eludrilinci] |
| Listerine Cool Mint Zero | **Unmarked; mixed laboratory findings acknowledged** | Current Polish alcohol-free variants use essential oils/Fluoride; the Intensywny variant lists CI42053 and Ekstra Łagodny lists no dye. Both lack CHX/CPC in their published lists. The protocol's purchased bottle should be matched to its own label. Older laboratory formulations cannot define its exact risk. [P5][listerine] [P6][listerineextra] |
| Ceylon Cinnamon 0.5g and Cloves 0.25g | **Unmarked for culinary use** | Relevant experiments used concentrated Cinnamon extracts or methanolic Cinnamon/Clove extracts in a CPP-ACP/Fluoride dental preparation. These are substantially different exposures. [E1][cinnamon] [E2][clove] |
| Other coloured whole foods, Nuts/Seeds, oils, greens, pulses, Orange Carrots/Sweet Potatoes, Tomatoes and Red Pepper | **Unmarked** | Pigments/polyphenols alone do not establish a priority staining source at the listed preparation and portion. No sufficiently applicable evidence emerged to add badges. |
| Possible future Iron therapy | **No active badge added** | Liquid Iron can stain teeth; an intact capsule or IV preparation is not the same oral exposure. Reassess if a liquid formulation is prescribed. [I1][iron] |

### Why the oral-product decisions are not blanket guarantees

Chlorhexidine has direct human evidence: a 60-person controlled trial found more staining with 0.12% and 0.2% rinses than placebo over 14 days. This supports the class warning, not a predicted incidence for one week of this exact ADS product. [C1][chxtrial]

Older **Listerine Zero** studies do show colour changes. A 2018 extracted-tooth study reported day 21 ΔE2.32 versus 1.55 for control, below its chosen clinical threshold. Another study of CAD-CAM materials found changes below clinical perceptibility. A 2020 enamel experiment reported larger changes with an older Brazilian formulation and distilled-water storage. These inconsistent, formulation/substrate-dependent findings are acknowledged; they do not justify treating current Listerine Zero as equivalent to Chlorhexidine or calling it stain-free. [L1][listerinelab] [L2][listerinecad] [L3][listerine2020]

For **Cinnamon/Cloves**, form matching matters. The Cinnamon experiment used 4%/12% extracts for 60–180 minutes. The Clove/Cinnamon work used methanolic extracts in a CPP-ACP/Fluoride dental preparation on artificially demineralized enamel. Such results cannot simply be transferred to small quantities of ground spice eaten in a meal. [E1][cinnamon] [E2][clove]

## Practical care supported by the audit

1. **Keep nutritious foods.** The intended action is to reduce unnecessary contact and maintain ordinary dental care, not to shrink the diet around weak laboratory findings.
2. **After marked food/drink, rinse with plain Water and avoid holding or swishing drinks.** This is a practical contact-reduction measure; a reliable percentage reduction in staining has not been established. The strongest official rinse guidance concerns acidic exposure. [G1][erosion]
3. **An optional straw may reduce contact.** A small clinical videofluoroscopy study measured contact with teeth, not long-term stain prevention. Position and drinking behaviour mattered. Use the wording “may reduce contact,” not “prevents stains.” [G2][straw]
4. **Acidity has a separate pathway.** An uncoloured drink may still be acidic. After acidic intake, follow the ADA advice to rinse and wait about 1 hour before brushing. Do not infer erosive potential from flavour name, colour or the absence of a staining badge. [G1][erosion] [G3][acid]
5. **Do not rinse away Chlorhexidine immediately with Water.** Spit it out and follow the actual product/dentist instructions. Generic US dosing must not replace the Curasept label. Tea/Coffee can contribute to CHX staining; the existing prescribed/product-directed course remains unchanged. [C2][curasept] [C3][chxlabel] [C4][chxuse]
6. **Do not assume Milk makes Matcha stain-free.** An extracted-tooth study found that dairy Milk/Casein reduced Tea staining; it did not test this Soy-Milk Matcha Latte or clinical bonding outcomes. [M2][milk]
7. **Whitening and bonding need distinct expectations.** Composite does not whiten predictably like natural teeth; persistent bonding discoloration should be assessed for suitable professional care. [ADA][ada]

The clinical literature also does **not** justify a universal strict white-food diet during bleaching. A 2025 synthesis of seven clinical studies found similar bleaching colour change with pigment exposure/unrestricted diets and a white diet, with moderate evidence certainty. That is a short-term bleaching-effectiveness finding, not proof against future staining. [W1][whitediet] A 2020 randomized trial also found no overall colour/whiteness-index difference, while one later lightness measure was worse with Coffee; the nuance is retained rather than declaring all pigment exposure harmless. [W2][whitetrial]

## Scope, limitations and future updates

This review changes markers and their supporting documentation. It does not change food portions, choices, Macros, supplement or medicine doses, schedules, product selections or physical pillbox contents.

There are no validated absolute risk estimates for the exact foods, combinations and restoration material in this protocol. The literature does not permit a reliable “most staining to least staining” ranking of all listed servings. A dental observation of repeated staining from a particular item can justify reassessment even when the general evidence is sparse.

Reassess when a drink flavour/formulation changes, a capsule is opened or chewed, liquid Iron is introduced, or the dentist identifies a particular material or surface condition as susceptible. Product labels and research may change; this audit records the evidence available on its review date.

## Sources

The links below identify original studies or official guidance/product information. Pharmacy listings are used only for the Eludril composition check. The Purple-Carrot patent is evidence of a proposed plaque-dye use, not clinical validation.

- **ADA:** [Whitening; extrinsic stains and restoration limitations][ada].
- **M1:** [Janson et al., 2025 — Matcha/composite immersion experiment][matcha].
- **M2:** [Lee et al., 2014 — Milk/Casein and Tea staining of extracted teeth][milk].
- **F1:** [Dias et al., 2016 — Blueberry/Acai juice and composite colour][blueberry].
- **F2:** [Baglar et al., 2017 — Pomegranate and other drinks on five composites][pomegranate].
- **F3:** [Topcu et al., 2009 — Sour-Cherry and other drinks on composites][cherry].
- **F4:** [Alyahya, 2026 — Raspberry juice and three composites][raspberry].
- **F5:** [Oliveira et al., 2014 — Artificial fruit drinks and nanofilled composite][strawberry].
- **F6:** [2018 artificial fruit-drink study][strawberry2].
- **S1:** [Yew et al., 2013 — Paprika/Turmeric/Tamarind and two composites][paprika].
- **S2:** [Usha et al., 2018 — spice experiment abstract][saffron2018]; [author-uploaded original full paper][saffronfull].
- **S3:** [Thaliyadeth et al., 2019 — native-spice solutions and direct/indirect composites][spices2019].
- **S4:** [Dabaghi Tabriz et al., 2025 — Saffron/Turmeric/Black Pepper experiment][saffron2025].
- **V1:** [Yenti et al. — Purple-Sweet-Potato-extract plaque disclosure][potato].
- **V2:** [Purple-Carrot-extract dental composition patent][carrot].
- **K1:** [2014 Korean-food hydroxyapatite-disc study][kimchi2014].
- **K2:** [2012 food liquids and composite study][kimchi2012].
- **C1:** [Najafi et al., 2012 — controlled human Chlorhexidine trial][chxtrial].
- **C2:** [Curasept ADS DNA 220 official formulation/instructions][curasept].
- **C3:** [Corsodyl 0.2% official SmPC; CHX class evidence][chxlabel].
- **C4:** [MedlinePlus — no immediate Water rinse after Chlorhexidine][chxuse].
- **P1:** [MicroVitamin+ official FAQ; carotenoid particles][microvitamin].
- **P2:** [HSN EvoBomb official Lemon formulation][evobomb].
- **P3/P4:** [Eludril Ortho official page][eludril]; [Polish pharmacy INCI][eludrilinci].
- **P5/P6:** [Polish Listerine Cool Mint Intensywny Zero][listerine]; [Ekstra Łagodny Zero][listerineextra].
- **L1:** [Atala et al., 2018 — extracted teeth and mouthrinses][listerinelab].
- **L2:** [Mouthrinses and CAD-CAM restorative materials][listerinecad].
- **L3:** [Favaro et al., 2020 — mouthrinses and human enamel][listerine2020].
- **E1:** [Anggono et al., 2018 — concentrated Cinnamon extract][cinnamon].
- **E2:** [Safy/Elgamily, 2019 — methanolic extracts in dental varnish][clove].
- **I1:** [NHS — liquid Ferrous Sulfate and tooth staining][iron].
- **G1/G2/G3:** [ADA erosion guidance][erosion]; [Edwards et al., 1998 contact study][straw]; [ADA brushing interval][acid].
- **W1/W2:** [2025 network meta-analysis of clinical bleaching studies][whitediet]; [Chen et al., 2020 randomized trial][whitetrial].

[ada]: https://www.ada.org/resources/ada-library/oral-health-topics/whitening
[matcha]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12263494/
[milk]: https://pubmed.ncbi.nlm.nih.gov/25040739/
[blueberry]: https://pubmed.ncbi.nlm.nih.gov/27814264/
[pomegranate]: https://pubmed.ncbi.nlm.nih.gov/28174359/
[cherry]: https://pmc.ncbi.nlm.nih.gov/articles/PMC2647959/
[raspberry]: https://jpmsonline.com/article/download/1078/
[strawberry]: https://www.scielo.br/j/rounesp/a/ZWLFgWKHYyLtKhCnnZ9gJNm/?lang=en
[strawberry2]: https://www.msjonline.org/index.php/ijrms/article/download/5620/4315/0
[paprika]: https://pubmed.ncbi.nlm.nih.gov/24320904/
[saffron2018]: https://pubmed.ncbi.nlm.nih.gov/29652015/
[saffronfull]: https://www.researchgate.net/publication/321575194_A_Comparative_Evaluation_of_the_Staining_Capacity_of_Microybrid_and_Nanohybrid_Resin_Based_Composite_to_Indian_Spices_and_Food_Colorants_-_An_In_vitro_Study
[spices2019]: https://pubmed.ncbi.nlm.nih.gov/31797832/
[saffron2025]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12366667/
[potato]: https://ojs.poltekkeskupang.ac.id/index.php/infokes/article/view/997
[carrot]: https://patents.google.com/patent/WO2012103264A1/en
[kimchi2014]: https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001952205
[kimchi2012]: https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001710341
[chxtrial]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3469897/
[curasept]: https://curasept.com/product/curasept-ads-dna-220-mouthwash/
[chxlabel]: https://www.medicines.org.uk/emc/product/529/smpc
[chxuse]: https://medlineplus.gov/druginfo/meds/a625015.html
[microvitamin]: https://microvitamin.com/pages/microvitamin-plus-faq
[evobomb]: https://www.hsnstore.eu/brands/sport-series/evobomb
[eludril]: https://www.pierrefabre-oralcare.com/pl-pl/p/eludril-ortho-plyn-do-plukania-jamy-ustnej-3577056025044-808759b4
[eludrilinci]: https://www.e-zikoapteka.pl/eludril-ortho-plyn-do-plukania-jamy-ustnej-500-ml.html
[listerine]: https://www.listerine.pl/p%C5%82yn-do-p%C5%82ukania/plyn-listerine-cool-mint-intensywny
[listerineextra]: https://www.listerine.pl/p%C5%82yn-do-p%C5%82ukania/pl%20yn-listerine-cool-mint-extra-lagodny
[listerinelab]: https://pubmed.ncbi.nlm.nih.gov/30106538/
[listerinecad]: https://pubmed.ncbi.nlm.nih.gov/31920055/
[listerine2020]: https://www.jstage.jst.go.jp/article/josnusd/62/1/62_18-0370/_article/-char/en
[cinnamon]: https://scholar.ui.ac.id/en/publications/effect-of-cinnamon-extract-solution-on-tooth-enamel-color/
[clove]: https://applications.emro.who.int/imemrf/86/Egypt-Dent-J-2019-65-3-2617-2623-eng.pdf
[iron]: https://www.nhs.uk/medicines/ferrous-sulfate/side-effects-of-ferrous-sulfate/
[erosion]: https://www.ada.org/resources/ada-library/oral-health-topics/dental-erosion
[straw]: https://pubmed.ncbi.nlm.nih.gov/9785633/
[acid]: https://www.mouthhealthy.org/all-topics-a-z/dietary-acids-and-your-teeth
[whitediet]: https://pubmed.ncbi.nlm.nih.gov/39557282/
[whitetrial]: https://pubmed.ncbi.nlm.nih.gov/32169479/
