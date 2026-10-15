---
name: matematicka-kontrola-ceny-a-rozpoctu
description: Vzťah ceny k rozpočtu („v rozpočte" / „presahuje rozpočet") ber iba z budget.status vo výstupe quote. Veta nesmie protirečiť číslam a bot nič neprepočítava.
type: feedback
---

Pred každou frázou o vzťahu *cena vs. rozpočet* pošli rozpočet do `quote` (`budget_eur`) a použi jeho výsledok. **Veta nesmie protirečiť číslam** a porovnanie nepočíta sám: použi `budget.status`. `quote` porovnáva cenu jednotiek na tom základe, ktorý zákazník použil (`budget.compared_price`): s DPH, ak nepovedal „bez DPH". Cenu montáže bot neuvádza, takže pri rozpočte „aj s montážou" vie potvrdiť iba jednotky.

**Why:** V reálnej session bot o ponuke, ktorá bola o takmer polovicu drahšia ako rozpočet, napísal *„Zostáva vám v rozpočte — je pod vašou hranicou."* Takáto chyba zhadzuje dôveru v ostatné čísla; ak unikne k objednávke, zákazník odíde s pocitom oklamania.

**How to apply:**

### Najprv nástroj

`quote` s `budget_eur` vráti `budget.status` a `budget.over_budget_by_eur` / `budget.under_budget_by_eur`. Použi presne tieto hodnoty.

| `budget.status` | Čo povedať |
|---|---|
| *v rozpočte* | „V rozpočte — zostáva rezerva `under_budget_by_eur` €." Ak rozpočet zahŕňa montáž (`budget.budget_includes_installation`): „Jednotky sa do rozpočtu zmestia; cenu montáže určí projektový manažér po obhliadke." — bez rezervy a bez tvrdenia o celku. |
| *na hranici rozpočtu* (do +5 %) | „Na hranici rozpočtu — o `over_budget_by_eur` € viac." |
| *nad rozpočtom* (do +20 %) | „O niečo presahuje rozpočet — o `over_budget_by_eur` €, je to najbližšie riešenie." |
| *výrazne nad rozpočtom* (nad +20 %) | „Výrazne presahuje rozpočet — o `over_budget_by_eur` €." + ponúkni alternatívu |

Porovnanie robí `quote` s cenou jednotiek s DPH (`budget.compared_price_eur`), iba ak zákazník povedal „bez DPH", tak bez DPH. Rozpočet pošli tak, ako ho povedal, a v odpovedi uveď aj cenu na tom istom základe.

### Alternatíva musí reálne vyriešiť požiadavku

Pred ponúknutím „lacnejšej alternatívy" over:
1. Rieši požiadavku (počet miestností, výkon, vlastnosti)?
2. Dostane zákazníka do rozpočtu? → zavolaj `quote` aj pre alternatívu s rovnakým `budget_eur` a ponúkni ju, iba ak jej `budget.status` je lepší. Ak `quote` vráti `cheaper_alternative`, začni ňou.
3. Nie je to len kozmetická redukcia bez zmyslu?

Ak neprejde, **neponúkaj**. Lepšie transparentne: *„Pre 4 miestnosti sa do tohto rozpočtu nedostaneme bez výraznej zmeny zadania. Možnosti: lacnejšie vnútorné jednotky, postupná inštalácia (najprv hlavné izby), alebo obhliadka s PM."* — sumy uveď iba z volaní `quote`.

### Špeciálne prípady

- **Rozpočet bez/s DPH**: bežný zákazník myslí cenu s DPH — `quote` porovnáva s DPH, kým zákazník nepovie „bez DPH". Uveď oba údaje z `quote`.
- **Rozpočet vrátane montáže**: povedz iba, či sa zmestia jednotky (`budget.status`), a že cenu montáže určí projektový manažér po bezplatnej obhliadke. Netvrď, že sa zmestí celok. Ak sú už samotné jednotky nad rozpočtom, povedz to jasne a ponúkni lacnejší set (`cheaper_alternative` alebo ďalší `quote`).
- **Viac variantov**: každý variant = samostatné volanie `quote` s rovnakým `budget_eur` (celý variant v jednom volaní, rovnaké sety cez `qty`). Ktorý je lacnejší a o koľko, ber z `comparison_with_earlier_quotes` — nepočítaj to sám.

### NEROB

- ❌ „V rozpočte" / „zostáva rezerva" bez `budget.status` z `quote`.
- ❌ Tvrdiť „v rozpočte", keď `budget.status` hovorí inak — najvážnejší typ chyby.
- ❌ Počítať rozdiel, percento alebo súčet sám.
- ❌ „Takmer v rozpočte" pre ponuku so statusom *výrazne nad rozpočtom*.
- ❌ Tvrdiť, že sa zákazka „aj s montážou" zmestí do rozpočtu — cenu montáže bot nepozná.
- ❌ Mlčať o rozpočte, keď je ponuka nad ním — povedz to a ponúkni lacnejší variant.

### Súvisiace pravidlá

- [[aplikacia-rabatov-zo-discounts-json]] — cenu aj porovnanie s rozpočtom vracia `quote`.
- [[discovery-pred-konkretnou-ponukou]] — rozpočet sa nepýta prvý; keď ho zákazník uvedie, prenes ho do `customer_state.budget_eur_max`.
- [[cena-dph-a-recyklacne-poplatky]] — konvencie DPH a recyklačných poplatkov.
