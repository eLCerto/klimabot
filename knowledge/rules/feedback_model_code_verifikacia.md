---
name: model-code-verifikacia-po-lookup
description: Po `lookup_product` over že vrátený `category_path` sedí s radom, ktorý si zákazníkovi prezentoval. Ak nesedí, znova `search_knowledge` na správny rad.
type: feedback
---

`lookup_product` vracia `category_path` (napr. `Toshiba.indoor_units_wallmount.SHORAI_CURVE_White`). **Po každom volaní over že sedí s radom v tvojej prezentácii.** Ak nesedí, kód je zlý — celá ponuka (cena, vlastnosti, lead) bude pre iný produkt.

**Why:** V reálnej session bot prezentoval *„DAISEIKAI 10 White"*, ale poslal kódy `RAS-B13P2KVSG-E + RAS-13P2AVSG-E` — to sú **SHORAI CURVE** kódy. Bot to v jednom turn-e zbadal („tie lookup-ov mi vrátili SHORAI"), ale pokračoval so SHORAI a odovzdal PM lead so SHORAI kódmi pod popisom „DAISEIKAI". Zákazník očakáva DAISEIKAI (HADA Careflow, plazma, výrazne drahší rad). PM → konflikt → reklamácia.

Skutočné DAISEIKAI 10 White: `RAS-B13S4KVPG-E` (indoor) + `RAS-13S4AVPG-E` (outdoor). Rozdiel v `P2K` vs `S4K` — bot ich nesmie improvizovať.

**How to apply:**

### Post-lookup self-check

Po každom `lookup_product` urob túto kontrolu **predtým ako napíšeš text alebo zavoláš ďalší tool:**

```
1. Hovoril som o rade: X (napr. "DAISEIKAI 10 White")
2. category_path vrátil: Y (napr. "Toshiba...SHORAI_CURVE_White")
3. Obsahuje Y reťazec X (case-insensitive, _ == medzera)?
   ÁNO → pokračuj
   NIE → STOP. Zavolaj search_knowledge("X model kódy <veľkosť>")
```

### Ako nájsť správny kód

Ak `lookup_product` vráti zlý rad → kód neexistuje v rade X. Postup:

1. **Nezahadzuj rad X** — to chce zákazník.
2. `search_knowledge` s úzkym dotazom: *„Toshiba DAISEIKAI 10 White model kódy indoor outdoor 13"* / *„Samsung WindFree Avant S2 AR70 veľkosť 12 set"*.
3. Z výsledku vyber model code obsahujúci správny rad v `category_path` (KB má v každom chunku `Kategória:` a v product záznamoch `category_path`).
4. `lookup_product` znova s novým kódom + opätovný self-check.
5. Až po overenej zhode `quote` a `update_customer_state.model_selected`.

### Časté zámeny

| Kód | Rad |
|---|---|
| `RAS-B13P2KVSG-E` | SHORAI CURVE White |
| `RAS-B13S4KVPG-E` | DAISEIKAI 10 White |
| `RAS-B13S4KVDG-E` | DAISEIKAI 10 Wood |
| `RAS-B13E2KVG-E` | SEIYA Classic 2 |
| `AR**F**` prefix | WindFree (Samsung) |
| `AR**TXEAW**` | AR30/35 (entry Samsung) |

Pri pochybnostiach vždy `search_knowledge`, nie improvizácia.

### NEROB

- ❌ **Improvizovať kód z pamäti.** Bot pozná vzor, ale konkrétny kód musí vždy overiť v KB.
- ❌ Ignorovať `category_path` v response — je to hlavná návratová hodnota pre self-verifikáciu, nie len informácia navyše.
- ❌ Pokračovať so zlým kódom „pretože už je neskoro". PM to postrehne → reklamácia. **Oprav v rovnakom turn-e.**
- ❌ Spýtať zákazníka „chcete DAISEIKAI alebo SHORAI?" keď zákazník jasne povedal DAISEIKAI a ty máš zlý kód. Vyrieš ticho cez `search_knowledge`.
- ❌ Zapísať do `model_selected` kód, ktorého `category_path` nesedí s prezentáciou. PM dostane lead s mismatch produktom.

### Súvisiace pravidlá

- [[search-knowledge-limit-per-turn]] — verifikácia kódu sa počíta; pri vyčerpaných 2× preferuj `lookup_product` ďalších kandidátov alebo handoff.
- [[handoff-zapis-z-rozhovoru-pre-pm]] — `model_selected` v handoff Markdowne musí zodpovedať skutočnému radu, nie len napísanému názvu.
- [[aplikacia-rabatov-zo-discounts-json]] — zlý kód v `quote` = cena za iný produkt.
