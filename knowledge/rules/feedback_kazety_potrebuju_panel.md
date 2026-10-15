---
name: kazety-vyzaduju-dekoracny-panel
description: Pri každej ponuke kazetovej jednotky uveď, že NEFUNGUJE bez dekoračného panela, a pridaj kód panela (a ovládača) do toho istého volania quote
type: feedback
---

Kazetové vnútorné jednotky (Toshiba 60x60 Slim, 1-cestná FLAT, 4-cestná štandardná, Smart kazeta; Samsung Mini 4-Way, 4-Way, 1-Way, 360 Cassette) **NEFUNGUJÚ bez dekoračného panela**. Panel je samostatná položka s vlastnou cenou. Pri ponuke pošli do `quote` jednotku + panel + ovládač, aby celková cena bola úplná.

**Why:** Zákazník môže predpokladať, že „kazeta" je hotový produkt. Po objednaní zistí, že chýba panel, a cíti sa oklamaný. Toto je častý zdroj reklamácií u distribútorov.

**How to apply:**
- Trigger frázy zákazníka: „kazeta", „cassette", „60x60", „kruhová kazeta", „4-cestná".
- Do jedného volania `quote` pošli: vnútornú kazetovú jednotku + vonkajšiu jednotku + kód panela (+ kód ovládača, ak ho jednotka nemá v cene).
- V odpovedi rozpíš riadky z `quote` (jednotka, panel, ovládač) a `total_eur`.

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
