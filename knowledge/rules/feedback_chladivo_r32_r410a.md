---
name: chladivo-r32-vs-r410a-preferuj-r32
description: Preferuj R32 (GWP 675); R410a (GWP 2088) iba kde nie je R32 alternatíva (Samsung HSP, Floor Standing, AHU). Upozorni na EU F-Gas budúce servisné náklady.
type: feedback
---

Klimatizácie používajú **R32** (moderné, nižší GWP) alebo **R410a** (staršie, vyšší GWP, postupne fázované). Preferuj R32 kde je to možné.

**Why:** EU F-Gas Regulation 2024/573 obmedzuje R410a (GWP 2088) kvôli vysokému dopadu. R32 má GWP 675 (3× menej). Od 2025 prísnejšie kvóty na výrobu R410a → vyššia cena servisu / dopĺňania. Zákazník s R410a v 2026 zaplatí viac za servis za 5–10 rokov.

**How to apply:**

### Toshiba — iba R32

- Všetky Toshiba RAS a RAV 2026/27 = R32. Pri Toshiba sa otázka R410a nerieši.

### Samsung — obe podľa modelu

**R32 (preferuj):**
- Všetky Samsung RAC (Single-Split): Première+/Première, Avant, Comfort, Cebu, Luzon, AR30/35
- Všetky Samsung FJM (Multi-Split AJ___TXJ)
- CAC R32 outdoor: AC026–140 RXADKG/NG
- CAC R32 HighEE: AC026–140 BXAPKG/NG
- AHU Kit MXD-K100XN1 (R32 verzia)

**R410a (iba ak chýba R32 alternatíva):**
- Samsung **HSP Duct AC200/250KNHPKH** (20–25 kW) — nie je R32
- Samsung **Floor Standing AC100/140BNPDKH** — iba R410a v cenníku 2026
- AHU Kit MXD-K100XN (R410a)

### Odporúčacia logika

1. **Rezidenčné (RAC, FJM)** → vždy R32.
2. **Menšie komerčné (CAC do 14 kW)** → preferuj R32 (RXAD/BXAP).
3. **Veľké komerčné 20+ kW** → R410a (HSP Duct, jediná voľba).
4. **Floor Standing** → Samsung má iba R410a; ak zákazník chce R32 stojanovú → **Toshiba RAV stojanová** (R32, 5–14 kW).

### Cenový rozdiel

Pri CAC 10 kW 1f outdoor majú AC100RXADKG (R32) a AC100BXPDKH (R410a) v cenníku porovnateľnú cenu (over oboma volaniami `quote`), ale **prevádzkové náklady R410a vyššie** (servis, dopĺňanie).

### Príklad

**Zákazník:** „Aký je rozdiel medzi R32 a R410a?"

**Bot:** „R32 je modernejšie chladivo s 3× nižším GWP (675 vs 2088). EU postupne obmedzuje R410a (F-Gas Regulation 2024/573), takže pri kúpe v 2026 je R32 lepšia dlhodobá voľba — nižšie servisné náklady. Pre rezidenčné použitie sú všetky moderné Toshiba a Samsung modely R32. R410a sa už používa len pri špecifických komerčných aplikáciách (HSP Duct 20–25 kW, niektoré Floor Standing). Odporúčam R32 kde je to možné."

**Zákazník:** „Stojanová klimatizácia 10 kW pre obchod."

**Bot:** „Stojanová 10 kW — dve možnosti:

**Samsung Floor Standing AC100BNPDKH** (R410a) — cena z `quote`. Pozor: R410a → vyššie budúce servisné náklady (EU regulácia).

**Toshiba RAV Stojanová DI 110** (R32) — cena z `quote`. Drahšia, ale R32 + detekcia únikov chladiva + dotykový ovládač v cene.

Pre dlhodobú investíciu (5+ rokov) odporúčam Toshiba RAV. Pre menší rozpočet Samsung (s upozornením na servisné náklady)."

### NEROB

- ❌ Predávať R410a bez upozornenia na EU F-Gas reguláciu.
- ❌ Zatajovať pred zákazníkom rozdiel R32 vs R410a — môže byť rozhodujúce.
- ❌ Riešiť horľavosť R32 (A2L) — to je práca inštalatéra (EN 378), nie chatbota.

### Súvisiace pravidlá

- [[komercne-priestory-cac-rav]] — pri serverovni/CAC preferuj R32 HighEE (rozšírený operatívny rozsah aj v zime).
- [[brand-specificke-funkcie-neplietat]] — chladivo nie je brand-specific termín, ale obmedzenia áno (Toshiba bez R410a v RAS/RAV).
