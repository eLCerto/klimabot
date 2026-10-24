---
name: priemyselne-priestory
description: Priemyselné a poľnohospodárske priestory (hala, výroba, továreň; chliev, maštaľ, farma, skleník) chatbot nerieši — žiadny návrh ani cena; kontakt na firmu alebo sa ozve projektový manažér.
type: feedback
---

Ak zákazník chce chladiť **priemyselný priestor** — výrobnú alebo skladovú halu, výrobu, továreň, závod, logistické centrum — alebo **poľnohospodársku budovu** — chliev, maštaľ, stajňu, kurín, farmu, skleník — chatbot **nenavrhuje riešenie ani nenaceňuje**. Kľúčové slová sú v `config/sizing_policy.json` (`industrial`).

**Why:** Chatbot je určený pre byty, domy a menšie prevádzky. Pri hale navrhol multi-split s výkonom odhadnutým z plochy, čo pre halu neplatí (výška, technológie, tepelné zisky výroby). Taký návrh by zákazníka zaviedol; priemyselné chladenie navrhuje projektový manažér individuálne (majiteľ, 2026-10-18). Pri chlieve pre ošípané bot vymýšľal normy plochy na zviera a raz ho nazval komerčným, raz rezidenčným priestorom; poľnohospodárske budovy (zvieratá, vlhkosť, vetranie) rieši tiež projektový manažér (majiteľ, 2026-10-24).

**How to apply:**

- Krátko povedz, že priemyselné priestory navrhuje individuálne projektový manažér.
- Ponúkni dve možnosti: kontakt na firmu (e-mail, telefón), alebo nech zákazník nechá meno a telefón či e-mail. Napíš to ako podmienku („Ak mi necháte…, projektový manažér sa vám ozve.“) — sľub bez súhlasu server zamietne. Súhlas so spracovaním údajov si vypýta server.
- Nepýtaj sa na plochu, zóny ani prevádzku, nehľadaj modely a nevolaj `quote` — server priemyselný priestor nenacení a kontakt doplní sám, ak ho vynecháš.

### Príklad

Zákazník: „Chcem chladiť priemyselnú halu.“

Bot: „Priemyselné priestory navrhuje individuálne náš projektový manažér. Napíšte nám na e-mail alebo zavolajte. Ak mi tu necháte meno a telefón či e-mail, projektový manažér sa vám ozve.“

### NEROB

- ❌ Navrhovať systém, výkon v kW ani modely pre halu.
- ❌ Pýtať sa na plochu, počet zón či prevádzku 24/7 — to zistí projektový manažér.
