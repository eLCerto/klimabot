---
name: 3-fazove-vyhotovenie-kedy-treba
description: 3f vonkajšie jednotky iba ak má objekt 3f prípojku alebo výkon >9 kW. Inak 1f. Pri >9 kW alebo komerčnom dotaze overiť prípojku.
type: feedback
---

Klimatizácie majú **1f (220–240V/1+N)** alebo **3f (380–415V/3+N)** vyhotovenia. Rozdiel nie je vo výkone, ale v elektrickej zaťaženosti. **3f odporúčaj iba ak má objekt 3f prípojku a/alebo výkon >9 kW.**

**Why:** Rezidenčné objekty (byt/dom) majú často iba 1f. Odporúčanie 3f bez overenia = nečakané náklady na elektrikársky zásah (rekonfigurácia rozvádzača, ističe).

**How to apply:**

### Kedy 1f stačí (preferuj)

| Výkon | 1f vhodný |
|---|---|
| Do 7 kW | Vždy 1f |
| 7–9 kW | 1f stačí (SDI, DI 90/110) |
| 9–14 kW | 1f aj 3f existujú — záleží na inštalácii |
| Nad 14 kW | Spravidla iba 3f (DI/SDI 1601 nemajú 1f) |

### Dostupnosť podľa značky/radu

**Toshiba RAS — iba 1f:**
- Všetky Single-Split sety (SEIYA, SHORAI, HAORI, DAISEIKAI, Parapetná)
- Multi-Split outdoor 2M–5M (aj 5M34 = 1f)

**Toshiba RAV — obe:**
- DI CLASSIC: 1f do 13,0 kW; 3f 110/140/160
- DI: 1f do 14,0 kW; 3f 110/140/160
- SDI: 1f do 12,5 kW; 3f 110/140/160
- **DI BIG Single Fan: iba 3f** (19,0 a 22,5 kW)

**Samsung RAC, FJM — iba 1f:**
- RAC outdoor, FJM outdoor (AJ040–AJ100)

**Samsung CAC — obe:**
- AC___RXAD (R32): 1f (KG), 3f (NG) pre 100/120/140
- AC___BXAP (R32 HEE): 1f (KG), 3f (NG) pre 71/100/120/140
- AC100/140 BXPDKH (R410a Floor Standing): 1f / 3f
- **AC200/250 KXAPNH (R410a HSP, 20–25 kW): iba 3f**

### Discovery pri >9 kW alebo komerčnom dotaze

1. **Akú prípojku máte?** (1f 230V / 3f 400V)
2. **Hlavný istič?** (16/20/25/32A)
3. **Máte už 3f zariadenia?** (sporák, ohrievač, motor)

### Cenový rozdiel (Toshiba RAV príklad)

Pri porovnaní 1f a 3f variantu zavolaj `quote` pre každý zvlášť a uveď obe sumy. 3f nie je vždy drahšie.

**Pozor:** SDI 1f GP1101AT-E je drahší ako 3f variant kvôli rozšírenému rozsahu (-27 °C vs -20 °C). Pri komerčnej inštalácii s 3f bez nárokov na extreme cold môže byť 3f ekonomickejšie.

### Príklad

**Zákazník:** „Pre kanceláriu 100 m² aký set?"

**Bot:** „Pre 100 m² potrebujete cca 10 kW — existujú 1f aj 3f varianty. Pred odporúčaním:

1. Akú prípojku má kancelária? (1f 230V alebo 3f 400V)
2. Aký hlavný istič?

3f RAV-GM1102AT8W-E má menší prúdový odber (3× ~12 A) než 1f RAV-GM1102ATW-E (22,5 A); ceny oboch variantov pripravím cez `quote`. Pri 1f s 25A ističom môže byť napäté.

Pri novostavbe / rekonštrukcii s 3f prípojkou odporúčam 3f. Pri staršom byte/dome s 1f preferuj 1f."

### NEROB

- ❌ 3f set bez overenia 3f prípojky.
- ❌ Považovať 3f za vždy „lepšie" — cenovo ani inštalačne to nie je vždy výhoda.
- ❌ Pri 19+ kW (DI BIG) zabudnúť, že je iba 3f — upozorni.
- ❌ Pri Samsung AC200/250 (HSP, AHU) zabudnúť, že je iba 3f.

### Súvisiace pravidlá

- [[komercne-priestory-cac-rav]] — pri serverovni >9 kW prejdi na 3f, ak je prípojka.
- [[montaz-zaruka-servis]] — zmena z 1f na 3f = drahšia inštalácia (elektrikár).
