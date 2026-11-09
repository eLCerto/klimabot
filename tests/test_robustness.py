"""Robustness (metamorphic) tests: the same meaning in many surface forms must give the same reading.

Code, not the model, reads the facts that steer a conversation from the customer's words: the rooms and their areas,
the wishes (the lowest price, filtration, quiet, Wi-Fi), a complaint or a sale, a price question, a yes or a no to the
consent question, "choose for me". Each family below lists phrasings with the reading they must give, and the suite
multiplies them by meaning-preserving transforms: no diacritics, lower or upper case, a greeting, a polite ending,
no punctuation, extra spaces, and for areas every way of writing the unit. A transform never changes the meaning, so
any variant that reads differently is a parsing bug. No model call: the whole suite runs in seconds.

The exploratory QA of 2026-11-09 (docs/qa_exploratory_2026-11-09.md) lost a customer who typed "spalna 14" without
"m2" and filed a complaint as a sale because "vaša firma mi montovala" wasn't read; each was one phrasing nobody had
written a test for. This suite tests the phrasings in bulk.

    .venv/bin/python -m unittest tests.test_robustness -v      one subTest per failing variant
    .venv/bin/python tests/test_robustness.py --report          a table: family, variants, failures, examples
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_guards import bot  # noqa: E402  (shares its setup: temp data dirs, no mail, no network)


def _fold(s):
    return bot.fold_diacritics(s)


def _lower_first(s):
    return s[:1].lower() + s[1:]


TRANSFORMS = {
    "as written": lambda s: s,
    "no diacritics": _fold,
    "lowercase": str.lower,
    "no diacritics, lowercase": lambda s: _fold(s).lower(),
    "UPPERCASE": str.upper,
    "greeting": lambda s: "Dobrý deň, " + _lower_first(s),
    "informal greeting": lambda s: "ahoj, " + _lower_first(_fold(s)).lower(),
    "polite ending": lambda s: s.rstrip(" .!?") + ", ďakujem.",
    "no punctuation": lambda s: re.sub(r"[,.!?;:]", "", s),
    "extra spaces": lambda s: re.sub(r" ", "  ", s),
}

UNITS = ["m2", " m2", "m²", " m²", " m^2", " metrov", " štvorcových metrov", " metrov štvorcových", " m", " M2"]


# --- readers: what code makes of one customer message, in a fresh session ---

def _session(*messages):
    sess = bot.Session()
    bot.use_session(sess)
    sess.user_inputs[:] = list(messages)
    return sess


def read_areas(text):
    _session(text)
    return sorted(bot._customer_m2())


def read_wish(regex):
    def reader(text):
        _session(text)
        return bot._wished(regex, text)
    return reader


def read_complaint(text):
    _session(text)
    return bot._support_case()


def read_price_question(text):
    return bool(bot._PRICE_QUESTION_RE.search(text))


def read_consent(text):
    if bot._consent_refusal(text) or bot._consent_withdrawal(text):
        return "no"
    if bot._CONSENT_YES_RE.search(bot._CONSENT_YES_NOT_CONSENT_RE.sub(" ", text)):
        return "yes"
    return None


def read_delegation(text):
    return bool(bot._DELEGATE_RE.search(_fold(text)))


def read_size_known(text):
    """The first message names a room and its size: the conversation must not ask for the size again."""
    _session(text)
    return bot._size_known()


# --- families: (phrasing, expected reading); {u} is filled with every unit form ---

AREAS_ONE = [(f"{t}", [14.0]) for t in (
    "Spálňa má 14{u}.", "Potrebujem klímu do spálne 14{u}.", "Izba 14{u}", "Obývačka má približne 14{u}.",
    "Chcem chladiť jednu izbu, má asi 14{u}.", "Do detskej izby, 14{u}.",
)]
AREAS_TWO = [(f"{t}", [14.0, 22.0]) for t in (
    "Spálňa 14{u} a obývačka 22{u}.", "Spálňa má 14{u}, obývačka má 22{u}.", "Chcem chladiť spálňu a obývačku, 14 a 22{u}.",
    "Obývačka 22{u}, spálňa 14{u}.",
)]
AREAS_NO_UNIT = [
    ("Spálňa 14 a obývačka 22.", [14.0, 22.0]), ("spalna ma 14 a obyvacka 22", [14.0, 22.0]),
    ("Spálňa má 14.", [14.0]), ("Obývačka má asi 22, spálňa 14.", [14.0, 22.0]),
]
NOT_AREAS = [
    ("Spálňa je na 2. poschodí.", []), ("Mám 2 deti a psa.", []), ("Byt je z roku 1985.", []), ("Máme 3 izby.", []),
    ("Detská izba 10 rokov stará.", []), ("Chcem 2 klimatizácie.", []),
]

CHEAP = [(t, True) for t in (
    "Čo najlacnejšie.", "Chcem najlacnejšiu.", "Hlavne lacno.", "Nech to nie je drahé.", "Najdôležitejšia je cena.",
    "Cena je pre mňa najdôležitejšia.", "Ide mi hlavne o cenu.", "Najnižšia cena.", "Čo najnižšia cena prosím.",
    "Hľadám niečo lacné.", "Mám obmedzený rozpočet, nech je to čo najlacnejšie.",
)] + [(t, False) for t in (
    "Nechcem najlacnejšiu.", "Cena až taká dôležitá nie je.", "Peniaze neriešim.", "Lacné veci nekupujem.",
)]
FILTRATION = [(t, True) for t in (
    "Syn má alergiu na prach.", "Som alergik.", "Dcéra má astmu.", "Potrebujem čistenie vzduchu.",
    "Dôležitá je dobrá filtrácia.", "Chcem kvalitný filter.", "Hlavne nech čistí vzduch.", "Máme problém s prachom.",
    "Záleží mi na čistom vzduchu.",
)] + [(t, False) for t in ("Nie som alergik.", "Filtrácia ma nezaujíma.")]
QUIET = [(t, True) for t in (
    "Hlavne nech je tichá.", "Potrebujem tichú klímu.", "Nech nehučí.", "Aby to v noci nehučalo.", "Dôležitý je tichý chod.",
    "Nízka hlučnosť je pre mňa dôležitá.", "Aby nebola hlučná.", "Koľko má decibelov? Musí byť tichá.",
)]
WIFI = [(t, True) for t in (
    "Chcem ovládanie z mobilu.", "Musí mať Wi-Fi.", "Aby som ju mohol zapnúť cez aplikáciu.", "Ovládanie cez wifi.",
    "Chcem ju ovládať z telefónu.", "Smart ovládanie cez mobil.",
)] + [(t, False) for t in ("Wi-Fi nepotrebujem.", "Neriešim wifi.")]

COMPLAINT = [(t, True) for t in (
    "Klimatizácia, ktorú ste mi namontovali, nechladí.", "Vaša firma mi minulé leto montovala klímu a teraz z nej kvapká voda.",
    "Chcem reklamovať klimatizáciu.", "Mám reklamáciu.", "Kúpil som u vás klímu a nefunguje.",
    "Váš technik mi ju inštaloval a teraz tečie.", "Už som to raz hlásil a nikto sa neozval.",
    "Klíma od vás robí hluk, chcem to riešiť reklamáciou.", "Montovali ste mi klímu a nefunguje.",
)]
SALE = [(t, False) for t in (
    "Stará klíma nefunguje, chcem novú.", "Videl som vašu reklamu, chcem klímu do spálne.", "Chcem klímu do spálne 14 m2.",
    "Vaša firma má dobré recenzie, koľko stojí klíma?", "Chceme novú klimatizáciu od vás.",
)]
PRICE_QUESTION = [(t, True) for t in (
    "Koľko to stojí?", "Aká je cena?", "Koľko by stála?", "Za koľko?", "Čo by to stálo?", "Koľko to vyjde?",
    "Koľko zaplatím?", "Mám rozpočet 1500 eur, dá sa to?", "Zmestím sa do 1000 eur?", "Pošlite mi cenu.",
)]
CONSENT = [(t, "yes") for t in (
    "Áno, súhlasím.", "Súhlasím.", "Áno súhlasím so spracovaním.", "Áno, súhlasím 🙂", "Súhlasím s tým.",
)] + [(t, "no") for t in (
    "Nie, nesúhlasím.", "Nesúhlasím.", "Kontakt vám nedám.", "Nechcem, aby ste ukladali moje údaje.",
)] + [(t, None) for t in ("Súhlasím s cenou.", "OK.", "Beriem.", "Dobre, môžete.")]
DELEGATION = [(t, True) for t in (
    "Vyberte mi.", "Vyber mi ty.", "Čo by ste odporučili?", "Ktorú odporúčate?", "Je mi to jedno, vyberte vy.",
    "Nechám to na vás.", "Rozhodnite za mňa.", "Čo by ste zobrali vy?", "Ktorá je pre nás lepšia? Vyberte nám.",
)]
SIZE_KNOWN = [(t, True) for t in (
    "Chcem klímu do spálne, má 14{u}.", "Spálňa 14{u}, koľko to stojí?", "Obývačka 25{u}.",
)]

FAMILIES = {
    # name: (reader, cases, transforms, unit forms or None)
    "areas, one room": (read_areas, AREAS_ONE, TRANSFORMS, UNITS),
    "areas, two rooms": (read_areas, AREAS_TWO, TRANSFORMS, UNITS),
    "areas, no unit": (read_areas, AREAS_NO_UNIT, TRANSFORMS, None),
    "not an area": (read_areas, NOT_AREAS, TRANSFORMS, None),
    "size known (first message)": (read_size_known, SIZE_KNOWN, TRANSFORMS, UNITS),
    "wish: lowest price": (read_wish(bot._CHEAP_WISH_RE), CHEAP, TRANSFORMS, None),
    "wish: filtration": (read_wish(bot._ALLERGY_RE), FILTRATION, TRANSFORMS, None),
    "wish: quiet": (read_wish(bot._QUIET_WISH_RE), QUIET, TRANSFORMS, None),
    "wish: Wi-Fi": (read_wish(bot._WIFI_WANTED_FOLDED_RE), WIFI, TRANSFORMS, None),
    "complaint": (read_complaint, COMPLAINT, TRANSFORMS, None),
    "sale, not a complaint": (read_complaint, SALE, TRANSFORMS, None),
    "price question": (read_price_question, PRICE_QUESTION, TRANSFORMS, None),
    "consent answer": (read_consent, CONSENT, TRANSFORMS, None),
    "choose for me": (read_delegation, DELEGATION, TRANSFORMS, None),
}


def variants(cases, transforms, units):
    """(base phrasing, variant, transform name, expected) for every combination."""
    for base, expected in cases:
        for unit in (units if units and "{u}" in base else [None]):
            text = base.replace("{u}", unit) if unit is not None else base
            for name, transform in transforms.items():
                yield base, transform(text), f"{name}" + (f", unit '{unit.strip()}'" if unit is not None else ""), expected


def run_family(name):
    reader, cases, transforms, units = FAMILIES[name]
    results = []
    for base, text, how, expected in variants(cases, transforms, units):
        got = reader(text)
        results.append((base, text, how, expected, got))
    return results


class RobustnessTests(unittest.TestCase):
    """One test per family; each failing variant is its own subTest, with the phrasing and the transform."""

    def check(self, name):
        for base, text, how, expected, got in run_family(name):
            with self.subTest(family=name, variant=text, transform=how):
                self.assertEqual(got, expected, f"{text!r} ({how}) read as {got!r}, expected {expected!r}")


def _add_tests():
    for name in FAMILIES:
        slug = re.sub(r"\W+", "_", name).strip("_").lower()
        setattr(RobustnessTests, f"test_{slug}", lambda self, n=name: self.check(n))


_add_tests()


def report():
    """A table for the README: per family the variants, the failures and up to three failing phrasings."""
    total = failed = 0
    print("| family | variants | failures | e.g. |\n|---|---|---|---|")
    for name in FAMILIES:
        results = run_family(name)
        bad = [r for r in results if r[3] != r[4]]
        total += len(results)
        failed += len(bad)
        bases = list(dict.fromkeys(f"{b!r} ({how.split(',')[0]})" for b, _, how, _, _ in bad))
        print(f"| {name} | {len(results)} | {len(bad)} | {'; '.join(bases[:3])} |")
    print(f"\n{total} variants, {failed} failures")
    return failed


if __name__ == "__main__":
    if "--report" in sys.argv:
        sys.exit(1 if report() else 0)
    unittest.main()
