"""Drive a scripted conversation through the bot end-to-end and print a
readable transcript with all validator events. Used for scenario testing.

Usage: ANTHROPIC_API_KEY=... python eval/test_scenario.py <scenario_name>
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # bot.py sits in the project root
import bot  # noqa: E402

SCENARIOS = {
    "byt_cheapest": [
        "ahoj chcem klimu do bytu",
        "30 m2, jedna izba",
        "chcem co najlacnejsie",
        "vyber mi to",
        "Peter, 0911222333, Bratislava",
        "suhlasim",
    ],
    # The live demo of 2026-10-15: 2-3 searches per message, one per series just to find codes.
    "detska_izba_alergia": [
        "Hľadám čo najtichšiu klimatizáciu do detskej izby, má 12 m².",
        "nástenná je v poriadku",
        "mam alergiu na prach, odporuc mi najlepsiu filtraciu",
        "ktora z tych najlepsich je najlacnejsia?",
    ],
    # Live demo of 2026-10-18: no search, series picked from the prompt's examples, no multi-split price.
    "dve_izby_porovnanie": [
        "potrebujem klimu do dvoch izieb",
        "aka je vyhoda multisplitu voci single?",
        "jedna izba ma 12 m2. priprav mi porovnanie kolko by stal multisplit a singlesplit",
        "15",
    ],
    # Live demo of 2026-10-18: the bot designed a multi-split for an industrial hall.
    "priemyselna_hala": [
        "ahoj",
        "chcem chladit priemyselnu halu",
        "300 m2, 4 zony a 24/7",
    ],
    # Live demo of 2026-10-19: "residential cassettes start at 5 kW", a wall unit priced as a cassette.
    "pracovna_kazeta": [
        "potrebujem klimu do pracovne, 20 m2, jedna miestnost",
        "chcem kazetovu jednotku do domacnosti, nie komercnu",
        "porovnaj cenu rezidencnej a komercnej kazetovej jednotky",
    ],
    # Live demo of 2026-10-19: a bare Toshiba outdoor sold as a console set, two brands in one quote.
    "obyvacka_parapetna": [
        "ahoj, chcem klimu do obyvacky",
        "30 m2",
        "chcem parapetnu jednotku",
    ],
    # Live demo of 2026-10-19: no feature question, three sets for three rooms, AR35 for a filter wish,
    # a stale PM brief after the switch.
    "byt_3_izby": [
        "potrebujem klimu do bytu do 3 izieb",
        "izby maju 20, 20 a 10 m2",
        "mam zaujem o kvalitny filter a wifi",
        "chcem nizsiu radu, nieco lacnejsie",
    ],
    # Live demo of 2026-10-20: features asked instead of the price, HAORI 3.5 kW for 14 m², one option.
    "spalna_14_cena": [
        "Dobrý deň, hľadám klimatizáciu do spálne, má 14 m². Koľko by stála?",
        "hladam najlepsi pomer cena vykon",
    ],
    # Live demo of 2026-10-20: "20mm2" unread, multi-split codes not found, brand and budget asked, Samsung
    # "hneď dostupný", the cheaper Wi-Fi option found only on the third ask.
    "dom_multisplit_wifi": [
        "dobr den, potreboval by som klimu do domu",
        "mam dom 10x8 metrov a chcem chladit kuchynu a obyvacku",
        "chcem multisplit, izby su rovnake - 20mm2",
        "potrebujem wifi",
        "je tam aj lacnejsia alternativa?",
    ],
    # Live demo of 2026-10-21: four rooms on 2× AJ050, "Samsung takes 2 at most", a Luzon price nobody quoted.
    # The customer's eight messages verbatim (log 2026-10-21_17-03-13_c81f96).
    "styri_izby_comfort": [
        "ahoj, chcem klimu do styroch izieb multisplit samsung comfort",
        "4 izby po 10 m2 chcem samsung comfort",
        "preco mi neponuknes jednu velku vonkajsiu jednotku?",
        "to je loz, samsung umoznuje pripojenie do 5 jednotiek",
        "chcem riesenie s jednou vonkajsou jednotkou",
        "Chcem túto ponuku: 1× Samsung – vonkajšia multi-split jednotka 8,0 kW, 4× Samsung WindFree Comfort S2 – "
        "vnútorná jednotka 2,0 kW — 5 619,13 € s DPH.",
        "Áno, súhlasím",
        "nevyplnim",
    ],
    "ambulancia_alergia": [
        "dobry den, chcem klimu do ambulancie, mam alergiu",
        "asi 40 m2, dve miestnosti",
        "Eva, 0944555666, Nitra",
        "suhlasim so spracovanim",
    ],
    "konkurencia": [
        "Mam ponuku Daikin Perfera za 1800. Co viete ponuknut?",
        "byt, 30 m2, jedna izba",
        "samsung",
        "Jan, 0900111222, Trnava, suhlasim",
    ],
    "serverovna": [
        "potrebujeme klimatizaciu do serverovne, bezi nam tam 8 serverov 24/7",
        "tepelny vykon serverov je asi 7 kW",
        "ano, mame 3-fazovu pripojku",
        "Marek, 0905111222, Bratislava",
        "suhlasim so spracovanim",
    ],
    "gdpr_refusal": [
        "dobry den, chcem klimu do bytu",
        "30 m2, jedna izba",
        "samsung najlacnejsi",
        "vyberte mi to",
        "Lucia, 0918333444, Kosice",
        "nesuhlasim s gdpr",
    ],
    "byt_premium_alergie": [
        "ahoj, mam astmu a chcem premium klimu do spalne",
        "25 m2",
        "toshiba",
        "co mi odporucas",
        "Tomas, 0911555666, Zilina, suhlasim so spracovanim osobnych udajov",
    ],
    # Customer initially wants Toshiba multi-split, then switches to Samsung
    # right at the contacts step. Tests: brand-switch handling, late-stage
    # update_customer_state, re-running check_compatibility for new outdoor,
    # capture_lead reflects FINAL choice (Samsung), not initial (Toshiba).
    "brand_switch": [
        "ahoj, chcem multisplit klimu, toshiba",
        "byt, dve izby — 20 m2 a 25 m2",
        "vyber mi to",
        "Peter, 0911222333, Bratislava — vlastne by som chcel radsej samsung",
        "suhlasim so spracovanim osobnych udajov",
    ],
}


def run_scenario(name):
    if name not in SCENARIOS:
        print(f"Unknown scenario: {name}. Available: {list(SCENARIOS)}", file=sys.stderr)
        sys.exit(1)

    bot.reset_session()
    inputs = SCENARIOS[name]
    print(f"\n{'=' * 70}\nSCENARIO: {name}\n{'=' * 70}")

    total_violations = 0
    total_regens = 0

    for user_msg in inputs:
        print(f"\n>>> USER: {user_msg}")
        bot_text = ""
        for event, data in bot.run_user_turn_streaming(user_msg):
            if event == "token":
                bot_text += data["text"]
            elif event == "tool_call":
                print(f"  [TOOL] {data['name']}({_short(data.get('input', {}))})")
            elif event == "tool_result":
                if data.get("is_error"):
                    print(f"  [TOOL-ERR] {data['name']}: {data.get('output_preview', '')[:140]}")
            elif event == "notice":
                txt = data["text"]
                if "Regenerujem" in txt or "regenerujem" in txt:
                    total_regens += 1
                if "Porušenie pravidla:" in txt:
                    total_violations += 1
                print(f"  [NOTICE] {txt[:200]}")
            elif event == "error":
                print(f"  [ERROR] {data['message'][:200]}")
            elif event == "handoff":
                print(f"  [HANDOFF written: {data['path']}]")
        if bot_text.strip():
            print(f"\n<<< BOT:\n{bot_text}")

    print(f"\n{'-' * 70}")
    print(f"Stats: violations={total_violations}, regens={total_regens}")
    print(f"Final state: {dict(bot.S().customer_state)}")


def _short(obj, max_len=80):
    import json
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= max_len else s[:max_len] + "..."


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <{'/'.join(SCENARIOS)}>", file=sys.stderr)
        sys.exit(1)
    run_scenario(sys.argv[1])
