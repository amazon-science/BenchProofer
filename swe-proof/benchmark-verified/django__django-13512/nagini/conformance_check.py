#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13512 (nagini).

SHADOW: the impl region of model.py `json_render_text`, copied verbatim below
with the contract calls stripped (Invariant/Assert lines removed; the
Requires/Ensures live in separate regions). The @Pure helpers `json_char` /
`json_string_body` copy over as plain functions operating on plain lists (the
PSeq shim is a plain Python list: PSeq(a, b) ~ [a, b], `+` ~ list concat,
`drop(1)` ~ slicing) and serve as an internal cross-check of the shadow.
There are no @ContractOnly callees in this bundle (the axioms region is
empty).

ORACLE: the REAL patched repo functions the model models per mapping.md 1 --
`django.forms.fields.JSONField.prepare_value` and the JSONField branch of
`django.contrib.admin.utils.display_for_field`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
modules importable. This script never applies any diff itself.

Type bridge (mapping.md 2): a text scalar `str` <-> `List[int]` of Unicode
code points (`text[k] == ord(s[k])`); the returned JSON text `str` <-> the
returned `List[int]` the same way. The shadow is fed the code-point list of
each input string and its output list is compared against the code points of
the real functions' returned text.

Input domain (the Requires): every code point of the input is printable
(>= U+0020). Generation draws only from that domain -- printable ASCII
(including the two escaped code points U+0022 and U+005C), CJK, accented
Latin/Greek, astral-plane samples, lone surrogates, and uniform random code
points in [U+0020, U+10FFFF].

>= 1e5 Requires-satisfying inputs: boundary strings (empty, quote/backslash
combos, the discriminator inputs the tests pin, per-code-point singletons
sweeping U+0020..U+2000 plus non-BMP samples) + 100000 fuzz strings.
Pinned fuzz seed: 135120. Every input is checked against prepare_value;
non-empty inputs are additionally checked against display_for_field (its
modeled branch requires a truthy value), so the number of shadow-vs-real
comparisons exceeds the input count.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random).
"""
import random
import sys

SEED = 135120
N_FUZZ = 100_000


# --- PSeq shim: pure Viper sequences as plain Python lists --------------------

def PSeq(*items):
    return list(items)


# --- pure helpers from model.py, contracts stripped, PSeq -> list -------------

def json_char(c):
    if c == 34:        # '"'  -> '\"'
        return PSeq(92, 34)
    if c == 92:        # '\'  -> '\\'
        return PSeq(92, 92)
    return PSeq(c)


def json_string_body(s):
    if len(s) == 0:
        return []
    return json_char(s[0]) + json_string_body(s[1:])


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def json_render_text(text):
    body = []  # type: List[int]
    i = len(text)
    while i > 0:
        c = text[i - 1]
        if c == 34:
            body = [92, 34] + body
        elif c == 92:
            body = [92, 92] + body
        else:
            body = [c] + body
        i = i - 1
    result = [34] + body + [34]
    return result


# --- oracle plumbing: the REAL patched repo functions --------------------------

def make_oracles():
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=True, INSTALLED_APPS=[], DATABASES={})
    import django
    django.setup()
    from django.forms.fields import JSONField as FormsJSONField
    from django.contrib.admin.utils import display_for_field
    from django.db.models import JSONField as ModelsJSONField

    form_field = FormsJSONField()
    model_field = ModelsJSONField()

    def forms_oracle(s):
        """The real forms-site rendering of a text scalar."""
        return form_field.prepare_value(s)

    def admin_oracle(s):
        """The real admin-display-site rendering of a text scalar (its
        modeled branch requires a truthy value; callers pass s != '')."""
        return display_for_field(s, model_field, '-empty-')

    return forms_oracle, admin_oracle


def _to_pts(s):
    return [ord(ch) for ch in s]


# --- differential driver --------------------------------------------------------

def check_one(forms_oracle, admin_oracle, s):
    """Diff shadow vs the real functions on one input string; return an error
    string on disagreement, else None."""
    text = _to_pts(s)
    shadow = json_render_text(text)
    # internal cross-check: the impl agrees with the pure deep model
    assert shadow == [34] + json_string_body(text) + [34]

    real_forms = forms_oracle(s)
    if shadow != _to_pts(real_forms):
        return ("DISAGREEMENT (forms site)\n"
                "  input=%r\n  shadow=%r\n  real=%r"
                % (s, shadow, real_forms))

    if s:  # the admin branch under model only fires for a truthy value
        real_admin = admin_oracle(s)
        if shadow != _to_pts(real_admin):
            return ("DISAGREEMENT (admin display site)\n"
                    "  input=%r\n  shadow=%r\n  real=%r"
                    % (s, shadow, real_admin))
    return None


def main():
    forms_oracle, admin_oracle = make_oracles()

    # --- boundary strings ----------------------------------------------------
    boundary = [
        "", '"', "\\", '""', "\\\\", '"\\"', 'a"b\\c',
        " ", "a", "foo", "abc 123 !@#", "{}", "[]",
        "你好 世界",          # CJK with a space
        "你好，世界",     # CJK with fullwidth comma
        "\U0001f600\U0001f431",               # astral / emoji
        "jaźń",                     # accented Latin
        "caf\xe9", "na\xefve",
        "你好\"\\世界",       # non-ASCII mixed with escapes
        "\x7f",                               # DEL (printable-domain edge)
        "  ",                       # JS-hostile line separators
        "\ud800", "\udfff",                   # lone surrogates (>= U+0020)
    ]
    # per-code-point singleton sweep inside the modeled domain
    boundary += [chr(c) for c in range(0x20, 0x2000)]
    boundary += [chr(c) for c in
                 [0x2400, 0x3042, 0x4e2d, 0x56fd, 0xfeff, 0xffff,
                  0x10000, 0x1d11e, 0x1f4a9, 0x10ffff]]

    checked = 0
    for s in boundary:
        err = check_one(forms_oracle, admin_oracle, s)
        if err:
            print(err)
            return 1
        checked += 1
    n_boundary = checked

    # --- randomized fuzz over the modeled domain (pinned seed) ----------------
    rng = random.Random(SEED)
    pool = (
        [chr(c) for c in range(0x20, 0x7f)] +                       # ASCII
        ['"', '\\', '"', '\\'] +                                    # escapes, upweighted
        [chr(c) for c in [0x4f60, 0x597d, 0x4e16, 0x754c, 0xff0c]] +  # CJK
        [chr(c) for c in [0xe9, 0x17a, 0x144, 0xdf, 0x3b1]] +       # Latin/Greek
        [chr(c) for c in [0x1f600, 0x1f431, 0x1f4a9]]               # astral
    )

    def rand_char():
        if rng.random() < 0.8:
            return rng.choice(pool)
        # uniform over the whole modeled domain (incl. surrogates, non-BMP)
        return chr(rng.randint(0x20, 0x10FFFF))

    for _ in range(N_FUZZ):
        n = rng.randint(0, 24)
        s = "".join(rand_char() for _ in range(n))
        err = check_one(forms_oracle, admin_oracle, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow (contract-stripped impl of json_render_text) == "
          "real patched forms prepare_value and admin display_for_field on "
          "%d inputs (%d boundary + %d fuzz, seed %d); zero disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
