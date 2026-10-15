# Samsung Klimatizácie – Master Index (cenník 2026)

**Zdroj cien:** Cenník Samsung Chladenie 2026, 1. vydanie (© Samsung Electronics Air Conditioner Europe B.V.) – verejne dostupný cenník ([PDF](https://www.climaport.sk/wp-content/uploads/2026/06/Cennik-Samsung-Chladenie-2026.pdf))
**Zdroj features:** Samsung Residential Air Conditioners katalóg 2025 (EN), © Samsung Electronics
**Platnosť cien:** od 1.1.2026 · MOC bez DPH a recyklačných poplatkov · EUR
**Chladivo:** R32 (väčšina) / R410a (HSP Duct, Floor Standing AC100/140 BNPDKH, AHU 100/140/200/250)

---

## 0. Súbory v databáze

| Súbor | Obsah | Modely |
|---|---|---|
| [rac.json](rac.json) | Single-Split residential (RAC) | 9 rád, ~40 SKU setov |
| [fjm.json](fjm.json) | Multi-Split (FJM) – vonkajšie + vnútorné | 6 vonk. + 11 typov vnút. |
| [cac.json](cac.json) | Komerčný split (CAC) | 16 typov, ~80 indoor SKU + 22 outdoor |
| [accessories.json](accessories.json) | Ovládače, panely, BMS, refnety, AHU | ~50 položiek |
| [glossary.json](glossary.json) | EN↔SK synonymá, definície termínov, FAQ pre SK chatbota | ~100 termínov |

---

## 1. RAC – Rezidenčný Single-Split (chatbot bude predávať najmä toto)

| Rada | Tier | Trieda chl./vyk. | SEER (09) | SCOP (09) | Cena setu 09 (2,5 kW) | Hlavná výhoda |
|---|---|---|---|---|---|---|
| **AR30 WIFI** | Budget | A++ / A+ | 6,30 | 4,00 | **809 €** | Najlacnejší, len WiFi |
| **AR35 WIFI** | Entry | A++ / A+ | 6,30 | 4,00 | **809 €** | Identický s AR30, ale o čosi vyšší rad |
| **Luzon S2** | Entry | A++ / A+ | 6,70 | 4,00 | **990 €** | Najlacnejší so SmartThings AI |
| **Cebu S2** | Entry-Mid | A++ / A+ | 7,40 | 4,20 | **1 028 €** | Lepšia účinnosť + solárny ovládač |
| **WindFree Comfort S2** | Mid | A++ / A++ | 7,90 | 4,60 | **1 221 €** | **WindFree režim** (bez prievanu) |
| **WindFree Avant S2** | Mid-High | A+++ / A++ | 8,80 | 4,80 | **1 504 €** | A+++ + Tri-care filter |
| **WindFree Avant S2 Black** | Mid-High | A+++ / A++ | 8,80 | 4,80 | **1 531 €** | Čierne prevedenie Avant |
| **WindFree Première** | High | A+++ / A++ | 8,80 | 4,80 | **1 683 €** | 4-in-1 Filter + Freeze Wash |
| **WindFree Première+ White** | TOP | A+++ / A+++ | **9,70** | **5,10** | **1 845 €** | AI Motion Wings + radar |
| **WindFree Première+ Black** | TOP | A+++ / A+++ | 9,70 | 5,10 | **1 882 €** | Čierne TOP prevedenie |

**Konvencia kódov:**
- `AR70H_CAA*NEU` = WindFree Première+ (TOP, GRID design)
- `AR70H_C1A*NEU` = WindFree Première
- `AR70F_C1A*NEU` = WindFree Avant S2 (B=Black, W=White)
- `AR60F_C1AWNEU` = WindFree Comfort S2
- `AR50F_C1AHNEU` = Cebu S2
- `AR50F_C1BHNEU` = Luzon S2
- `AR40H_C1AMNEU` = AR35 WIFI
- `AR40H_C1BMNEU` = AR30 WIFI
- Veľkosti: **07** (2 kW), **09** (2,5 kW), **12** (3,5 kW), **15** (4,25 kW), **18** (5 kW), **24** (6,5 kW)

### Cenová tabuľka RAC podľa veľkosti (sety, EUR)
| Rada | 07 | 09 | 12 | 15 | 18 | 24 |
|---|---|---|---|---|---|---|
| Première+ White | – | 1 845 | 2 047 | – | – | – |
| Première+ Black | – | 1 882 | 2 088 | – | – | – |
| Première White | 1 574 | 1 683 | 1 870 | 2 357 | 2 876 | 3 800 |
| Première Black | 1 597 | 1 715 | 1 906 | – | – | – |
| Avant S2 Black | 1 427 | 1 531 | 1 701 | – | – | – |
| Avant S2 White | 1 402 | 1 504 | 1 671 | 2 106 | 2 571 | 3 396 |
| Comfort S2 | – | 1 221 | 1 357 | – | 2 088 | 2 757 |
| Cebu S2 | 960 | 1 028 | 1 142 | 1 439 | 1 759 | 2 320 |
| Luzon S2 | – | 990 | 1 099 | – | 1 692 | 2 234 |
| AR35 WIFI | – | 809 | 897 | – | 1 578 | 1 900 |
| AR30 WIFI | – | 809 | 897 | – | – | – |

### Prevádzkový rozsah
- **Chladenie:** -10°C / +46°C (všetky RAC)
- **Vykurovanie:** -15°C / +24°C (všetky RAC)

---

## 2. FJM – Multi-Split (2-5 izieb na 1 vonkajšiu)

### Vonkajšie jednotky AJ
| Model | Izby | kW chl./vyk. | SEER (najlepšia komb.) | SCOP | Trieda | Max. potrubie | Cena |
|---|---|---|---|---|---|---|---|
| AJ040TXJ2KG | 2 | 4,0 / 4,2 | 8,54 | 4,64 | A+++ / A++ | 30 m | **1 654 €** |
| AJ050TXJ2KG | 2 | 5,0 / 5,6 | 8,54 | 4,64 | A+++ / A++ | 30 m | **1 899 €** |
| AJ052TXJ3KG | 3 | 5,2 / 6,3 | 8,51 | 4,60 | A+++ / A++ | 50 m | **2 140 €** |
| AJ068TXJ3KG | 3 | 6,8 / 8,0 | 7,75 | 4,32 | A++ / A+ | 50 m | **2 498 €** |
| AJ080TXJ4KG | 4 | 8,0 / 9,3 | 7,75 | 4,10 | A++ / A+ | 70 m | **3 296 €** |
| AJ100TXJ5KG | 5 | 10,0 / 12,0 | 8,00 | 4,32 | A++ / A+ | 75 m | **3 654 €** |

> **Pripojovací pomer až 176 %**, NASA protokol, kombinovateľné nástenné/kazetové/kanálové/parapetné.

### Multi-Split vnútorné nástenné (samostatné, bez vonkajšej)
| Rada | Veľkosti | Cena rozpätie |
|---|---|---|
| Première+ White | 07, 09, 12 | 780 – 1 014 € |
| Première+ Black | 07, 09, 12 | 812 – 1 055 € |
| Première White | 07, 09, 12, 18, 24 | 740 – 1 819 € |
| Première Black | 07, 09, 12 | 763 – 931 € |
| Avant S2 Black | 07, 09, 12 | 641 – 782 € |
| Avant S2 White | 07, 09, 12, 18, 24 | 616 – 1 528 € |
| Comfort S2 | 07, 09, 12, 18, 24 | 445 – 1 103 € |
| Cebu S2 | 07, 09, 12, 18, 24 | 374 – 938 € |
| Luzon S2 | 07, 09, 12, 18, 24 | 360 – 894 € |

### Multi-Split iné formáty
| Typ | Modely | Cena | Poznámka |
|---|---|---|---|
| WindFree Mini 4-Way Cassette | AJ016/020/026/035/052 TNN | 628 – 961 € | + panel PC4SUFMAN 252 € |
| WindFree 1-Way Cassette | AJ026/035 TN1 | 656 – 801 € | + panel PC1NWFMAN 273 € |
| LSP Slim Duct | AJ026/035 TNL | 890 – 922 € | čerpadlo zabudované |
| MSP Duct | AJ052 BNM | 1 001 € | + voliteľné čerpadlo |
| Console (parapetná) | AJ026/035/052 TNJ | 729 – 965 € | s ionizérom |

### Kombinačná tabuľka (max. veľkosti vnútorných na vonkajšiu)
| Vonkajšia | Console | 5,0 kW WM | 6,5 kW WM | 5,2 kW Cassette |
|---|---|---|---|---|
| AJ040 | 5,2 | – | – | – |
| AJ050 | 5,2 | ✓ | – | – |
| AJ052 | 5,2 | ✓ | – | – |
| AJ068 | – | ✓ | – | ✓ |
| AJ080 | – | ✓ | ✓ | ✓ |
| AJ100 | – | ✓ | ✓ | ✓ |

> Detailné kombinácie v `fjm.json` → `fjm_combination_table`.

---

## 3. CAC – Komerčný Split

### Outdoor (R32) – ceny EUR
| Model | kW chl./vyk. | Napájanie | Cena |
|---|---|---|---|
| AC026RXADKG | 2,6 / 3,3 | 1f | 1 156 € |
| AC035RXADKG | 3,5 / 4,0 | 1f | 1 285 € |
| AC052RXADKG | 5,0 / 6,0 | 1f | 1 513 € |
| AC071RXADKG | 7,1 / 8,0 | 1f | 1 960 € |
| AC100RXADKG / NG | 10,0 / 11,2 | 1f / 3f | 2 652 / 2 784 € |
| AC120RXADKG / NG | 12,0 / 13,2 | 1f / 3f | 2 922 / 3 067 € |
| AC140RXADKG / NG | 13,4 / 15,5 | 1f / 3f | 2 998 / 3 148 € |

### Outdoor (R32 HighEE) – -20°C/+52°C, vnút. teplota vyk. od 8°C
| Model | kW | Cena |
|---|---|---|
| AC026BXAPKG | 2,6 | 1 587 € |
| AC035BXAPKG | 3,5 | 1 764 € |
| AC052BXAPKG | 5,0 | 2 071 € |
| AC071BXAPKG / NG | 7,1 | 2 654 / 2 787 € |
| AC100BXAPKG / NG | 10,0 | 3 561 / 3 722 € |
| AC120BXAPNG | 12,1 | 4 099 € |
| AC140BXAPNG | 13,4 | 4 213 € |

### Outdoor (R410a) – HSP Duct, AHU
| Model | kW | Cena |
|---|---|---|
| AC100BXPDKH | 10,0 | 2 652 € |
| AC140BXPDNH | 13,4 | 3 148 € |
| AC200KXAPNH | 20,0 | 5 595 € |
| AC250KXAPNH | 25,0 | 6 429 € |

### Indoor typy (CAC)
| Typ | Veľkosti | Cenové rozpätie indoor |
|---|---|---|
| 360 Cassette (kruhová) | 071/100/120/140 | 1 299 – 1 626 € + panel 256+ € |
| 360 Cassette HighEE | 052/071 | 1 260 – 1 299 € |
| WindFree 1-Way Cassette | 026/035 | 745 – 782 € + panel 273 € |
| Mini 4-Way 60x60 | 026/035/052/071 | 481 – 828 € + panel 252 € |
| Mini 4-Way HighEE | 026/035/052 | 481 – 664 € |
| 4-Way Cassette 95x95 | 052/071/100/120/140 | 917 – 1 626 € + panel 270+ € |
| 4-Way HighEE | 071/100/140 | 942 – 1 181 € |
| WindFree QMD Wallmounted | 026/035/052/071 | 503 – 810 € |
| WindFree QMD HighEE | 026/035/052/071 | 503 – 810 € |
| Wallmounted Max | 100 (1f/3f) | 1 173 € |
| Wallmounted Max HighEE | 100 (1f/3f) | 1 173 € |
| Console parapetná | 026/035/052 | 634 – 911 € |
| LSP Slim Duct | 026/035/052/071 | 725 – 829 € |
| MSP Duct | 035/052/071/100/120/140 | 739 – 1 128 € |
| MSP Duct HighEE | 052/071/100 | 771 – 998 € |
| HSP Duct (R410a) | 200/250 | 2 977 – 3 425 € |
| Ceiling podstropná | 052/071/100/120/140 | 761 – 2 167 € |
| Ceiling HighEE | 071 | 802 € |
| Floor Standing (R410a) | 100/140 | 1 096 – 1 234 € |

### CAC DPM – Twin/Triple/Quad refnety
- **MXJ-2D2509K** – 157 € (2 vnút.)
- **MXJ-3D2509K** – 195 € (3 vnút.)
- **MXJ-4D2509K** – 287 € (4 vnút.)

---

## 4. Príslušenstvo – kľúčové položky

### Diaľkové ovládanie / WiFi
| Kód | Popis | RAC | FJM | CAC | Cena |
|---|---|---|---|---|---|
| AR-EH03E | IR ovládač s WindFree | ✓ | ✓ | ✓ | 76 € |
| AR-CH01E | IR Solárny ovládač | – | – | ✓ | 99 € |
| MWR-WG01KN | Káblový SK/CZ | ✓ | ✓ | ✓ | 206 € |
| MWR-SH11N | Káblový dotykový | ✓ | ✓ | ✓ | 158 € |
| MIM-H14EN | WiFi individuálny | – | – | ✓ HEE | 81 € |
| MIM-H04EN | WiFi centrálny | ✓ | ✓ | ✓ | 231 € |
| MCM-A300BN | Centrálny dotykový | ✓ | ✓ | ✓ | 1 485 € |

### BMS
- **MIM-B19N** Modbus – 115 €
- **MIM-B17BN** BACnet – 3 317 €
- **MIM-B18BN** LonWorks – 3 370 €

### Senzory pohybu (úspora energie pri neprítomnosti)
- **MCR-SMD** – Mini 4-Way 60x60 – 125 €
- **MCR-SMC** – 4-Way 95x95 – 125 €
- **MCR-SME** – 360 Cassette – 125 €

### Dekoračné panely – NUTNÉ pre kazetové
| Pre | Kód | Cena |
|---|---|---|
| Mini 4-Way (FJM, CAC RNN) | PC4SUFMAN | 252 € |
| Mini 4-Way HEE (CAC BNN) | PC4SUFMANW | 252 € |
| 1-Way Cassette | PC1NWFMAN | 273 € |
| 4-Way 95x95 (CAC RN4) | PC4NUFMAN | 270 € |
| 4-Way 95x95 + Air Purif. | PC4NUCEAN | 845 € |
| 4-Way 95x95 + Auto Elev. | PC4NUXMAN | 587 € |
| 360 (4 farby/tvary) | PC4NUDMAN/UNMAN/BDMAN/BNMAN | 256 € |
| 360 + Air Purif. | PC6EUCMAN(W) | 751 € |
| 360 + Auto Elev. | PC6EUXMAN(W) | 704 € |

> Plný zoznam panelov v [accessories.json](accessories.json) → `decorative_panels_cassettes`.

---

## 5. Predajný cheat-sheet

### Podľa rozpočtu (Single-Split set, veľkosť 09 = 2,5 kW)
- **Najlacnejší:** AR30 / AR35 WIFI – 809 €
- **S AI a SmartThings od:** Luzon S2 – 990 €
- **S WindFree režimom od:** WindFree Comfort S2 – 1 221 €
- **A+++ od:** WindFree Avant S2 – 1 504 €
- **TOP rad:** WindFree Première+ – 1 845 €

### Podľa funkcií
| Funkcia | Rady |
|---|---|
| **WindFree režim** (bez prievanu) | Comfort S2, Avant S2 (W/B), Première (W/B), Première+ (W/B) + všetky CAC WindFree |
| **AI Motion Wings** | Première+ (TOP) |
| **Integrovaný radarový senzor** | Première+ |
| **AI Bixby ovládanie** | Comfort S2, Avant S2, Première, Première+ |
| **Wi-Fi SmartThings štandardne** | Všetky AR50/60/70 + AR30/AR35 |
| **Solárny IR ovládač v balení** | Cebu S2, Comfort S2, Avant S2, Première, Première+ (NIE Luzon, NIE AR30/35) |
| **4-in-1 filter** | Première, Première+ |
| **Tri-care filter** | Avant S2 (W/B) |
| **Easy Filter Plus** | Cebu, Luzon, Comfort S2, Avant, Première, Première+ |
| **Freeze Wash** (samočistenie) | Comfort S2, Avant S2, Première, Première+ |
| **Ionizér (SPi)** | Console (FJM aj CAC) |

### Voľba kapacity (orientačne)
| kW | m² (orientačne) | Veľkosť | Typický model (Avant S2) |
|---|---|---|---|
| 2,0 | do 20 | 07 | AR70F07C1AWNEU |
| 2,5 | 20-30 | 09 | AR70F09C1AWNEU |
| 3,5 | 30-40 | 12 | AR70F12C1AWNEU |
| 4,25 | 40-50 | 15 | AR70F15C1AWNEU |
| 5,0 | 50-60 | 18 | AR70F18C1AWNEU |
| 6,5 | 60-80 | 24 | AR70F24C1AWNEU |

---

## 6. Vyhľadávacie kľúče (rýchlo)

**Hľadanie modelu:**
```bash
grep "AR70H09CAAW" rac.json fjm.json cac.json accessories.json
```

**JSON štruktúra (všetky súbory):**
- Každý JSON má **metadata** s prehľadom + tematické sekcie pre rady/produkty
- Ceny v JSON sú v `price_EUR` (číslo, nie string)
- Vnútorná = `indoor`, Vonkajšia = `outdoor`
- Setová cena = `set_price_EUR`
- Samostatná indoor/outdoor cena = `indoor_price_EUR` / `outdoor_price_EUR`

**Konvencia model code (Samsung):**
- `AR` – residential nástenná (RAC + FJM indoor)
- `AJ` – Multi-Split (vonkajšie TXJ, vnútorné multi-only kazety/kanály)
- `AC` – Commercial split (CAC)
- `MWR-` – káblový ovládač
- `MIM-` – komunikačné/BMS moduly
- `MCM-` – centrálne ovládače
- `MCR-` – senzory pohybu
- `MDP-` – čerpadlá kondenzátu
- `MXD-` – AHU Kit
- `MXJ-` – refnety
- `PC` – dekoračné panely

**Sufix v kódoch RAC/FJM:**
- `NEU` – vnútorná jednotka (indoor)
- `XEU` – vonkajšia jednotka (outdoor)

**Sufix v kódoch CAC:**
- `KG/EU` – 1-fázové (1f, 220-240 V)
- `NG/EU` – 3-fázové (3f, 380-415 V)
- `R*` – staršia generácia (R32 alebo R410a)
- `B*` – nová generácia / HighEE

---

## 7. Token-efektívna stratégia pre chatbota

| Stratégia | Tokeny / dotaz | Vhodné pre |
|---|---|---|
| **A. SAMSUNG_INDEX.md v system prompte** + 4 JSON ako tools | ~5k base + 2-5k per query | **odporúčané** |
| **B. Všetko v system prompte** (RAC + FJM + CAC + acc.) | ~80k cached + ~500 fresh | málo konverzácií |
| **C. RAG (embeddings + retrieval)** | ~300-1000 / dotaz | tisíce konverzácií |

**Odporúčaný setup:** systém prompt obsahuje SAMSUNG_INDEX.md + [glossary.json](glossary.json) (~8k tokenov), bot má tooly:
- `get_rac_series(series_name)` → vráti príslušnú sekciu z rac.json
- `get_fjm_combination(outdoor_model)` → vráti povolené vnútorné z fjm.json
- `get_cac_series(category)` → vráti vybranú CAC sekciu z cac.json
- `get_accessory(code_or_purpose)` → vyhľadá v accessories.json

**Glossary tip:** [glossary.json](glossary.json) treba načítať do system promptu (~3k tokenov) – obsahuje:
- `category_aliases` – rozpozná RAC/FJM/CAC z dotazu
- `product_type_aliases` – nástenná/kazety/kanály/parapetná/floor standing v EN aj SK
- `rac_series_aliases` – rozpozná „premiere plus black", „cebu", „luzon", atď.
- `feature_aliases` – WindFree, AI Motion Wings, SmartThings, Bixby, Tri-care filter, Freeze Wash
- `design_lines` – GRID / GEO / AIRISE
- `panels_aliases` – PC4SUFMAN/PC4NUFMAN/PC4NUDMAN... podľa typu kazety
- `technical_glossary` – WindFree™ technológia, FJM/176%, NASA protokol, AHU Kit, HighEE, R32 vs R410a
- `use_case_to_recommendation` – odporúčania podľa veľkosti priestoru a požiadaviek
- `common_questions_and_answers` – rozdiely medzi radmi, čo je WindFree, panely, atď.
