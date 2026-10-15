---
name: alergie-prioritne-modely-s-filtraciou
description: Pri zmienke alergie / astma / prach / čistý vzduch odporuč triedu 1 z poradia filtrácie (config/filtration_policy.json), nie najlacnejšie
type: feedback
---

Ak zákazník spomenie **alergiu, astmu, deti, citlivosť na prach, kvalitu vzduchu, peľ, roztoče**, alebo „čo najlepšiu filtráciu" – prioritne odporuč modely s pokročilou filtráciou. NEPONÚKAJ entry rady (SEIYA Classic 2, AR30/AR35, Luzon S2) bez upozornenia že majú len základný prachový filter.

**Why:** Alergici sú špecifický segment ktorý si **kupuje klimatizáciu primárne kvôli kvalite vzduchu**, nie kvôli cene. Ak im odporučíš entry model so základným filtrom a ich symptómy sa nezmiernia, vrátia sa s reklamáciou alebo dajú zlú recenziu („Toshiba SEIYA mi nepomohla na alergie"). Rozdiel medzi entry a premium filtráciou je v stovkách eur, ale pre alergikov je to kľúčový rozdiel.

**How to apply:**

### Trigger frázy
- „alergia", „alergic", „alergik"
- „astma", „dýchanie", „dýchacie problémy"
- „prach", „peľ", „roztoče"
- „kvalita vzduchu", „čistý vzduch", „čistenie vzduchu"
- „dieťa", „malé deti", „bábätko"
- „antibakteriálny", „antialergický"
- „PM2.5", „jemné častice"

### Odporúčania: poradie filtrácie

Poradie nástenných radov podľa filtrácie (triedy 1–4) je v `config/filtration_policy.json`. Server ho pri zmienke alergie, prachu alebo kvality vzduchu pošle v kontexte a `quote` upozorní, keď existuje lepšia trieda v tej istej veľkosti. Tu ho nepreberaj zo starých poznámok.

- Odporúčaj **triedu 1**. Rady v jednej triede sú rovnocenné: rešpektuj značku, ktorú zákazník chce, inak ponúkni lacnejší (cenu zistíš cez `quote`).
- Žiadny rad nenazývaj lepšou filtráciou, než mu dáva poradie, a odporúčanie nemeň len preto, že zákazník namietne — vysvetli poradie.
- HAORI má rovnakú filtráciu ako DAISEIKAI 10 (plazmový ionizátor + Ultra Pure). „Ozónová čistička“ v starších záznamoch bola chyba prekladu slovenského katalógu — ozón nespomínaj.
- Filter Ultra Pure je pri SHORAI CURVE voliteľný — ak ho zákazník chce, pridaj kód filtra do `quote`.

**Toshiba RAV (komerčné):**
1. **4-cestná štandardná kazeta** + voliteľný **TCB-EAPC1UHP-E plazmový filter PURE** – pre obchody, ordinácie

### Príklad správnej odpovede

Zákazník: „Mám alergiu na prach, akú klimatizáciu odporúčate?"

Bot: „Pre alergikov odporúčam rady s najlepšou filtráciou – nie základné prachové filtre. Rovnocenné možnosti:

**Toshiba DAISEIKAI 10** a **Toshiba HAORI**: prachový filter + plazmový ionizátor + filter Ultra Pure, ktorý zachytáva jemné častice PM2.5. DAISEIKAI 10 má navyše HADA careflow (jemné prúdenie bez prievanu), HAORI textilný kryt.

**Samsung WindFree Avant S2**: Tri-care filter + Easy Filter Plus + Freeze Wash (samočistenie). WindFree režim chladí bez priameho prievanu.

Akú veľkú miestnosť plánujete chladiť? Podľa veľkosti pripravím presné ceny a uvidíte aj rozdiel medzi nimi."

### NEROB
- ❌ Neodporúčaj SEIYA Classic 2 / AR30 / AR35 / Luzon S2 alergikom (len základný prachový filter)
- ❌ Nezamietnuť otázku „mám alergiu" frázou „všetky klimatizácie majú filter" – nie všetky majú dobrú filtráciu
- ❌ Nezabudni, že Ultra Pure 2.5 je v SHORAI voliteľný – ak ho zákazník chce, pridaj kód filtra do `quote`
