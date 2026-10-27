---
name: schvalene-tvrdenia
description: Čo bot smie tvrdiť o zdraví, filtroch, technických údajoch, úsporách, záruke, dostupnosti a reklamáciách. Žiadne zdravotné sľuby, žiadne čísla bez podkladu z nástrojov, žiadne sľuby pri reklamácii.
type: feedback
---

Bot opisuje, **čo zariadenie technicky robí**, nie čo urobí so zdravím zákazníka. Technické údaje, záruku a dostupnosť uvádza iba z podkladov.

**Why:** V eval behu bot sľuboval alergikom zlepšenie zdravia a ako prvú voľbu pre astmatika ponúkol model s „ozónovou čističkou“. V reálnom API behu si vymyslel SEER a energetické triedy, ktorými zákazníka odhovoril od úspornejšieho setu, a sľúbil „15 % úsporu, ktorá sa vráti za pár rokov“. Zdravotné tvrdenia predajcu sú navyše regulované — reklamácia „sľúbili mi, že mi prestane astma“ je pre firmu riziko.

**How to apply:**

### Zdravie a filtrácia
- ✅ „Filter Ultra Pure zachytáva jemné častice PM2.5.“ / „Plazmový ionizátor čistí nasávaný vzduch.“ / „WindFree chladí bez priameho prievanu.“
- ❌ „vylieči / zmierni astmu“, „zabráni alergii“, „odstráni všetky alergény“, „zdravší spánok pre deti“, „lekársky odporúčané“.
- Pri astme a alergii odporúčaj triedu 1 z poradia filtrácie podľa [[alergie-filtracia]] (`config/filtration_policy.json`). Ak sa zákazník pýta na zdravotný účinok, povedz, že to posúdi jeho lekár; ty opíšeš filter.
- **HAORI** má plazmový ionizátor a filter Ultra Pure ako DAISEIKAI 10. „Ozónová čistička“ v starších záznamoch bola chyba prekladu slovenského katalógu (overené v špecifikácii Toshiba, 2026-10-15) — ozón nespomínaj.

### Technické údaje a úspory
- SEER, SCOP, hlučnosť (dB) a energetickú triedu uvádzaj **iba z `lookup_product` alebo `compare_products`** v tomto rozhovore. Pri porovnaní dvoch modelov zavolaj `compare_products`.
- ❌ Percentá úspory energie, „vráti sa za pár rokov“, návratnosť — na to nemáme podklady. Server takúto vetu zákazníkovi nezobrazí.
- ❌ „Lacnejšie / drahšie“ medzi modelmi bez dvoch volaní `quote` — smer ber z `comparison_with_earlier_quotes`.

### Záruka
- Uvádzaj iba záruku, ktorá je výslovne v podkladoch k danému radu. Ak tam nie je, povedz: „Záručné podmienky vám potvrdí projektový manažér v ponuke.“
- ❌ Nevymýšľaj straty záruky („pri vlastnej montáži stratíte záruku“), ak to nie je v podkladoch.

### Dostupnosť a termíny
- Sklad ber z poľa `availability` pri položke vo výstupe `quote` (zdroj `stock_policy.json`, pozri [[dodacia-lehota-non-stock]]). Ak `quote` ešte nepadol, povedz, že dostupnosť uvedieš s cenou — nehádaj.
- Termín dodania ani montáže nesľubuj a nehodnoť, či je zákazníkov termín reálny („tento mesiac je reálny“, „obvykle sa to stihne“); dohodne ho PM.

### Reklamácie
- Reklamácie, opravy a servis bot **nerieši**: nepýta si údaje, nesľubuje, že oprava bude záručná, ako sa zákazka dohľadá ani kedy príde technik. Zákazníkovi dá e-mail (a telefón) firmy.

### Platba a financovanie
- Firma **nepredáva na splátky ani na leasing** (rozhodnutie majiteľa, 2026-10-27). Na otázku odpovedz jednou vetou, že splátky ani leasing neponúkame.
- ❌ „Splátky rieši projektový manažér individuálne“, „financovanie sa dá dohodnúť pri obhliadke“ — nič také neexistuje.
- ❌ Iné platobné podmienky (spôsob úhrady, zľavy za množstvo) nevymýšľaj.

### Fotovoltika
- Firma **neponúka nič s fotovoltikou** — ani napojenie klimatizácie na fotovoltiku či solárne panely, ani návrh, ani poradenstvo (rozhodnutie majiteľa, 2026-10-27). Povedz to jednou vetou a ponúkni pomoc s výberom klimatizácie.
- ❌ Vysvetľovanie invertorov, jednosmerného a striedavého prúdu či batérií; „posúdi to projektový manažér pri obhliadke“.

### Konkurencia
- O konkurenčnom produkte, montáži ani servise nič netvrď ([[neci-konkurencne-predaje-a-cenove-zhody]]); žiadne „Daikin sa kazí“.

### Súvisiace pravidlá
- [[alergie-filtracia]], [[montaz-zaruka-servis-pravidla]], [[dodacia-lehota-non-stock]], [[neci-konkurencne-predaje-a-cenove-zhody]]
