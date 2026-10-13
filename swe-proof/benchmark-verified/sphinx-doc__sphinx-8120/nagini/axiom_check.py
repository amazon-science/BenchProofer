#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8120.

There are NO consumed @ContractOnly axioms in model.py. The single kind-A
obligation is an A-REFERENCE: model.py's deep model `resolved` (the first-wins
precedence fold over the ordered source list) must equal the REAL behaviour of
the standard-library gettext catalog merge that the changed code relies on.

The real mechanism (verbatim from the changed code's callee, sphinx.locale.init):

    translator = None
    for dir_ in locale_dirs:
        trans = gettext.translation(catalog, localedir=dir_, languages=...)
        if translator is None:
            translator = trans            # first found -> primary
        else:
            translator.add_fallback(trans)  # the rest -> fallback chain (in order)
    ...
    translator.gettext(message)

`gettext.*Translations.gettext` returns the primary catalog's entry if present,
otherwise descends the fallback chain in order (CPython
Lib/gettext.py: GNUTranslations.gettext / NullTranslations.add_fallback). Hence
the resolved translation of a message is the one from the FIRST source, in the
order the sources were added, that has an entry for it -- exactly model.py's
`resolved`. This script builds REAL gettext translation objects (in-memory
catalogs, no .mo files needed -- the merge/lookup logic under test is identical),
chains them with the real `add_fallback`, and asserts the real
`merged.gettext(message)` equals the model's first-wins fold over the same
ordered sources, on boundary cases and randomized fuzz, including the decisive
sphinx scenario (default ++ project ++ bundled, with project overriding bundled).

Imports only the Python standard library (`gettext`), the very module the
changed code merges/looks up through. Exit 0 iff every observation is sound.
"""
import gettext
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

NO_TEXT = 0  # model.py NO_TEXT(): the "untranslated" sentinel


def model_resolved(defines, tr):
    """Reference of model.py's `resolved`: text of the FIRST source (in order)
    that provides one, else NO_TEXT. `defines`/`tr` are aligned lists."""
    for d, t in zip(defines, tr):
        if d:
            return t
    return NO_TEXT


def model_init_translation(system_defines, system_tr, user_defines, user_tr,
                           builtin_defines, builtin_tr, message):
    """Reference of model.py's `init_translation`: assemble the ordered source
    list [default] ++ project ++ bundled, resolve first-wins, fall back to the
    untranslated message when nothing provides."""
    defines = [system_defines] + list(user_defines) + [builtin_defines]
    tr = [system_tr] + list(user_tr) + [builtin_tr]
    res = model_resolved(defines, tr)
    if res == NO_TEXT:
        res = message
    return res


# --- the REAL gettext merge/lookup (the callee the changed code uses) --------

class _Cat(gettext.NullTranslations):
    """A real gettext translations object backed by an in-memory catalog.
    Uses the genuine NullTranslations.add_fallback chaining; overrides only the
    per-catalog lookup, exactly as GNUTranslations.gettext does (entry present
    -> return it; else descend the real fallback chain)."""
    def __init__(self, catalog):
        super().__init__()
        self._catalog = dict(catalog)

    def gettext(self, message):
        if message in self._catalog:
            return self._catalog[message]
        if self._fallback:
            return self._fallback.gettext(message)
        return message


def real_resolve(sources, message):
    """Merge `sources` (each a dict message->text, in order, None meaning "this
    source provides nothing / was skipped") with the REAL gettext add_fallback
    chain -- exactly like sphinx.locale.init -- and look `message` up."""
    translator = None
    for cat in sources:
        if cat is None:
            continue  # gettext.translation raised for this dir -> skipped
        trans = _Cat(cat)
        if translator is None:
            translator = trans
        else:
            translator.add_fallback(trans)
    if translator is None:
        translator = gettext.NullTranslations()
    return translator.gettext(message)


# --- translation-code <-> text bijection for cross-checking ------------------

def encode(text, mapping):
    """Map a real translation string to its model int code (>=1), or NO_TEXT."""
    if text is None:
        return NO_TEXT
    return mapping[text]


def check_case(message_text, source_specs):
    """`source_specs`: ordered list of dicts {message_text: translation_text}
    or None. Assert the REAL merged gettext lookup of `message_text` equals the
    model's first-wins fold over the same ordered sources (mapped to codes)."""
    # Build a code bijection: NO_TEXT=0; the message itself and every distinct
    # translation get distinct codes >= 1.
    texts = [message_text]
    for spec in source_specs:
        if spec:
            for v in spec.values():
                if v not in texts:
                    texts.append(v)
    mapping = {t: i + 1 for i, t in enumerate(texts)}
    message_code = mapping[message_text]

    # Real side.
    real_text = real_resolve(source_specs, message_text)
    real_code = mapping.get(real_text, None)
    assert real_code is not None, (
        "real gettext produced an unexpected text %r" % (real_text,))

    # Model side: defines/tr per source for THIS message.
    defines = []
    tr = []
    for spec in source_specs:
        if spec and message_text in spec:
            defines.append(True)
            tr.append(mapping[spec[message_text]])
        else:
            defines.append(False)
            tr.append(NO_TEXT)
    model_res = model_resolved(defines, tr)
    if model_res == NO_TEXT:
        model_res = message_code

    assert real_code == model_res, (
        "first-wins precedence mismatch on message %r over sources %r: "
        "real gettext -> %r (code %d), model -> code %d"
        % (message_text, source_specs, real_text, real_code, model_res))


def check_sphinx_scenario():
    """The decisive scenario: order [default(None)] ++ project ++ bundled. A
    project source overrides the message the bundled source also provides; the
    real merged catalog must return the PROJECT text (the bug returned the
    bundled text). Also checks the assembled init_translation reference."""
    msg = "Quick search"
    project = {msg: "QUICK SEARCH"}
    bundled = {msg: "Hurtig sogning", "Other": "Andet"}

    # Post-fix order: default, project, bundled -> project wins.
    fixed = real_resolve([None, project, bundled], msg)
    assert fixed == "QUICK SEARCH", (
        "post-fix order must select the project override, got %r" % (fixed,))

    # Pre-fix order: default, bundled, project -> bundled wins (the bug).
    buggy = real_resolve([None, bundled, project], msg)
    assert buggy == "Hurtig sogning", (
        "pre-fix order selects the bundled value (the bug), got %r" % (buggy,))

    # The model's init_translation reference reproduces the post-fix selection.
    # codes: message=1, project="QUICK SEARCH"=2, bundled="Hurtig sogning"=3
    out = model_init_translation(
        system_defines=False, system_tr=NO_TEXT,
        user_defines=[True], user_tr=[2],
        builtin_defines=True, builtin_tr=3,
        message=1)
    assert out == 2, ("model init_translation must select the project text "
                      "(code 2), got %d" % out)
    # And it would have selected the bundled text (3) under the buggy order:
    buggy_model = model_resolved([False, True, True], [NO_TEXT, 3, 2])
    assert buggy_model == 3, "buggy-order model sanity check failed"


def main():
    # --- decisive sphinx scenario (the F2P behaviour) ---------------------
    check_sphinx_scenario()

    # --- boundary cases over orderings & catalog contents -----------------
    M = "m"
    A, B, C = "A", "B", "C"
    boundary = [
        [],                                   # no sources -> untranslated
        [None],                               # only a skipped source
        [None, None],
        [{M: A}],                             # single provider
        [{}],                                 # single source, no entry for M
        [{M: A}, {M: B}],                     # first wins
        [{M: B}, {M: A}],                     # order matters (first wins)
        [{}, {M: A}],                         # gap then provider
        [{M: A}, {}],                         # provider then gap
        [None, {M: A}, {M: B}],               # skipped default, then two
        [None, {M: A}, {M: B}, {M: C}],       # first of three
        [{"other": A}, {M: B}],               # earlier source lacks M
        [{"other": A}],                       # nobody provides M -> untranslated
        [None, {"x": A}, {M: B}, {M: C}],     # project provides, bundled too
    ]
    for spec in boundary:
        check_case(M, spec)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(8120)
    texts = ["A", "B", "C", "D", "E"]
    for _ in range(20000):
        nsrc = rng.randint(0, 6)
        specs = []
        for _ in range(nsrc):
            r = rng.random()
            if r < 0.2:
                specs.append(None)              # skipped source
            elif r < 0.45:
                specs.append({})                # source with no entry for M
            else:
                d = {M: rng.choice(texts)}
                # sometimes add unrelated entries
                if rng.random() < 0.5:
                    d["noise"] = rng.choice(texts)
                specs.append(d)
        check_case(M, specs)

    print("G-AX OK: deep model `resolved` (first-wins precedence) == real "
          "gettext merge/lookup over %d boundary + 20000 fuzz orderings; "
          "decisive sphinx project-overrides-bundled scenario sound."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
