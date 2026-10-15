---
name: search-knowledge-limit-per-turn
description: Max 2× `search_knowledge` na user turn. Server-side counter loguje `search_knowledge_overuse` pri 3+. Použí `lookup_product` / `compare_products` / handoff namiesto opakovania.
type: feedback
---

`search_knowledge` je drahý (hybrid BM25 + embeddings + cross-encoder rerank, 5–10 chunkov v context budget-e). **Max 2× na user turn.** Server-side counter loguje `search_knowledge_overuse` pri 3+ a pošle notice botovi.

**Why:**
- Každé volanie pridá ~5–8k tokenov. Pri 7× volaniach v session: 35–56k tokenov navyše = 4× vyššia cena.
- Opakované dotazy na tú istú tému vrátia rovnaké chunky (diminishing returns).
- Pri 5+ search-och bot odkladá akciu, zákazník čaká.

**How to apply:**

### Limit per turn

| Počet | Stav | Bot smie |
|---|---|---|
| 1× | OK | pokračuj |
| 2× | OK pri komplexnom dotaze | druhý search **iný keyword set**, nie parafráza |
| 3× | **Stop** | použí čo máš, `lookup_product` / `compare_products` / handoff |
| 4×+ | porušenie | mal už handoff |

### Voľba keywordov

Namiesto série úzkych dotazov, jeden širší dotaz vráti všetky relevantné chunky cez rerank.

❌ ZLE (skutočne sa stalo, 5× search pre tú istú tému):
```
search_knowledge("Samsung FJM multi-split nástenná 2 indoor")
search_knowledge("Samsung FJM outdoor 2 indoor")
search_knowledge("Samsung FJM vykurovanie -15")
search_knowledge("Samsung AR70F Avant S2 heating")
search_knowledge("Samsung FJM AR70F09C1AWNEU AJ050 package")
```

✅ LEPŠIE:
```
search_knowledge("Samsung FJM multi-split WindFree Avant Comfort 2 indoor vykurovanie operating range cena")
search_knowledge("Samsung FJM AJ050 outdoor combinations table indoor pairings")
```

### Po 2 search-och ak chýba info

1. **`lookup_product`** s konkrétnym model kódom — vráti detail vrátane `category_path` + cena + špecifikácie.
2. **`compare_products`** pre side-by-side 2+ modelov.
3. **Ak nie je v KB**, priznaj: *„Detail X nemám v databáze, PM vám to potvrdí pri obhliadke."* Volaj `request_human_handoff` ak je to scope-blocker.

### NEROB

- ❌ `search_knowledge` na rovnakú tému s parafrázou v jednom turn-e.
- ❌ `search_knowledge` pred `lookup_product` na známy model kód — lookup je presnejší a lacnejší.
- ❌ `search_knowledge` po `quote` — cena je už vypočítaná.
- ❌ Cyklus „search → text → search → text → search". Po 2 search-och buď máš info, alebo handoff.

### Súvisiace pravidlá

- [[discovery-pred-konkretnou-ponukou]] — discovery otázky neexpanduj search dotazmi pre každú vec.
- [[aplikacia-rabatov-zo-discounts-json]] — po `lookup_product` rovno `quote`, nie ďalší search.
