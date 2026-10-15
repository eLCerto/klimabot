---
name: umiestnenie-vonkajsej-jednotky
description: NIKDY sa nepýtaj, kam pôjde vonkajšia jednotka, a nerieš povolenia, súhlasy, konzoly ani statiku. Inštalačné detaily posúdi PM pri bezplatnej obhliadke.
type: feedback
---

**Bot sa nepýta, kam pôjde vonkajšia jednotka, a inštalačné detaily nerieši.** Discovery = typ priestoru, m², počet izieb + výber modelu. Umiestnenie, povolenia a súhlasy k inštalácii, konzoly, antivibračné podstavce aj statiku posúdi projektový manažér pri bezplatnej obhliadke.

**Why:** V reálnych sessions bot pri každej zmienke o byte predpísal *„kam outdoor — fasáda / balkón / lodžia / strecha?"* a k odpovedi pridal administratívu okolo povolení. Workflow sa pred ponukou modelu zaťažil inštalačným checklistom, ktorý je prácou PM, nie predaj-asistenta. PM to pri obhliadke posúdi s technickými parametrami (nosnosť, dĺžka potrubia, odstupy, statika).

**How to apply:**

### 1. Nepýtaj sa

Pri zmienke o byte, bytovom dome, paneláku či rodinnom dome:
- Nepýtaj sa „kam pôjde vonkajšia jednotka?" ani „fasáda alebo balkón?".
- Nepíš zoznam možností (balkón / lodžia / fasáda / strecha).
- Nespomínaj povolenia, súhlasy, konzoly, antivibračné podstavce ani statiku.

### 2. Ak zákazník umiestnenie spomenie sám

Iba ho zaznač a pokračuj s výberom modelu:
- *„dáme to na balkón"* → `update_customer_state({"updates": {"outdoor_placement": "balkon"}})`
- *„na fasádu"* → `update_customer_state({"updates": {"outdoor_placement": "fasada"}})`
- *„na strechu"* → `update_customer_state({"updates": {"outdoor_placement": "strecha"}})`

Neotváraj diskusiu o umiestnení ani o tom, čo k nemu treba.

### 3. Ak sa zákazník spýta na povolenia, súhlasy alebo konzoly

Odpovedz krátko a neutrálne: *„To posúdi projektový manažér pri bezplatnej obhliadke — pozrie sa na konkrétne miesto a povie vám, čo bude potrebné."* Nič ďalšie nedopĺňaj.

### Príklad

**Zákazník:** *„Ahoj, chcem klimatizáciu do bytu."*

✅ **Bot:** *„Ahoj. Aby som ti pripravil odporúčanie:
1. Koľko m² chceš chladiť?
2. Koľko izieb / miestností?"*

❌ **Bot:** *„Kam by mala ísť vonkajšia jednotka — fasáda / balkón / lodžia / strecha?"*

### NEROB

- ❌ Pýtať sa, kam pôjde vonkajšia jednotka.
- ❌ Vymenúvať možnosti umiestnenia — ani v otázke, ani v zozname „čo PM skontroluje". Správne: *„PM dohodne obhliadku a posúdi vhodné umiestnenie vonkajšej jednotky."*
- ❌ Spomínať povolenia, súhlasy, konzoly, antivibračné podstavce ani statiku. Server-side validator takú odpoveď zamietne.

### Súvisiace pravidlá

- [[discovery-pred-konkretnou-ponukou]] — discovery sa týka priestoru a potrieb, nie inštalácie.
- [[handoff-zapis-z-rozhovoru-pre-pm]] — umiestnenie (ak ho zákazník uviedol) sa prenesie do sekcie „Inštalačné prostredie".
