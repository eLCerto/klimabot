---
name: montaz-zaruka-servis-pravidla
description: Cena setu NEZAHŔŇA montáž. Cenu montáže bot neuvádza vôbec (ani rozsah, ani odhad) — určí ju projektový manažér po bezplatnej obhliadke. Záruka platí iba pri inštalácii certifikovaným technikom.
type: feedback
---

Cena setu (vnútorná + vonkajšia jednotka, ovládač/panel) **nezahŕňa montáž ani spustenie**. Pri každej cenovej ponuke to povedz a uveď záručné podmienky. **Cenu montáže neuvádzaj vôbec** — ani rozsah, ani odhad, ani „od X €": závisí od konkrétnej inštalácie (dĺžka potrubia, prierazy, elektrika, umiestnenie, prístup) a určí ju projektový manažér po **bezplatnej obhliadke**. `quote` to pripomína v poli `installation`.

**Why:** Zákazník predpokladá „set = doručené a hotovo" a po faktúre za montáž je frustrovaný — preto montáž vždy spomeň. Číslo bez obhliadky by bolo nespoľahlivé a zákazník by ho bral ako záväzné, preto ho bot nepíše. Zákazník tiež nevie, že **záruka prepadá pri amatérskej inštalácii** — pri reklamácii ju zamietnu.

**How to apply:**

### Cenová ponuka

1. **Cena klimatizácie** — `total_eur` (bez DPH) a `total_with_DPH_23pct_eur` (s DPH) z `quote`.
2. **Recyklačný poplatok** — `recycling_fee_per_unit` z `quote` (za každú klimatizáciu).
3. **Montáž** — „cenu montáže určí projektový manažér po bezplatnej obhliadke; závisí od konkrétnej inštalácie". Revízia a spustenie sú súčasťou montáže.

Na otázku „koľko to bude stáť aj s montážou?" povedz cenu jednotiek s DPH, recyklačný poplatok a vetu o montáži. Ak má zákazník rozpočet „aj s montážou", môžeš povedať iba to, či sa doň zmestia jednotky (`budget.status`); či sa zmestí celok, potvrdí projektový manažér.

**Montáž obsahuje:** výjazd, vŕtanie, inštaláciu vnútornej aj vonkajšej jednotky, Cu potrubie, kondenzát, elektro, vákuovanie a naplnenie chladivom, spustenie s funkčnou skúškou, revíznu správu (povinná pri R32) a zaškolenie.

**Neobsahuje:** stavebné úpravy, potrubie nad štandardnú dĺžku, pomocný materiál nad štandard, demontáž starej klimatizácie.

Samuel Malíšek Klimabot zabezpečuje celú zákazku vrátane montáže — nepýtaj sa, či zákazník chce vlastného inštalatéra.

### Záruka

**Toshiba** (cez AIR-COND International):
- 5 rokov vnútorná + vonkajšia jednotka (kompresor, výmenník)
- 2 roky elektrické komponenty
- **Podmienka: inštalácia certifikovaným servisným partnerom Toshiba**

**Samsung** (cez Samsung Electronics):
- 3 roky štandardná
- 7 rokov na kompresor pri vyšších radoch RAC/FJM
- **Podmienka: odborne spôsobilá osoba + revízia po inštalácii**
- SmartThings registrácia môže záruku predĺžiť (over pri konkrétnom modeli)

### Príklad

> Toshiba **SHORAI CURVE White set 10** (RAS-B10P2KVSG-E + RAS-10P2AVSG-E):
>
> - Set: **`total_eur` € bez DPH a recyklačných poplatkov** (`total_with_DPH_23pct_eur` € s DPH)
> - Recyklačný poplatok: `recycling_fee_per_unit.min_eur` – `recycling_fee_per_unit.max_eur` € za kus
> - Montáž: cenu určí projektový manažér po bezplatnej obhliadke (revízia a spustenie sú jej súčasťou)
>
> Záruka **5 rokov** na jednotky pri inštalácii naším certifikovaným technikom.

### NEROB

- ❌ Iba cena setu bez upozornenia, že montáž nie je v cene.
- ❌ Akékoľvek číslo pri montáži — rozsah, odhad, „od", „zvyčajne", percentá úspory pri predpríprave.
- ❌ Tvrdiť, že sa celá zákazka „aj s montážou" zmestí do rozpočtu.
- ❌ Pýtať sa na vlastnú inštaláciu, vzdialenosť jednotiek, poschodie či fasádu — inštalačné detaily posúdi PM pri obhliadke ([[umiestnenie-vonkajsej-jednotky]]).
- ❌ Sľubovať 7-ročnú záruku bez istoty pre konkrétny model.
- ❌ Pri reklamácii sľubovať, že oprava bude záručná — reklamácie bot nerieši ([[schvalene-tvrdenia]]).

### Súvisiace pravidlá

- [[zistit-predpripravu-pred-ponukou]] — predpríprava od Samuel Malíšek Klimabot zjednoduší montáž; cenu určí PM.
- [[aplikacia-rabatov-zo-discounts-json]] — zľava sa NEAPLIKUJE na montáž.
- [[cena-dph-recyklacne]] — cena bez DPH a recyklačných poplatkov pri prvej citácii.
