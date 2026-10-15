# Cenník montážneho príslušenstva Samuel Malíšek Klimabot – prehľad

Zdroj: FIKTÍVNE CENY – generované vzorcom (výkon × rad × typ jednotky); štruktúra, rady a parametre podľa verejných katalógov výrobcov
Platnosť: **od 1.5.2026 do odvolania**
Ceny: **bez DPH a bez zľavy** (rabatová politika `discounts.json` sa na montáž **NEAPLIKUJE** — je to fixný nákladový cenník).

## Štruktúra cenníka

Hlavný súbor: [cennik.json](cennik.json) — obsahuje všetky položky organizované do týchto sekcií:

### Chladivový okruh
- **predizolovane_medene_potrubie** — jednoduché aj duálne CU potrubie (1/4 až 7/8) s izoláciou (PE alebo silver/UV-odolná)
- **neizolovane_medene_tyce** — tvrdé Cu rúry 28 / 35 / 42 mm
- **medene_tvarovky** — kolená 90° (5090), nátrubky (5270), oblúky 90° (5002A) a 45° (5041)
- **gulove_ventily** — GBC (bez servisu), SBV (so servisným ventilom) 6-42 mm
- **medene_prislusenstvo** — servisné ventily, tesnenia, krytky, spájka L-Ag
- **sady_na_ohybanie_potrubia** — Mastercool sady 9899-850-00, 9899-852-00
- **izolacia_k_flex** — tepelná izolácia K-flex 28/35/42 mm
- **k_flex_pasky_a_lepiace_pasky** — izolačné a tesniace pásky FA101/102, 0010NAN/NBP

### Žľaby a kanály (vedenie potrubia po stene)
- **plastove_zlaby** — 06-14 v 4 farbách (W/B/M/G)
- **prepojenie_zlabu** — flexi spojky a kompletné kity
- **spojky_kanalu** — vnútorné spojky GC
- **priechodky** — priechodky stenou PM, redukciové RM
- **rychlosvorky** — ST 6-14
- **priechodky_roh** — rohové priechodky (CM), redukcie plastové (RI), koncovky (TT), vonkajšie rohy (AE), vnútorné rohy (AI), ploché kolená (CP), T-kusy (DT)
- **naradie_zlaby** — nožnice na plastové potrubie

### Kondenzát (odvod vody)
- **listy_pre_kondenz** — žľaby a tvarovky pre kondenz 03-04
- **odvod_kondenzu_hadicky_spojky** — Y-spojky, T-kusy, kondenzné hadice 16/18/20, plastové boxy pod omietku
- **redukcie_a_spojky_tvrdej_a_flexi** — redukcie a spojky medzi rigid a flexi hadicou
- **vanicky_pod_vonkajsiu_jednotku** — drip trays 0079/0094 vrátane vyhrievaných variantov
- **sifony_a_difuzory_kondenzatu** — podomietkové sifóny, HL 138, difúzory Wipcool, VAPOBOX odparovač
- **kondenzne_cerpadla** — Sauermann (SI-10, SI-20, SI-27, SI-30, Delta Pack), Aspen (Mini Aqua, Mini Orange), Refco (VAMP-F)

### Konzoly a antivibračné komponenty
- **konzoly_stenove** — MS 117 až MS 630, MT 650 (strešná), MC 700
- **konzoly_podstavce_a_podlahove** — SP 740/930/940, DXL 450/600/1000 (antivibračné, zvýšená odolnosť), 9898 séria (antivibračné štandard)
- **antivibracne_podstavce_a_kity** — Guma 300x600, kuželové podstavce 0501SC/0505BSR, AV kity AV101/201/301 — pre inštaláciu na podlahu balkóna (vyberá PM pri obhliadke)
- **stresne_vstupy_plastove** — UT300/500

### Mosadzné tvarovky (chladivový okruh – pripojenie jednotiek)
- **mosadzne_tvarovky** — redukcie 9020-101/102/103, spojky 9020-071/072/073/074, matice 9020-061/062/063/064, inverzné konektory 9020-301/302/303/304, redukcie M-F (9020-201 až 9020-207)

### PVC NIBCO (kondenzátový/vodovodný rozvod)
- **pvc_prislusenstvo_nibco** — Rúry PVC PN 15 (1/2", 3/4", 1"), kolená 90°/45°, T-kusy, nátrubky, redukcie, lepidlo 31840, ENERGY FLEX

### Elektroinštalácia
- **elektroinstalacne_prvky** s podsekciami:
  - kable (CYKY-J, CYSY/H05VV-F, YSLCY-OZ)
  - trubky_fxp (chrániky FXP 16-32)
  - isticie_a_relevantne (LTN ističe 10B/16B/16C/20B/20C/16B-3/16C-3, Finder relé)
  - krabice_a_skrinky (rozvodné krabice, modulové skrinky)
  - listy_pvc_a_pasky_kable (PVC lišty, izolačné pásky, sťahovacie pásky)
  - vidlice_zasuvky_konektory (vidlice 250V, Wago svorky 221/222)

### Servisná chémia
- **dezinfekcne_prostriedky** — Clinex Nano Protect Silver, Sanibact, Luxedo, PolyHMG
- **cistiace_produkty_vnut_jednotka** — Clinex A/C, Universal Nano, Power Clean IN, Chinook (filtre), Evap Coil F+/+, Drizzle (kondenz hadice), Emerald Tabs (odtok), Evo Ultra
- **cistiace_produkty_vonk_jednotka** — Nano Alkaline, Power Clean Out, Alkaline Ultra
- **ochranne_obaly** — Wally In Bucket, Ceily (stropné)
- **odstranovanie_unikov_chladiva** — Extreme Ultra, External pasta, Thor, Brilliant HVAC&R (UV farbivo), Brilliant Remover, EZ-125/12 pasta
- **ine_chemikalie** — detektor kyslosti Acid-Test, neutralizátor No-Acid, Compressor+, Super Dry, Ezi Oil (olej na pertle)
- **vone_a_osviezovace** — Clinex AIR, dezinfekčné spreje 9105-016 (Vanilka/Mint/Blue Ocean/Papaya/Fresh), Fresh Home osviežovače

### Chladivo
- **chladivo** — R32, R410A, R134a, R407C (vrátane záloh za fľaše)
- ⚠️ **Predaj chladiva podlieha F-plyn certifikácii** (EÚ 517/2014). Bot **NESMIE** predávať chladivo zákazníkovi bez certifikátu – odkáž na predajcu / certifikovaného inštalatéra.

### Spojovací materiál
- **spojovaci_material** s podsekciami:
  - hlinikove_pasky_a_tesniace (700/701/702, TP0001)
  - pena_montazna_a_lepidla (PUR pena 500/750 ml, Mamut, Silikón, Tmel, chemická kotva HIT-1)
  - skrutky_do_dreva (Tex 4,2x13/16/19, 4,5x50, 5,0x50/60, 6,0x60, M8x80)
  - hmozdinky_a_kotvy (UPA 8/10/12, UH-L 8/10/12, rámové RMS 10x160 až 12x300, kotvy M8/M10 mosadzné, do sadrokartónu)
  - zavitove_tyce_a_zavesy (M8 1m/2m, ZZ8, ZL8, ZV8, ZT8)

### Gripple závesné systémy
- **gripple_zavesny_system** — UniGrip UGR22/25 (FR/SP/EF8), HF Express XP12/15 (SP/EF6)

### Tepelné čerpadlá – príslušenstvo
- **tepelne_cerpadla_prislusenstvo** — HydroTank HT-200-E, AkuTank AT-200, DuoTank DT-250-E-100, QUADROFLEX QUA 301391, ohrevné telesá (QUA 41-020001EX, 41-030001EX, ETT-M-2,0/3,0, KHT RS 3,0), 3-cestný ventil MBA132, nemrznúci ventil 90609AG06, magnetické filtre QUADRO MAG / TF1

### Servisné náradie
- **naradie_mastercool** — manometre, vákuovačky, váhy, detektory úniku, regulátor dusíka, pertlovačky, rezačky, expander sady
- **naradie_ostatne** — rýchlospojky, špeciálny kľúč na outdoor, balenia flexi hadíc pre rôzne chladivá

### Drobnosti
- **uchyty_a_drobnosti** — stenové úchyty, nosníky

## Použitie ako referencie

- **Vyhľadávanie**: `search_knowledge` cez bot zaznamená každú položku ako chunk. Aliasy v [glossary.json](glossary.json) dvíhajú BM25 recall na slovenské/české/anglické varianty (napr. „silentblok" → AV kity, „antivibračná konzola" → DXL séria).
- **Bot podľa tohto cenníka vysvetľuje, čo montáž obsahuje.** Ceny jednotlivých položiek zákazníkovi neuvádza a materiál nerozpočítava; cenu montáže neuvádza vôbec — určí ju projektový manažér po bezplatnej obhliadke. Položky nie sú v `lookup_product` ani v `quote`; presný rozpis materiálu pripraví PM po obhliadke.

## Cenník vs `discounts.json`

Položky tu uvedené **NEpodliehajú** cenovej politike v `discounts.json` (zľavy platia výhradne pre Samsung a Toshiba klimatizácie a príslušenstvo). Pre väčšie objednávky alebo dlhodobých partnerov je možná individuálna kalkulácia – ponúkni `request_human_handoff` s reason=\"kalkulacia_materialu\".

## Súvisiace pravidlá v `knowledge/rules/`

- [[zistit-predpripravu-pred-ponukou]] – stav predprípravy mení rozsah montáže; cenu určí projektový manažér.
- [[umiestnenie-vonkajsej-jednotky]] – konzoly a antivibračné podstavce vyberá PM pri obhliadke; bot ich zákazníkovi neponúka.
- [[montaz-zaruka-servis]] – cena setu zo `knowledge/samsung/` resp. `knowledge/toshiba/` **nikdy** nezahŕňa montáž ani montážne príslušenstvo z tohto cenníka.
