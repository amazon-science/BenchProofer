#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14539 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped: ``trim_trailing_punct(middle, trail,
decoded_len, kept_len)`` over ``List[int]`` code points. There are no @Pure
helpers and no @ContractOnly callees in this bundle; the two integer
parameters are the length outputs of the unchanged decode/strip callees
(mapping.md section 3.1), computed here by calling those REAL callees
(stdlib ``html.unescape`` + ``str.rstrip`` with the repo's own constant).

ORACLE: the REAL patched repo object the model models per mapping.md — the
``trim_punctuation`` inner function of ``django.utils.html.urlize``. The gate
applies patch.diff to /testbed before this script runs, so the module holds
the patched code. ``trim_punctuation`` is a closure-free nested function (it
references only module globals), so it is materialized at runtime from the
patched ``urlize`` code object via ``types.FunctionType`` — no repo code is
re-typed here.

BRIDGE (mapping.md section 2): repo strings are ``str``; the model carrier is
``List[int]`` of Unicode code points via ``ord``/``chr`` — a bijection, so
generation happens over ``str`` and each call lowers/raises per the map.
The modeled block sits inside an iterated trim loop whose other steps are
untouched by the patch; the shadow drives that same unchanged scaffolding
(transcribed from the module at the pinned base commit) and delegates ONLY
the modeled block to the impl-region shadow, so a disagreement with the
oracle isolates the modeled behaviour.

INPUT DOMAIN: the model's Requires are established by construction — the two
length parameters come from the real callees (which never lengthen, per the
A-reference facts G-AX validates) and the block is entered only under the
same guard the repo uses (kept length strictly below decoded length). Every
(lead, middle, trail) str triple is therefore Requires-satisfying at each
delegated call. Generation stresses the decision boundary: encoded entities
adjacent to trailing punctuation (where the encoded and decoded lengths
diverge), all-punctuation middles, wrapped/parenthesized middles that make
the outer loop iterate, and plain text.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz triples.
Pinned fuzz seed: 214539.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import html
import json
import random
import sys
import types

SEED = 214539
N_FUZZ = 100000

# The repo's module constants that parameterize the UNCHANGED scaffolding /
# callees are imported from the patched module itself (not re-typed), so the
# shadow uses exactly the values the oracle uses.
import django.utils.html as dh

TRAILING_PUNCTUATION_CHARS = dh.TRAILING_PUNCTUATION_CHARS
WRAPPING_PUNCTUATION = dh.WRAPPING_PUNCTUATION


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def trim_trailing_punct(middle, trail, decoded_len, kept_len):
    punctuation_count = decoded_len - kept_len
    split = len(middle) - punctuation_count
    moved = middle[split:]
    new_trail = moved + trail
    new_middle = middle[:split]
    return new_middle, new_trail


# --- bridge helpers (str <-> List[int] code points) ----------------------------

def to_cp(s):
    return [ord(ch) for ch in s]


def from_cp(cp):
    return "".join(chr(c) for c in cp)


# --- shadow of the full trim loop ----------------------------------------------
# The loop and the wrapping-punctuation steps are NOT part of the modeled
# change (they are identical before and after the patch); they are transcribed
# here from the module at the pinned base commit purely as harness scaffolding
# so the shadow and the oracle can be compared at the same call boundary.
# The modeled trailing-trim block is delegated to the impl-region shadow.

def shadow_trim_punctuation(lead, middle, trail):
    trimmed_something = True
    while trimmed_something:
        trimmed_something = False
        for opening, closing in WRAPPING_PUNCTUATION:
            if middle.startswith(opening):
                middle = middle[len(opening):]
                lead += opening
                trimmed_something = True
            if (middle.endswith(closing) and
                    middle.count(closing) == middle.count(opening) + 1):
                middle = middle[:-len(closing)]
                trail = closing + trail
                trimmed_something = True
        # The unchanged callees produce the two length summaries; the guard
        # below is the repo's own branch condition, equivalent to the model's
        # Requires(kept_len < decoded_len) (mapping.md section 1).
        middle_unescaped = html.unescape(middle)
        stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
        if middle_unescaped != stripped:
            decoded_len = len(middle_unescaped)
            kept_len = len(stripped)
            new_middle_cp, new_trail_cp = trim_trailing_punct(
                to_cp(middle), to_cp(trail), decoded_len, kept_len)
            middle = from_cp(new_middle_cp)
            trail = from_cp(new_trail_cp)
            trimmed_something = True
            shadow_trim_punctuation.branch_hits += 1
    return lead, middle, trail


shadow_trim_punctuation.branch_hits = 0


# --- oracle: the real patched trim_punctuation ----------------------------------

def real_trim_punctuation():
    """Materialize the REAL patched ``trim_punctuation`` from the patched
    module's ``urlize`` code object. It is a nested function with no free
    variables (it reads only module globals), so ``types.FunctionType`` over
    the module's globals reconstructs the very function the repo executes."""
    fn = dh.urlize
    # unwrap the lazy-argument decorator to the underlying function
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    for const in fn.__code__.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == "trim_punctuation":
            if const.co_freevars:
                raise AssertionError(
                    "trim_punctuation unexpectedly closes over %r"
                    % (const.co_freevars,))
            return types.FunctionType(const, fn.__globals__)
    raise AssertionError("trim_punctuation code object not found in urlize")


# --- differential driver ---------------------------------------------------------

def check(oracle, lead, middle, trail):
    got = shadow_trim_punctuation(lead, middle, trail)
    want = oracle(lead, middle, trail)
    if got != want:
        return ("DISAGREEMENT on (lead, middle, trail) = (%r, %r, %r):\n"
                "  shadow (impl region via unchanged scaffolding) = %r\n"
                "  real patched trim_punctuation                  = %r"
                % (lead, middle, trail, got, want))
    return None


def boundary_cases():
    """Hand-picked triples at the decision boundary: entity runs whose encoded
    length exceeds their decoded length, adjacent trailing punctuation,
    all-punctuation middles, wrapping punctuation forcing loop re-entry, and
    branch-skipping plain inputs."""
    ents = ["&lt;", "&gt;", "&amp;", "&quot;", "&#x27;", "&#39;"]
    cases = [
        ("", "google.com/?q=1&lt!", ""),
        ("", "example.com.", ""),
        ("", "example.com&gt;;", ""),
        ("", "foo.com!!!", ")"),
        ("", "a.com&amp;.", "abc"),
        ("", "&lt;&gt;!!", "X"),
        ("", "&amp;&amp;&amp;;", ""),
        ("", "x&lt;y&gt;z.,:;!", "tail"),
        ("", "plain.text;", ""),
        ("", "&#x27;quote'.", ""),
        ("", "no_punct_here", ""),        # branch never entered
        ("", "", ""),                     # empty middle
        ("", "....", ""),                 # all punctuation
        ("", "&amp;.", "&gt;"),
        ("(", "(foo.com.", ""),           # wrapping open + trailing punct
        ("", "(foo.com).", ""),           # balanced wrap then punct
        ("", "[a.com&lt;].", ")"),        # both wrap kinds + entity + punct
        ("", "((x.com!))", ""),           # nested wraps force loop re-entry
        ("", ".&lt;.", "."),              # punct-entity-punct sandwich
        ("", "é.com•!", ""),    # non-ASCII code points
        ("", "\U0001F600.com&lt;!", ""),  # astral code point + entity
    ]
    for e in ents:
        cases.append(("", "host" + e + "!", ""))
        cases.append(("", e + ".", "t"))
        cases.append(("", "a" + e, ""))   # entity, no trailing punct
    return cases


def main():
    oracle = real_trim_punctuation()

    checked = 0
    boundary = boundary_cases()
    for lead, middle, trail in boundary:
        err = check(oracle, lead, middle, trail)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over token sequences mixing entities, punctuation,
    # wrapping characters, plain text, and non-ASCII (pinned seed)
    rng = random.Random(SEED)
    tokens = (["&lt;", "&gt;", "&amp;", "&quot;", "&#x27;", "&#39;"]
              + list(TRAILING_PUNCTUATION_CHARS)
              + list("abzAZ09-_/?=@%~")
              + ["(", ")", "[", "]", "&", "#", "é", "•",
                 "\U0001F600", "com", "www.", "&amp", "&lt", "lt;"])
    for _ in range(N_FUZZ):
        n = rng.randint(0, 8)
        middle = "".join(rng.choice(tokens) for _ in range(n))
        m = rng.randint(0, 3)
        trail = "".join(rng.choice(tokens) for _ in range(m))
        k = rng.randint(0, 2)
        lead = "".join(rng.choice(tokens) for _ in range(k))
        err = check(oracle, lead, middle, trail)
        if err:
            print(err)
            return 1
        checked += 1

    hits = shadow_trim_punctuation.branch_hits
    if hits < 10000:
        print("INSUFFICIENT COVERAGE: modeled block entered only %d times" % hits)
        return 1

    print("G-CONF OK: shadow impl == real patched trim_punctuation on "
          "%d triples (%d boundary + %d fuzz, seed %d); modeled block "
          "exercised %d times; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED, hits))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "branch_hits": hits,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
