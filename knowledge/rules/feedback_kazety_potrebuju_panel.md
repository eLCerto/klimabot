---
name: kazety-vyzaduju-dekoracny-panel
description: Kazeta NEFUNGUJE bez dekoračného panela a ovládača — pridaj ich do quote. Rezidenčné kazety sú v multi-split radoch (Toshiba FLAT a 60x60, Samsung Mini 4-Way), kódy cez lookup_product
type: feedback
---

Kazetové vnútorné jednotky (Toshiba 60x60 Slim, 1-cestná FLAT, 4-cestná štandardná, Smart kazeta; Samsung Mini 4-Way, 4-Way, 1-Way, 360 Cassette) **NEFUNGUJÚ bez dekoračného panela**. Panel je samostatná položka s vlastnou cenou. Pri ponuke pošli do `quote` jednotku + panel + ovládač, aby celková cena bola úplná.

**Why:** Zákazník môže predpokladať, že „kazeta" je hotový produkt. Po objednaní zistí, že chýba panel, a cíti sa oklamaný. Toto je častý zdroj reklamácií u distribútorov.

**How to apply:**
- Trigger frázy zákazníka: „kazeta", „cassette", „60x60", „kruhová kazeta", „4-cestná".
- Do jedného volania `quote` pošli: vnútornú kazetovú jednotku + vonkajšiu jednotku + kód panela (+ kód ovládača, ak ho jednotka nemá v cene).
- V odpovedi rozpíš riadky z `quote` (jednotka, panel, ovládač) a `total_eur`.

**Rezidenčné kazety existujú — ako multi-split vnútorné jednotky.** V single-split radoch (SEIYA, SHORAI, HAORI, DAISEIKAI, Samsung RAC) kazeta nie je, ale rezidenčné multi-split rady ju majú aj v malých výkonoch: Toshiba 1-cestná FLAT a 60x60 Slim (RAS multi), Samsung WindFree Mini 4-Way 60x60 a 1-Way (FJM). Predávajú sa s multi-split vonkajšou jednotkou, aj keď je v miestnosti jediná vnútorná (Toshiba: s jedinou vnútornou jednotkou podľa `combinations_table` iba chladí — povedz to). Komerčné kazety sú Toshiba RAV a Samsung CAC.

- Kódy nájdeš okamžite cez `lookup_product` s typom a výkonom („<značka> kazetová <výkon v kW>“) — vráti rezidenčné aj komerčné kazety s tým, čo potrebujú.
- Nikdy netvrď, že rezidenčná kazeta v danom výkone neexistuje, ani že začína od nejakého výkonu — over to cez `lookup_product`.
- Nástennú jednotku (napr. SEIYA) nikdy nenazývaj kazetovou a nenaceňuj ju ako kazetu.
- `quote` odmietne kazetu bez panela a bez ovládača.

**Panely k bežným kazetám** (kód nájdeš aj cez `search_knowledge`):

| Typ kazety | Panel |
|---|---|
| Toshiba 60x60 Slim (Multi aj RAV) | RBC-UM21P-E (biely), RBC-UM21PB-E (čierny) |
| Toshiba 1-cestná FLAT (Multi) | RBC-UY32P-E / RBC-UY42P-E podľa šasi |
| Toshiba 4-cestná RAV | RBC-U32PGP-E |
| Samsung Mini 4-Way FJM | PC4SUFMAN |
| Samsung 360 Cassette CAC | PC4NUDMAN (voliteľne Air Purification PC6EUCMAN, Auto Elevation PC6EUXMAN) |
| Samsung 4-Way 95x95 | voliteľne PC4NUCEAN (Air Purification), PC4NUXMAN (Auto Elevation) |

**Toshiba RAV:** cenník uvádza aj ceny celých setov, ktoré už obsahujú kompaktný ovládač RBC-ASCU32Y-E (pri kazetách aj panel). `quote` naceňuje RAV po jednotlivých kódoch — preto pri RAV vždy pridaj ovládač RBC-ASCU32Y-E (a pri kazete panel), inak bude ponuka nižšia ako cenníkový set a neúplná.
