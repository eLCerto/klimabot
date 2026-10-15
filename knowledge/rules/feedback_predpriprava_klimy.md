---
name: zistit-predpripravu-pred-ponukou
description: V discovery zisti predprípravu (medené potrubie + elektrika + kondenzát + otvor), ale NIE prvá otázka. Ak ju má Samuel Malíšek Klimabot, žiadna obhliadka. Ak iný subjekt, obhliadka. Ak nemá, kompletná inštalácia.
type: feedback
---

Predprípravu zisti **v rámci discovery**, ale **až po m² + použití + 1–3 modelových návrhoch s cenami**. Predpríprava výrazne mení rozsah inštalačných prác, ale zákazníka pred poradenstvom by zmiatla. Cenu montáže bot neuvádza ani pri predpríprave — určí ju projektový manažér po obhliadke ([[montaz-zaruka-servis-pravidla]]).

**Zákazník stavia alebo rekonštruuje** („stavíme chatu", „robíme rekonštrukciu", „novostavba"): práve vtedy je čas na predprípravu. Ponúkni ju sám — keď ju Samuel Malíšek Klimabot urobí počas stavby, finálna montáž je jednoduchšia a netreba sekať do hotových stien.

**Poradie v discovery:**
1. Typ priestoru, m² (alebo chladiaci výkon pre serverovňu)
2. Použitie, počet miestností, špecifické požiadavky
3. Modelové návrhy s cenami
4. **Až teraz predpríprava**
5. Kontakty + GDPR + `capture_lead`

Ak položíš predprípravu ako 1.–2. otázku, **toto pravidlo si porušil**.

**Why:**
- **Samuel Malíšek Klimabot predpríprava** → poznáme trasu, dimenziu CU, elektriku, otvor. Garantujeme kompatibilitu, žiadna obhliadka, plná zodpovednosť po inštalácii. Ostáva iba finálna inštalácia; jej cenu určí projektový manažér.
- **Iný subjekt** → nepoznáme detaily (riziko: zlá dimenzia CU, podpriemerná izolácia, chýbajúci sifón). Potrebná **bezplatná obhliadka** pred ponukou.
- **Nemá predprípravu** → kompletná inštalácia (potrubie, otvor, elektrika, kondenzát) + obhliadka; cenu určí projektový manažér.

**How to apply:**

### 1. Otázka

> „Máte už spravenú **predprípravu** na klimatizáciu? Teda či sú v mieste inštalácie pripravené:
> - **medené potrubie** medzi vnútornou a vonkajšou jednotkou,
> - **elektrická prípojka** pri obidvoch jednotkách,
> - **odvod kondenzátu**,
> - **otvor cez stenu** pre prestup potrubia."

### 2. Ak zákazník nevie čo je predpríprava

Stručne vysvetli (5 bodov):
1. **Medené chladivové potrubie** (predizolovaná dvojica) z vnútornej k vonkajšej — v stene/podhľade.
2. **Elektrický prívod** pre obe jednotky (CYKY 3×2,5 alebo 3×1,5) + istič.
3. **Odvod kondenzátu** (sifón do odpadu alebo trubka cez stenu).
4. **Otvor cez vonkajšiu stenu** Ø 50–70 mm.

Doplň: „Ak predpríprava hotová nie je, nevadí — urobíme kompletnú inštaláciu." Cenu montáže neuvádzaj — určí ju projektový manažér po bezplatnej obhliadke.

### 3. Doplňujúca otázka ak ju má

> „Robila predprípravu **Samuel Malíšek Klimabot**, alebo niekto iný (inštalatér, staviteľ, developer)?"

**Ak Samuel Malíšek Klimabot:**
- `update_customer_state({"updates": {"predpriprava": "áno", "predpriprava_kto": "Samuel Malíšek Klimabot", "predpriprava_obhliadka_potrebna": false}})`
- Pokračuj k výberu modelu. V ponuke: „Pri vašej predpríprave od Samuel Malíšek Klimabot ostáva iba finálna inštalácia; jej cenu potvrdí projektový manažér."

**Ak iný subjekt:**
- `update_customer_state({"updates": {"predpriprava": "áno", "predpriprava_kto": "iny_subjekt", "predpriprava_obhliadka_potrebna": true}})` (kto ju robil, zapíš do `notes`)
- „Pretože predprípravu robil iný subjekt, potrebujeme bezplatnú obhliadku (asi 30 min) — overíme dimenziu CU, izoláciu a elektriku, aby sme garantovali záruku. Môžem to teraz odovzdať predajcovi cez `request_human_handoff`?"

**Ak nemá:**
- `update_customer_state({"updates": {"predpriprava": "nie", "predpriprava_obhliadka_potrebna": true}})`
- V ponuke povedz, že montáž bude kompletná a jej cenu určí projektový manažér po obhliadke. Materiál (potrubie, otvor, elektrika, kondenzát) nerozpočítavaj.

### 4. Trigger frázy zákazníka

- „mám natiahnuté potrubie" / „pri rekonštrukcii sme nechali rúru cez stenu" / „čaká to len na osadenie" → existuje, opýtaj sa kto robil.
- „neviem o čom hovoríte" / „prvýkrát kupujem klimu" → vysvetli (sekcia 2).
- „developer to spravil" / „v novostavbe sme dali vyviesť" → spýtaj sa na detaily, pravdepodobne iný subjekt → obhliadka.

### 5. Príklad

Po základných discovery otázkach a prezentácii modelov:

**Bot:** „Ešte jedna otázka pre finálnu kalkuláciu — máte spravenú predprípravu? Teda natiahnuté medené trubky, elektrika a odvod kondenzátu, alebo to bude súčasť inštalácie?"

**Zákazník:** „Áno, mám to z rekonštrukcie."

**Bot:** „Skvelé. Robila predprípravu **Samuel Malíšek Klimabot**, alebo niekto iný?"

**Zákazník:** „Stavebná firma."

**Bot:** „Rozumiem. Pre takéto prípady robíme bezplatnú obhliadku (asi 30 min) — overíme priemer potrubia, izoláciu a elektrickú prípojku, aby sme garantovali záruku. Ak chcete, napíšte mi meno, telefón, e-mail a obec — projektový manažér vás potom kontaktuje."

### 6. NEROB

- ❌ Pýtať sa na predprípravu v prvej alebo druhej otázke — stratíš pozornosť pred zistením potrieb.
- ❌ Predpokladať že zákazník vie čo je predpríprava — ak neodpovie jasne, vysvetli.
- ❌ Robiť záväznú ponuku inštalácie ak predprípravu robil iný subjekt a nebola obhliadka — ponúkni handoff alebo „cena podlieha obhliadke".
- ❌ Zabúdať volať `update_customer_state` — bez záznamu sa fakt stratí v ďalšom turn-e.
- ❌ Pýtať „a robili to vaši?" po tom, čo zákazník povedal „Samuel Malíšek Klimabot" — pôsobí ako že nečítaš.

### 7. Súvisiace pravidlá

- [[discovery-pred-konkretnou-ponukou]] — predpríprava patrí do discovery, ale **nie prvá**.
- [[montaz-zaruka-servis]] — cena setu nezahŕňa montáž; predpríprava ovplyvní rozsah.
- [[umiestnenie-vonkajsej-jednotky]] — umiestnenie a konzoly vonkajšej jednotky posúdi PM pri obhliadke; predpríprava sa týka vnútornej trasy.
