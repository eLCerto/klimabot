---
name: aplikacia-rabatov-zo-discounts-json
description: Každú sumu v € (cenu, zľavu, súčet, DPH, porovnanie s rozpočtom, montáž, recyklačný poplatok) vypočíta nástroj quote; bot mu posiela iba model kódy a počty kusov a nikdy nepíše sumu, ktorú quote nevrátil.
type: feedback
---

`quote` je jediný zdroj akejkoľvek sumy v € pre zákazníka. Bot mu posiela **iba model kódy a počty kusov** — katalógovú cenu, kategóriu zľavy, segment, akciu, súčet, DPH, porovnanie s rozpočtom, orientačnú montáž aj recyklačný poplatok dohľadá a vypočíta kód. Validator porovná každú sumu v odpovedi s výstupmi `quote` a so správami zákazníka; sumu, ktorá odtiaľ nepochádza, zamietne ešte pred zobrazením: odpoveď sa vygeneruje znova, a ak suma ostane, server vetu s ňou zákazníkovi nezobrazí. Ceny z výsledkov `search_knowledge` alebo `lookup_product` sa nerátajú — sú to katalógové ceny pred zľavou.

**Why:** V reálnej session bot pred volaním nástroja napísal vlastnú „zľavnenú" cenu s vlnovkou — vymyslenú zľavu, hoci skutočná bola 0 %. Inokedy napísal, že ponuka nad rozpočtom je „pod hranicou rozpočtu". Pôvodný nástroj síce počítal zľavu v kóde, ale katalógovú cenu doň posielal model — chyba mohla vzniknúť už na vstupe. Teraz model s cenou ako vstupom vôbec nepracuje.

**How to apply:**

### Workflow

1. Vyber model(y) cez `search_knowledge` / `lookup_product` (over rad podľa [[model-code-verifikacia-po-lookup]]).
2. Zavolaj `quote`:
   - **Single-split set:** vnútorná **aj** vonkajšia jednotka → tool ich spáruje na setovú cenu. Samostatný kód zo setu tool odmietne.
   - **Multi-split:** vonkajšia + všetky vnútorné jednotky (rovnaký kód viackrát = `qty`). Tool sám overí kompatibilitu; nekompatibilná zostava vráti chybu.
   - **Komerčné (CAC / RAV):** vnútorná + vonkajšia; pri kazete pridaj kód dekoračného panela ([[kazety-vyzaduju-dekoracny-panel]]).
   - **Príslušenstvo** (ovládač, filter, Wi-Fi modul): pridaj jeho kód do tej istej ponuky.
   - `segment` iba ak ho zákazník explicitne uviedol (tabuľka nižšie), `budget_eur` ak povedal rozpočet, `promotion_code` ak ho spomenul.
3. Ak `quote` vráti chybu (neznámy kód, kód zo setu bez páru, viac cien podľa použitia, nekompatibilita, segment s overením), oprav položky podľa správy a zavolaj znova.
4. Do odpovede prepíš **presne** čísla z výstupu: `unit_catalog_price_eur`, `discount_pct`, `unit_discount_eur`, `unit_price_eur`, `unit_price_with_DPH_23pct_eur`, `total_eur`, `DPH_23pct_eur`, `total_with_DPH_23pct_eur`, `budget.status`, `budget.over_budget_by_eur`, `recycling_fee_per_unit`, `comparison_with_earlier_quotes`. Cenu montáže neuvádzaj — určí ju projektový manažér po obhliadke. Nič nezaokrúhľuj na „cca", nič nedopočítavaj.
5. Dva varianty (napr. 2× single-split vs. multi-split) = **dve** volania `quote`, každý variant celý v jednom volaní (dve rovnaké sady = jedna položka s `qty: 2`). Uveď obe sumy; ktorý je lacnejší a o koľko, je v `comparison_with_earlier_quotes`.

### Zobrazenie

> **SHORAI CURVE White set 10** (RAS-B10P2KVSG-E + RAS-10P2AVSG-E):
> - Katalógová cena: **`unit_catalog_price_eur` € bez DPH a recyklačných poplatkov**
> - Zľava: `discount_pct` %
> - **Vaša cena: `unit_price_eur` € bez DPH** (`unit_price_with_DPH_23pct_eur` € s DPH)

Ak je zľava 0 %, riadok so zľavou vynechaj.

### Zľava podľa kategórie

Zľava závisí iba od kategórie produktu (single-split set, multi-split vonkajšia/vnútorná, komerčná vonkajšia/vnútorná, panely, ovládače, príslušenstvo) a je **rovnaká pre Samsung aj Toshiba**. Výšku určuje `discounts.json`; bot ju nepozná vopred a nesľubuje ju pred volaním `quote`.

### Segmenty

Aplikuj **len** ak zákazník explicitne identifikuje segment. Výšku príplatkovej zľavy určuje `discounts.json`, nie bot.

| Segment | Trigger | V chate |
|---|---|---|
| retail_B2C (default) | žiadny | áno |
| B2B_firma | „máme firmu", „IČO", „s.r.o." | áno |
| partner_dealer | „sme dealer" | **nie** — `quote` ho odmietne; overí predajca |
| instalator_certifikovany | „som inštalatér" | **nie** — overí predajca |
| velkoobchodny_odber | „5+ ks", „developerský projekt" | **nie** — overí predajca |

Pre segmenty s overením naceň ako retail_B2C (alebo B2B_firma) a povedz: *„Pre dealer cenu vás prepojím s naším predajcom — overí váš zmluvný status."* → `request_human_handoff`.

### Žiadna „skrytá rezerva"

Samuel Malíšek Klimabot NEAPLIKUJE extra zľavu na požiadanie. Strop = to, čo vráti `quote`. Ak zákazník zjednáva nad tento rámec, slušne odmietni a navrhni lacnejší model alebo handoff na predajcu.

### NEROB

- ❌ Napísať akúkoľvek sumu v € (cenu, zľavu, súčet, DPH, rozdiel, úsporu, montáž, poplatok), ktorú nevrátil `quote` alebo nenapísal zákazník.
- ❌ Odhadovať („~X €", „cca X €", „okolo X €") alebo prepočítavať („2 × X = …").
- ❌ Prepísať cenu z výsledkov vyhľadávania alebo z `lookup_product` — vždy najprv `quote`.
- ❌ Implikovať segment B2B/dealer bez explicitnej zmienky zákazníka.
- ❌ Sľúbiť zľavu na montáž alebo recyklačné poplatky.

### Súvisiace pravidlá

- [[cena-dph-a-recyklacne-poplatky]] — prvá citácia ceny vždy uvedie aj recyklačné poplatky.
- [[matematicka-kontrola-ceny-a-rozpoctu]] — stav rozpočtu ber z `budget.status` vo výstupe `quote`.
- [[montaz-zaruka-servis-pravidla]] — cenu montáže bot neuvádza; určí ju projektový manažér po obhliadke.
- [[handoff-zapis-z-rozhovoru-pre-pm]] — handoff Markdown preberá ceny priamo z výstupov `quote`.
