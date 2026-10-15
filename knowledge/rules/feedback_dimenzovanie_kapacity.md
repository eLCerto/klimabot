---
name: dimenzovanie-kapacity-podla-m2
description: 1 kW na 10 m². Z plochy priamo z tabuľky. Žiadne otázky o izolácii, strope, slnečnej strane, počte ľudí — to rieši PM pri obhliadke.
type: feedback
---

Dimenzovanie chladiaceho výkonu: **1 kW = 10 m².** Z plochy priamo veľkosť z tabuľky. Žiadne korekčné koeficienty, žiadne otázky navyše.

**Why:** Bot nie je projektový kurič. Detailné dimenzovanie cez izoláciu/slnečnú stranu/výšku stropu robí PM pri obhliadke. Botova úloha = orientačná ponuka pre 95 % rezidenčných situácií (zmestia sa do ±1 veľkosť). Pýtanie 5 technických parametrov pred prvou ponukou zákazníka odrádza („to musím merať?", „neviem akú mám izoláciu") a odkladá rozhodnutie. Lepšie: jednoduchá ponuka z m² + poznámka *„finálnu veľkosť potvrdí technik pri obhliadke"*.

**How to apply:**

### Discovery — jediná dimenzovacia otázka

**Aká je plocha miestnosti v m²?** To je všetko.

### Výber veľkosti z m²

| Plocha | Výkon kW | Toshiba | Samsung |
|---|---|---|---|
| do 15 m² | 1,5–2,0 | 05 (iba Multi) / 10 | 07 / 09 |
| 15–25 m² | 2,0–2,5 | 10 | 07 / 09 |
| 25–35 m² | 3,3–3,5 | 13 | 12 |
| 35–45 m² | 4,2–4,6 | 16 | 15 |
| 45–55 m² | 5,0 | 18 | 18 |
| 55–70 m² | 6,1 | 22 (iba SHORAI) | – |
| 65–80 m² | 6,5–7,0 | 24 | 24 |

Pri m² na hranici dvoch pásiem (napr. 24 m²) → vyber **nižšiu**. Predimenzovanie spôsobuje krátke ON/OFF cykly a horšie odvlhčovanie.

### NEPÝTAJ SA

- ❌ Izolácia — zákazník nevie kategorizovať, neopodstatňuje zmenu pri prvej ponuke.
- ❌ Výška stropu — štandard 2,5–2,7 m je v tabuľke.
- ❌ Slnečná strana / orientácia — korekcia v rámci pásma.
- ❌ Počet ľudí pravidelne v miestnosti — irelevantné pre rezidenciu.
- ❌ Región / aké zimy — všetky modely sú heat-pump.

### Atypické prípady — iba ak zákazník spomenie

- *„Podkrovie s vysokým šikmým stropom"* → rezerva 10–20 %, o veľkosť vyššie alebo obhliadka.
- *„Starý panelák bez zateplenia"* → spomeň že môže byť o veľkosť vyššia, alebo nechaj na PM.
- *„Obývačka spojená s kuchyňou"* → kuchynská záťaž = väčšia veľkosť alebo obhliadka.
- *„Juhozápadné okná po celej stene"* → o veľkosť vyššie alebo obhliadka.

**Bot reaguje na podanú informáciu, nepýta sa proaktívne.** Pri komplikácii: *„Pre takýto špecifický prípad je najlepšie, aby finálnu veľkosť potvrdil PM pri obhliadke."*

### Komerčné priestory

Samostatné pravidlo [[komercne-priestory-cac-rav]]:
- **Serverovňa** → chladiaci výkon (kW) alebo tepelný výkon serverov, nie m².
- **Gastro / kuchyňa** → m² × 1,3–1,5 alebo handoff na PM.

### Príklady

- 12 m² → pásmo „do 15 m²" → veľkosť **10** (2,5 kW).
- 30 m² → pásmo „25–35 m²" → veľkosť **13** (3,5 kW).
- 45 m² obývačka spojená s kuchyňou → pásmo „35–45 m²" → veľkosť 16, ale kuchynská záťaž → veľkosť **18** (5,0 kW) alebo handoff.

### NEROB

- ❌ Pýtať na izoláciu/strop/slnko/ľudí — discovery friction bez prínosu.
- ❌ Násobiť korekčné koeficienty (×1,3 izolácia × 1,2 juh × …) — aktuálne je výpočet **iba m² → tabuľka**.
- ❌ Predimenzovanie kvôli „bezpečnostnej rezerve" — tabuľka už vyberá vhodnú veľkosť.
- ❌ Tváriť sa ako projektový kurič — pri atypickom prípade navrhni obhliadku.
