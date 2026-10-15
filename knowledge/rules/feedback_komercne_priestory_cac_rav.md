---
name: komercne-priestory-automaticky-cac-rav
description: Komerčné priestory (serverovňa, ambulancia, salón, obchod, gastro, fitness, väčšia kancelária) → automaticky Samsung CAC alebo Toshiba RAV. Nikdy nezačínaj RAC/RAS.
type: feedback
---

Komerčný priestor → **automaticky Samsung CAC alebo Toshiba RAV**, nie rezidenčné RAC/RAS. Aj keď je rozpočet napätý.

**Why:**
- Rezidenčné jednotky sú dimenzované na ~4–8 hodín cyklovanej prevádzky. Serverovňa 24/7 a obchod 10–14 h/deň → kompresor sa rýchlo opotrebí, reklamácia po 18 mes.
- Komerčné rady majú vyššiu životnosť kompresora, robustnejší výmenník, vyššiu IP triedu.
- **Server-room funkcia** (zálohovanie/striedanie 2 jednotiek) je IBA v Toshiba RAV a Samsung CAC, nie v RAS/RAC.
- Kazety vs. nástenná: nástenná fúka priamo do klienta v kresle u kaderníka/manikérky — neprofesionálne.
- Filtre (Plazma, UltraPure, Air Purification) sú v komerčných radoch silný argument pre ambulancie/kozmetiky.
- BMS integrácia (KNX, Modbus, BACnet) je v CAC/RAV štandard; v RAC obmedzená cez MIM-B17/18/19, v RAS chýba.

**How to apply:**

### 1. Trigger frázy

- **Serverovňa:** „serverovňa", „server room", „IT miestnosť", „24/7", „rack", „dáta"
- **Zdravotníctvo:** „ambulancia", „ordinácia", „zubár", „čakáreň", „klinika", „MUDr."
- **Salón/wellness:** „barber-shop", „kaderníctvo", „manikúra", „nechtové štúdio", „kozmetika", „pedikúra", „masáže", „solárium"
- **Obchod:** „obchod", „predajňa", „butik", „showroom", „retail"
- **Gastro:** „reštaurácia", „kaviareň", „bar", „cukráreň", „bistro", „pizzeria"
- **Fitness:** „fitness", „posilňovňa", „telocvičňa", „yoga štúdio"
- **Kancelária:** „kancelária", „open space", „zasadačka", „meeting room", „coworking" *(pozor: <25 m², 1–2 osoby = môže byť RAC)*

### 2. Workflow

1. **Potvrď priestor:** „Spomenuli ste *serverovňu / kaderníctvo / …* – pre takéto priestory odporúčam komerčný rad."
2. **Pýtaj špecifické detaily** podľa typu (NIE univerzálne):
   - **Serverovňa**: požadovaný chladiaci výkon (kW) **alebo** tepelný výkon serverov (kW). Z toho cooling ≈ 1,2× thermal output. **Nepýtaj m², počet rackov ani predprípravu.** Ak vie výkon, doplň 1f/3f. Do ponuky vždy pridaj ovládač pre striedanie (Toshiba RBC-AMSU52-E, Samsung MIM-B14).
   - **Ambulancia/salón/kozmetika**: m², počet osôb, počet pracovísk, podhľad, citlivosť na hluk/prievan.
   - **Obchod/gastro**: m², počet osôb v špičke, podhľad. Gastro = odsávanie pár samostatne.
   - **Open-space/coworking**: m², počet pracovných miest, BMS áno/nie.
3. **Navrhni konkrétny komerčný typ** (viď tabuľka).
4. **Spomeň diferenciáciu** od rezidenčnej (životnosť, akustika, filtre, BMS).
5. Volaj `search_knowledge` na konkrétne CAC/RAV modely + `lookup_product` pre cenu.

### 2a. Serverovňa bez technických údajov → handoff

Ak zákazník na otázku o chladiacom/tepelnom výkone povie *„neviem"*, *„nemám tucha"*, *„to nech zistí technik"* → **okamžite zastav technický dotazník a prejdi na zber kontaktov + `capture_lead`**. Ďalšie otázky (napájanie, redundancia) bez znalosti záťaže nemajú zmysel.

Postup:
1. Neutralizuj: „Úplne v pohode, chladiaci výkon nemusíte vedieť teraz — pri obhliadke ho zmeria a vyráta projektový manažér."
2. Vysvetli bezplatnú obhliadku (meranie záťaže, počet serverov, návrh N+1).
3. Vyžiadaj **meno + telefón + obec + GDPR súhlas** podľa [[handoff-zapis-z-rozhovoru-pre-pm]].
4. `capture_lead` s poznámkou v `summary`: *„[SERVEROVŇA – BEZ TECH. ÚDAJOV] Zákazník nepozná chladiaci ani tepelný výkon serverov. PM nech dohodne bezplatnú obhliadku — meranie záťaže pred kalkuláciou. Typicky 2× Samsung CAC HighEE alebo Toshiba RAV SDI v N+1 konfigurácii."*

**Výnimka:** ak ponúkne hrubý odhad („asi 2 kW serverov", „4 boxy") → akceptuj, navrhni orientačnú zostavu s upozornením na obhliadku.

### 3. Mapa: priestor → odporúčaný rad

| Priestor | Samsung CAC | Toshiba RAV | Komentár |
|---|---|---|---|
| **Serverovňa** (záťaž do ~4 kW) | 2× WindFree QMD HighEE (AC026/035/052 BNAPKG/EU) | 2× nástenná RAV-HM301/401/561 KRTP-E + RAV-GM ATP-E (SDI/DI) | **N+1 pár nezávislých single-splitov** — nikdy multi-split. |
| **Serverovňa** (záťaž nad ~4 kW) | 2× 4-Way Cassette HighEE (BN4P) alebo 360 Cassette HighEE | 2× nástenná SDI 80/110 alebo podstropná HM801/1101 CTP-E | Dvojica identických jednotiek, každá na plnú záťaž. 3f pri >9 kW. |
| **Ambulancia / čakáreň** | WindFree 1-Way alebo Mini 4-Way (RN1/RNN) + PC4NUCEAN panel s Air Purification | RAV 60×60 slim (HM301-561 MUTP-E) + Plazma a UltraPure | Antibakteriálne filtre, tichá prevádzka. |
| **Manikúra / barber / kozmetika** | WindFree 1-Way kazeta (najnižší prievan) | RAV podstropná HM401-801 CTP-E alebo 60×60 slim | Klient sedí pod jednotkou 30–60 min — tichá + bez prievanu. Nikdy nástennú nad pracoviskom. |
| **Kaderníctvo / salón** (50–80 m²) | 4-Way Cassette (RN4) alebo 360 | RAV podstropná alebo 4-cestná kazeta | Veľa osôb, výpary chemikálií — odporúč Plazma/Air Purification. |
| **Obchod / predajňa** (do 100 m²) | 4-Way Cassette (RN4) alebo MSP kanálová | RAV kazety, kanálové, nástenné HM801 KRTP-E | Vstupné dvere → predimenzovať o 15–20 %. |
| **Open-space kancelária** | Multi-zónové CAC (DPM Twin/Triple) alebo kazety 60×60 | RAV Twin/Triple kit alebo viacero RAV s RBC-AMSU52-E | BMS (Modbus/BACnet) väčšinou žiadaná. |
| **Reštaurácia / kaviareň** | MSP kanálová alebo 4-Way kazeta s Air Purification | RAV štandardná kanálová HM__BTP-E s antikoróznym výmenníkom | Odsávanie pár samostatne. Antikorózia pri otvorenom uhlí/grile. |
| **Fitness / telocvičňa** | High-výkonové CAC (AC100-140) — kanálová alebo 4-cestná | RAV DI 110/140 alebo SDI 110 | Vlhkosť >60 %, predimenzovať. |
| **Zasadačka** (do 30 m²) | WindFree Mini 4-Way (60×60) alebo WindFree QMD | RAV 60×60 slim alebo HM561 CTP-E podstropná | Kazeta lepšia ako nástenná. |

### 3a. Serverovňa: N+1 redundancia (nie 2× polovica)

1. **Vypočítaj záťaž**: rack so 4–6 servermi ≈ 3–4 kW; 10–15 servermi ≈ 7–10 kW.
2. **Jedna jednotka na celú záťaž s rezervou** — každý systém musí mať chladiaci výkon aspoň násobok tepelnej záťaže podľa `sizing_policy.json` (`capacity_factor_per_system`). `quote` to kontroluje a nevhodnú zostavu odmietne; nikdy 2× polovica.
3. **Druhá identická ako záskok** (rovnaký model + výkon).
4. **VŽDY pár nezávislých single-splitov** (2× outdoor + 2× indoor, oddelené chladivové okruhy). **Nikdy multi-split** (FJM/RAV multi/Twin/Triple/DPM) — zdieľaný okruh = pri úniku chladiva vypadnú všetky indoor jednotky súčasne.
5. **Server-room funkcia** prepne 100 % záťaže na zdravý okruh:
   - **Toshiba RAV**: vstavaná, aktivuje sa cez **RBC-AMSU52-E** ovládač (riadi obe jednotky, auto-switch on temperature rise).
   - **Samsung CAC**: externý kontakt **MIM-B14** (binárna) alebo centrálny MCM-A300BN.
   - **RAC/RAS funkciu nemajú** — preto nevhodné.

**Vždy doplň do sady:**
- 2× outdoor + 2× indoor (rovnaký model)
- Toshiba RAV: 1× RBC-AMSU52-E
- Samsung CAC: 1× MIM-B14 + 1× MWR-WG01KN/SH11N
- Voliteľne: BMS rozhranie (Toshiba TO-RC-MBS-1 / BMS-IFKX0UEW-E; Samsung MIM-B19N) pre monitoring

**Príklad správneho dimenzovania:**

| Tepelná záťaž | Zlé ❌ | Zlé ❌ (multi-split) | Správne ✅ (každý systém s rezervou podľa sizing_policy.json) |
|---|---|---|---|
| 5 kW | 2× 2,5 kW | FJM/Twin 1×out + 2×in | 2× nezávislý 5 kW |
| 10 kW | 2× 5 kW | FJM AJ100 + 2× indoor | 2× nezávislý 10 kW |
| 14 kW | 2× 7,1 kW | Twin kit 14 kW | 2× nezávislý 14 kW (3f) |

### 4. Kancelária — rozlíšenie veľkosti

- **<25 m² / 1–2 osoby** (domáca, freelancer): RAC/RAS OK. WindFree Comfort S2 alebo SHORAI CURVE.
- **25–60 m² / 3–8 osôb**: hraničné — pri 5+ ľuďoch denne / 8+ h prevádzky → CAC/RAV.
- **>60 m² alebo open-space**: vždy CAC/RAV.

### 5. Príklad

**Zákazník:** „Nechtové štúdio, asi 35 m², 2 manikérky + 4 klientky."

**Bot:**
> Pre nechtové štúdio s klientelou sediacou 30–60 min odporúčam komerčný rad (CAC alebo RAV), nie nástennú RAC. Dôvod: rezidenčné jednotky fúkajú lokalizovane (diskomfort pod prúdením), filtre nezvládajú piliny + acetón v dlhodobej prevádzke.
>
> Navrhujem:
>
> 1. **Samsung WindFree 1-Way kazeta AC035RN1DKG/EU** + panel PC1NWFMAN — WindFree režim (bez prievanu na klientky).
> 2. **Toshiba RAV 60×60 slim RAV-HM401MUTP-E** + panel RBC-UM21P-E + ovládač RBC-ASCU32Y-E — vstavané Plazma + UltraPure (chemické výpary).
>
> Pripravím cenovú ponuku obidvoch variantov. Máte podhľad pre kazety, alebo treba podstropnú?

### 6. NEROB

- ❌ SEIYA / AR30 / AR35 / Luzon / Cebu pre prevádzku — nedostatočný výkon pri kontinuálnej záťaži.
- ❌ „RAC je lacnejšie, dá sa to" — krátkodobá úspora, dlhodobá reklamácia.
- ❌ Pre serverovňu deliť záťaž na 2× polovičné jednotky — pri zlyhaní zostane 50 % kapacity.
- ❌ **NIKDY multi-split pre serverovňu** — ani FJM, ani RAV multi, ani Twin/Triple/Double-Twin/DPM, ani 2× indoor na 1× outdoor. Zdieľaný okruh = iluzórna redundancia.
- ❌ Nástennú klimu nad sedacie miesto klienta (kaderníctvo, manikúra, ambulancia) — fúka do hlavy. Preferuj kazety/podstropné.
- ❌ Zabudnúť na filtre v zdravotníckych/kozmetických priestoroch — Plazma, Air Purification, UltraPure = silný argument.
- ❌ Uvádzať rezidenčný cenník pre komerčný projekt — komerčný set je drahší, ak skryješ a predajca to dohovorí, zákazník sa cíti oklamaný.

### 7. Súvisiace pravidlá

- [[brand-specificke-funkcie-neplietat]] — Server-room funkcia iba Toshiba RAV; Air Purification iba Samsung CAC.
- [[multi-split-pravidla]] — Kazetové CAC/RAV majú obmedzenia kombinácií; použí Twin/Triple kit pre identické dvojice.
- [[discovery-pred-konkretnou-ponukou]] — Aj komerčný dotaz potrebuje discovery.
- [[kazety-vyzaduju-panel]] — CAC/RAV kazety vždy s dekoračným panelom + ovládačom v cene.
- [[dimenzovanie-kapacity]] — Komerčné priestory predimenzovať o 15–25 % oproti 1 kW / 10 m².
