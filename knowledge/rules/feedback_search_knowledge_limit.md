---
name: search-knowledge-limit-per-turn
description: 1× `search_knowledge` na otázku zákazníka (druhý iba keď prvý nič nevrátil, tvrdý limit 3 na správu). Kódy setov cez `lookup_product` s názvom radu a výkonom, nie cez search.
type: feedback
---

`search_knowledge` je pomalý a drahý (hybrid BM25 + embeddings + cross-encoder rerank, ktorý na serveri trvá okolo 9 s, a 5–10 chunkov v context budget-e). **Na otázku zákazníka 1× dôkladný dotaz.** Server pri druhom hľadaní v tej istej správe pošle notice a tretie je posledné povolené (tvrdý limit).

**Why:**
- Každé volanie pridá ~5–8k tokenov. Pri 7× volaniach v session: 35–56k tokenov navyše = 4× vyššia cena.
- Opakované dotazy na tú istú tému vrátia rovnaké chunky (diminishing returns).
- Každé hľadanie zákazníka zdrží o niekoľko sekúnd; tri hľadania = pol minúty čakania.

**How to apply:**

### Limit na jednu správu zákazníka

| Počet | Stav | Bot smie |
|---|---|---|
| 1× | OK | jeden dotaz so všetkými kľúčovými slovami naraz |
| 2 naraz | nespustí sa | v jednej odpovedi server spustí iba prvé hľadanie — zlúč kľúčové slová do jedného dotazu |
| 2× | výnimka | iba keď prvý nevrátil nič použiteľné, **iný keyword set**, nie parafráza |
| 3× | posledné povolené | potom server ďalšie hľadanie nespustí — použi čo máš |

### Kódy setov bez hľadania

`lookup_product` prijme aj **názov radu a výkon** („<značka> <rad> <výkon v kW>“) a okamžite vráti presné kódy setov (vnútorná + vonkajšia jednotka). Na kódy nikdy nehľadaj cez `search_knowledge` (hľadanie „model kód“ je zbytočných 9 sekúnd).

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

### Keď po hľadaní chýba info

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
