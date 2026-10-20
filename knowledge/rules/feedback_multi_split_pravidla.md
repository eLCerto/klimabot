---
name: multi-split-pravidla-a-obmedzenia
description: Multi-Split má obmedzenia (max 5 izieb, povolené kombinácie). Pred ponukou ZAVOLAJ `check_compatibility`.
type: feedback
---

Multi-Split (Toshiba RAS-#M, Samsung FJM AJ___TXJ) nie je univerzálne pripojiteľný. **Pred prezentáciou setu zavolaj `check_compatibility(outdoor_code, [indoor_codes])`** — overí počet jednotiek, súčet kapacít a typové obmedzenia.

**Why:** Ak zákazníkovi navrhneš 4 indoor na RAS-2M14 (max 2), pri inštalácii sa zistí že to nie je možné. Stratíme čas aj dôveru.

**How to apply:**

### Toshiba RAS Multi-Split

| Vonkajšia | Max izieb | Min/Max indoor |
|---|---|---|
| RAS-2M10G3AVG-E (3,3 kW) | 2 | 05–10 |
| RAS-2M14G3AVG-E (4,0 kW) | 2 | 07–13 |
| RAS-2M18G3AVG-E (5,2 kW) | 2 | 07–16 |
| RAS-3M18G3AVG-E (5,2 kW) | 3 | 07–18 |
| RAS-3M26G3AVG-E (7,5 kW) | 3 | 07–24 |
| RAS-4M27G3AVG-E (8,0 kW) | 4 | 07–24 |
| RAS-5M34G3AVG-E1 (10,0 kW) | 5 | 07–24 |

- **Veľkosť 05 (1,5 kW) je IBA Multi-Split** — nedá sa použiť ako Single-Split.
- **1 indoor na 1 outdoor = iba chladiaca prevádzka** (pre kúrenie min. 2 indoor).
- Indoor môžu byť rôzne typy (nástenná + kazeta + parapetná na 1 outdoor).
- Súčet menovitých výkonov indoor nesmie príliš prekročiť kapacitu outdoor.

### Samsung FJM Multi-Split

| Vonkajšia | Max izieb | Pravidlá |
|---|---|---|
| AJ040TXJ2KG (4,0 kW) | 2 | Console OK, bez 6,5 kW indoor, chladí od -5 °C |
| AJ050TXJ2KG (5,0 kW) | 2 | Console OK, bez 6,5 kW indoor, chladí od -5 °C |
| AJ052TXJ3KG (5,2 kW) | 3 | Console OK, bez 6,5 kW indoor, chladí od -10 °C |
| AJ068TXJ3KG (6,8 kW) | 3 | **Console NEPOVOLENÁ**, Mini 4-Way 5,2 OK |
| AJ080TXJ4KG (8,0 kW) | 4 | **Console NEPOVOLENÁ**, max 6,5 kW indoor |
| AJ100TXJ5KG (10,0 kW) | 5 | **Console NEPOVOLENÁ**, max 6,5 kW indoor |

- **Console (parapetná) iba pre AJ040/050/052** — pre väčšie nie!
- **Indoor 6,5 kW (24) iba pre AJ080/100** — nie pre 2M/3M.
- **Mini 4-Way 5,2 kW** od AJ068 hore (nie pre 2-room).
- **AJ040/050 chladia od -5 °C**, ostatné od -10 °C — pre studené regióny preferuj AJ052+.

### Discovery otázky

1. Koľko izieb celkovo? (1 = Single, 2–5 = Multi)
2. Veľkosti izieb v m²?
3. Typy indoor — všetko nástenné, alebo mix (nástenná + kazeta + parapetná)?
4. Povinné typy? („v jednej izbe MUSÍ byť kazeta")

### Porovnanie single vs. multi

Pri porovnaní 2× single-split a multi-split zavolaj `quote` **dvakrát** — každý variant celý v jednom volaní (dve rovnaké single-split sady = jedna položka s `qty: 2`). Ktorý variant vyjde lacnejšie a o koľko, povie `comparison_with_earlier_quotes` v druhej ponuke — smer („drahšie / lacnejšie") nikdy neodhaduj.

**Zákazník váha** („neviem, či multisplit alebo dve samostatné"): naceň oba varianty, porovnaj ich vecne a nech si vyberie. Výhody multi-splitu, ktoré môžeš povedať: **iba 1 vonkajšia jednotka** (estetika, menej vŕtania) a **jeden ovládací ekosystém**. Výhody samostatných setov: **nezávislosť** (porucha jednej nezastaví druhú). Tvrdenia o úspore energie či efektivite bez údajov z `compare_products` nepíš ([[schvalene-tvrdenia]]).

**Zákazník si vyberie podľa ceny** („beriem tú lacnejšiu"): zapíš variant, ktorý je podľa `comparison_with_earlier_quotes` lacnejší — aj keď je to 2× single-split.

**Ak si zákazník multi-split už vybral** (nie len spomenul ako otázku) — rešpektuj jeho voľbu a neponúkaj single-split ako náhradu.

**Veľkosť každej vnútornej jednotky podľa jej izby:** obývačke 38 m² nestačí 2,0 kW jednotka len preto, že súčet celej zostavy vyzerá dobre. Ak zákazník povie plochu jednotlivých izieb, každú vnútornú jednotku dimenzuj na tú izbu.

**Mix typov (Samsung):** 3 izby — 1× parapetná + 2× nástenná → AJ068 NIE je povolená s Console; musí byť AJ052 (max 3, Console OK) alebo Single-Split pre parapetnú izbu.

### Workflow pred ponukou multi-split setu

1. `lookup_product` s textom „<značka> multi-split <výkon v kW>“ vráti nástenné vnútorné jednotky tej veľkosti (`wifi_standard`) a vonkajšie (`outdoor_options`) — vonkajšiu vyber podľa počtu izieb. Na kódy nehľadaj cez `search_knowledge`.
2. Vnútorné jednotky vyber podľa veľkostí izieb (1 kW / 10 m²).
3. **Zavolaj `check_compatibility(outdoor_code, indoor_codes)`.**
4. Pri error/warning → uprav výber a znova check.
5. Až potom `quote` s vonkajšou + všetkými vnútornými jednotkami a prezentuj jeho cenu.

### NEROB

- ❌ 4 izby na RAS-2M (max 2).
- ❌ Console parapetná s AJ068+.
- ❌ Veľkosť 05 ako Single-Split (je iba Multi).
- ❌ Pri zákazníkovi, ktorý si multi-split vybral, odporučiť 2× single-split „lebo je lacnejší".
- ❌ Odporučiť multi-split „lebo je to default" alebo „lebo je úspornejší" zákazníkovi, ktorý chce najlacnejšie riešenie.
- ❌ Napísať, ktorý variant je drahší, bez `comparison_with_earlier_quotes`.
- ❌ **Prezentovať multi-split set bez `check_compatibility`.** Tabuľka v tomto pravidle nie je zdroj pravdy — tool je. KB sa môže zmeniť.

### Súvisiace pravidlá

- [[komercne-priestory-cac-rav]] — pre serverovňu NIKDY multi-split (zdieľaný okruh, žiadna redundancia).
- [[brand-specificke-funkcie-neplietat]] — Console vs Mini 4-Way vs Twin kit — rôzne značky, rôzne obmedzenia.
- [[dimenzovanie-kapacity]] — 1 kW / 10 m² platí aj pre indoor v Multi-Split.
