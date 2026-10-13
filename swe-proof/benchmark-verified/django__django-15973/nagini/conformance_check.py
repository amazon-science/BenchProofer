#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15973 (nagini).

SHADOW: the impl region of model.py's `through_dependency`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped,
plus the @Pure helper `lower_cp` it calls, copied over as a plain function.
The impl operates on plain Python lists of code points, so no PSeq shim is
needed (PSeq/ToSeq appear only inside the stripped contract calls).

ORACLE: the REAL patched repo function the model models per mapping.md —
`MigrationAutodetector._get_dependencies_for_foreign_key` (a staticmethod on
`django.db.migrations.autodetector.MigrationAutodetector`). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched code importable. The function is driven with a minimal field
stand-in: `field.remote_field.model` carries the primary reference token and
`field.remote_field.through` carries the intermediary reference token, both
as "app.Object" strings (exactly the string-reference form the resolver
handles); no swappable setting is present, and the project_state argument is
unused on this path (the remote-field model attribute is present). The model
projects the function to the intermediary dependency it contributes, so the
oracle output is the (app_label, object_name) of the SECOND dependency the
real function returns.

Type bridge (mapping.md section 2): "app.Object" reference str <-> List[int]
of Unicode code points, s[k] <-> ord(s[k]); the resolved pair str 2-tuple <->
Tuple[List[int], List[int]]. Tokens are therefore encoded to code-point lists
for the shadow and the oracle's returned strings are encoded the same way
before comparing with ==.

Input domain (Requires-satisfying): both references are lists of code points;
the intermediary reference must contain a dot (precondition
`dot_index(through_ref, 0) < len(through_ref)`). The primary reference is
unconstrained beyond being a token; per mapping.md the exercised domain is
ASCII-identifier references, so fuzz tokens draw app/name parts from the
ASCII identifier alphabet (upper/lower/digit/underscore), with occasional
extra dots embedded in the name part (the split is on the FIRST dot) and
undotted or "self" primary tokens mixed in (the primary token's shape is
irrelevant to the projected output but exercises the real function's other
resolver arms without violating any precondition).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 15973.

Exit 0 iff zero disagreements; on disagreement prints the input pair and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15973
N_FUZZ = 100_000


# --- @Pure helper from model.py, decorator stripped --------------------------

def lower_cp(c):
    """Lower-case a single code point: ASCII 'A'..'Z' (65..90) map to
    'a'..'z' (97..122); every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


# --- the impl region of model.py, verbatim, contracts stripped ---------------

def through_dependency(primary_ref, through_ref):
    app = []  # type: List[int]
    name = []  # type: List[int]
    # locate the first dot of the intermediary reference
    d = 0
    while d < len(through_ref) and through_ref[d] != 46:
        d = d + 1
    # app label: prefix before the dot (verbatim)
    j = 0
    while j < d:
        app = app + [through_ref[j]]
        j = j + 1
    # object name: lower-cased suffix after the dot
    k = len(through_ref)
    while k > d + 1:
        c = through_ref[k - 1]
        name = [lower_cp(c)] + name
        k = k - 1
    res = (app, name)  # type: Tuple[List[int], List[int]]
    return res


# --- oracle + differential ----------------------------------------------------

def cps(s):
    """str -> List[int] code points (the mapping.md carrier bridge)."""
    return [ord(ch) for ch in s]


def check_case(real_fn, make_field, primary_tok, through_tok):
    """Diff shadow vs real on one (primary, intermediary) token pair; return
    an error string on disagreement, else None."""
    shadow_app, shadow_name = through_dependency(cps(primary_tok),
                                                 cps(through_tok))
    deps = real_fn("some_app", "somemodel", make_field(primary_tok,
                                                       through_tok), None)
    # projection: the intermediary dependency is the second entry appended
    # when an intermediary reference is present
    if len(deps) != 2:
        return ("DISAGREEMENT (shape)\n  primary=%r through=%r\n"
                "  real returned %d dependencies, expected 2"
                % (primary_tok, through_tok, len(deps)))
    real_app, real_name = deps[1][0], deps[1][1]
    if shadow_app != cps(real_app) or shadow_name != cps(real_name):
        return ("DISAGREEMENT\n  primary=%r through=%r\n"
                "  shadow=(%r, %r)\n  real=(%r, %r)"
                % (primary_tok, through_tok,
                   "".join(chr(c) for c in shadow_app),
                   "".join(chr(c) for c in shadow_name),
                   real_app, real_name))
    return None


def boundary_cases():
    """(primary_tok, through_tok) pairs at the dot/case boundaries."""
    throughs = [
        "fonte_variavel.FonteVariavelModel",
        "variavel.VariavelModel",
        "contract.Contract",
        "testapp.Publisher",
        "a.B",                    # minimal dotted token
        "a.",                     # empty name part (dot at the end)
        ".B",                     # empty app part (dot at the start)
        ".",                      # both parts empty
        "app.lowercase",
        "App.UPPER",
        "x.y.z",                  # multiple dots: split on the FIRST
        "ABC.A.B.C",
        "my_app.My_Model123",
        "APP_LABEL.MixedCaseName",
        "z9.M0del",
        "a..b",                   # consecutive dots
        "_._",
        "0.0",
    ]
    primaries = [
        "testapp.Publisher",      # dotted primary in another app
        "otherapp.Other",
        "self",                   # recursive-reference token
        "UndottedName",           # undotted primary (resolver fallback arm)
        "a.B",
    ]
    pairs = []
    for t in throughs:
        for p in primaries:
            pairs.append((p, t))
    return pairs


IDENT = ([chr(c) for c in range(ord("A"), ord("Z") + 1)]
         + [chr(c) for c in range(ord("a"), ord("z") + 1)]
         + [chr(c) for c in range(ord("0"), ord("9") + 1)]
         + ["_"])


def rand_part(rng, lo, hi):
    return "".join(rng.choice(IDENT) for _ in range(rng.randint(lo, hi)))


def rand_pair(rng):
    """One Requires-satisfying (primary, intermediary) fuzz pair."""
    # intermediary: MUST contain a dot (the precondition)
    app = rand_part(rng, 0, 8)
    name = rand_part(rng, 0, 10)
    if rng.random() < 0.2:
        # extra dot embedded in the name part (split is on the first dot)
        pos = rng.randint(0, len(name))
        name = name[:pos] + "." + name[pos:]
    through_tok = app + "." + name
    # primary: any token shape
    r = rng.random()
    if r < 0.6:
        primary_tok = rand_part(rng, 1, 8) + "." + rand_part(rng, 1, 10)
    elif r < 0.8:
        primary_tok = rand_part(rng, 1, 10)   # undotted
    else:
        primary_tok = "self"
    return primary_tok, through_tok


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    from types import SimpleNamespace
    # REAL patched repo function: the dependency computation for a relational
    # field, as bound in mapping.md section 1.
    from django.db.migrations.autodetector import MigrationAutodetector
    real_fn = MigrationAutodetector._get_dependencies_for_foreign_key

    def make_field(primary_tok, through_tok):
        # Minimal field stand-in: the primary related reference and the
        # intermediary reference, both as string tokens. No swappable
        # setting attribute is present (getattr default applies).
        return SimpleNamespace(
            remote_field=SimpleNamespace(model=primary_tok,
                                         through=through_tok))

    checked = 0
    n_boundary = 0
    for primary_tok, through_tok in boundary_cases():
        err = check_case(real_fn, make_field, primary_tok, through_tok)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        primary_tok, through_tok = rand_pair(rng)
        err = check_case(real_fn, make_field, primary_tok, through_tok)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real intermediary-dependency "
          "resolution on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
