---
name: cena-dph-a-recyklacne-poplatky
description: Pri prvej citácii ceny uveď, že je bez DPH a recyklačných poplatkov. Sumu s DPH aj výšku poplatku ber z výstupu quote — nič neprepočítavaj.
type: feedback
---

Ceny v cenníkoch Toshiba (RAS, RAV) a Samsung sú **MOC bez DPH a recyklačných poplatkov**. Pri prvej zmienke ceny v konverzácii to povedz. Cenu s DPH (`unit_price_with_DPH_23pct_eur`, `total_with_DPH_23pct_eur`), samotnú DPH (`DPH_23pct_eur`) aj výšku recyklačného poplatku (`recycling_fee_per_unit`) vracia `quote` — sám nič nenásob.

**Why:** SK B2C zákazníci zvyčajne myslia cenu *s DPH* (to je cena, ktorú reálne zaplatia). Ak im odcitujem cenu bez DPH a oni ju berú ako konečnú, po zistení rozdielu sa cítia oklamaní. B2B zákazníka (firma) naopak zaujíma cena bez DPH kvôli odpočtu.

**How to apply:**
- Prvá citácia v konverzácii: *„SHORAI CURVE White 10 (2,5 kW) – set za **`unit_price_eur` € bez DPH a recyklačných poplatkov** (`unit_price_with_DPH_23pct_eur` € s DPH)."*
- Ďalšie citácie v tej istej konverzácii: stačí cena bez DPH (zákazník už pozná kontext).
- B2B (firma, IČO, fakturácia): preferuj cenu bez DPH.
- Recyklačný poplatok (HEEE), ak sa zákazník spýta: rozsah z `recycling_fee_per_unit` (za jednu klimatizáciu, presná suma pri objednávke).

**NEROB:**
- ❌ Uviesť cenu bez kontextu DPH.
- ❌ Označiť cenu bez DPH ako cenu s DPH.
- ❌ Násobiť × 1,23 alebo odhadovať poplatok — obe čísla sú vo výstupe `quote`.
