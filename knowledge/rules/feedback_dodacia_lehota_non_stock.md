---
name: dodacia-lehota-non-stock-modely
description: Pri ponuke modelov označených "Nejde o skladový tovar – dodacia lehota na dopyt" upozorni zákazníka pred objednaním
type: feedback
---

Niektoré modely Toshiba sú **non-stock** (nie sú skladovým tovarom u distribútora AIR-COND International). Pri ponuke takého modelu zákazníkovi VŽDY uveď že ide o objednávku s dodacou lehotou a odporuč overenie konkrétneho dátumu.

**Why:** Zákazníci typicky predpokladajú že keď je v cenníku, je „na sklade" a doručenie do týždňa. Pri non-stock to môže byť 3–8 týždňov (objednávka z výroby Toshiba). Ak zákazník objedná pred sezónou (júl, august) a klimatizácia príde až v septembri, je to vážny problém. Lepšie ho na to upozorniť dopredu a navrhnúť alternatívu zo skladu.

**How to apply:**

Dostupnosť každej položky vracia `quote` v poli `availability` (zdroj `stock_policy.json` — zoznamy nižšie sú len prehľad). Povedz ju zákazníkovi tak, ako je, spolu s cenou; dostupnosť nikdy nepodmieňuj kontaktom. Termín dodania ani montáže nesľubuj a nehodnoť, či je zákazníkov termín reálny — potvrdí ho projektový manažér.

### Toshiba RAS – ŠTANDARDNE skladové
- Všetky SEIYA Classic 2, SEIYA, SHORAI CURVE (W/B), DAISEIKAI 10 White
- Multi-Split outdoor 2M / 3M / 4M / 5M
- Multi-Split indoor (kazety, kanál, parapetná, nástenné)
- Bežné príslušenstvo (ovládače, panely, filtre)

### Toshiba RAS – non-stock (dodacia lehota)
- **DAISEIKAI 10 Wood** – z dôvodu drevenej úpravy je vyrobená na objednávku (pri každej veľkosti 10/13/18)

### Toshiba RAV – non-stock (dodacia lehota)
- **Smart kazeta** (RAV-HM561UT-E, RAV-HM801UT-E, RAV-HM1101UT-E, RAV-HM1401UT-E) – explicitne uvedené v katalógu
- **Stojanová jednotka** (RAV-HM561FT-E – RAV-HM1601FT-E) – explicitne uvedené v katalógu
- **RBC-MTSC1 ovládač** (Local Touch Lite, 4,5" dotyk) – objednávkový tovar
- **TO-RC-BAC-1 BACnet rozhranie** – objednávkový tovar

### Samsung – status v cenníku 2026 nešpecifikuje skladovú dostupnosť
Pri Samsung neuvádzaj automaticky non-stock status, ale ak zákazník chce konkrétny model, odporuč overenie dostupnosti u predajcu.

### Príklad správnej odpovede

Zákazník: „Chcem DAISEIKAI 10 Wood pre obývačku 30 m²."

Bot: „DAISEIKAI 10 Wood veľkosť 13 (3,5 kW) je výborná voľba pre 30 m². **Upozornenie:** DAISEIKAI 10 Wood **NIE je skladový tovar** – vyrobí sa na vašu objednávku, dodaciu lehotu potvrdí projektový manažér. Ak potrebujete skôr, alternatívou je **DAISEIKAI 10 White** (technicky identický, len bez dreveného frontu) ktorý býva skladom. Chcete pokračovať s Wood verziou alebo si vyberiete White?"

### NEROB
- ❌ Neponúkaj non-stock modely bez upozornenia
- ❌ Nesľubuj konkrétne dátumy doručenia (overuje predajca, nie chatbot)
- ❌ Nezamlčuj alternatívu zo skladu (zákazník to oceňuje)
