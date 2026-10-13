#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13741 (nagini).

SHADOW: the impl regions of model.py copied VERBATIM below with the contract
calls stripped (the impl regions themselves contain no Requires/Ensures
lines). The @Pure helper `norm_seq` and the model's minimal `Field` twin copy
over as plain Python; `PSeq`/`ToSeq` become a thin tuple shim (a PSeq is a
finite sequence with content equality, exactly a tuple). There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo symbols the model models per mapping.md.
The gate applies patch.diff to /testbed before this script runs and
PYTHONPATH=/testbed makes the patched code importable.

  * `make_field(required_kw, disabled_kw)` <-> constructing the real
    `django.contrib.auth.forms.ReadOnlyPasswordHashField`. Bridge
    (mapping.md section 2): the Optional[bool] parameter carries keyword
    presence — None means "the caller did not name this flag", i.e. the key
    is left out of the constructor kwargs; a non-None value is passed
    verbatim. Outputs compared: the constructed field's `.required` /
    `.disabled` flags against the shadow Field twin's fields.

  * `differs(self, initial, data)` <-> the real base
    `django.forms.fields.Field.has_changed` (the method the specialised
    field inherits once patched). Bridge (mapping.md section 2): text values
    are Optional[List[int]] of Unicode code points in the model and
    Optional[str] in the repo — s <-> [ord(c) for c in s], None <-> None;
    the shadow's PSeq-content inequality corresponds to str inequality
    (both are content equality on the code-point sequence). The shadow's
    Field twin carries the `disabled` flag the real field object carries.
    Outputs compared as bools.

  * Composed: for every kwarg combination, the real patched
    ReadOnlyPasswordHashField's own `has_changed` is diffed against
    shadow `differs` over a shadow field built by shadow `make_field`,
    checking the two modeled behaviours agree with the repo when chained.

Input domain (the model's Requires): any Optional[bool] pair for make_field
(9 distinct inputs — both flags range over {absent, True, False}); for
differs any Optional[List[int]] pair plus a bool `disabled` flag. Boundary
cases cover the None/empty frontier, equal/unequal values, shared prefixes,
and non-ASCII / astral code points; fuzz draws random-length code-point
lists biased toward short lengths and occasionally reuses one side on the
other to hit the equal case.

>= 1e5 Requires-satisfying inputs: 9 make_field combos + 28 differs
boundary pairs (x2 disabled states) + 100000 differs fuzz cases + 9x8
composed cases. Pinned fuzz seed: 13741.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13741
N_FUZZ = 100_000


# --- PSeq / ToSeq shim (a PSeq is a finite sequence: plain tuple) -------------

class PSeq(tuple):
    def __new__(cls, *args):
        return super().__new__(cls, args)

    def take(self, n):
        return PSeq(*self[:n])


def ToSeq(v):
    return PSeq(*v)


# --- the model's Field twin, contracts stripped -------------------------------

class Field:
    def __init__(self, required, disabled):
        self.required = required
        self.disabled = disabled


# --- pure helper from model.py, decorator + contracts stripped ----------------

def norm_seq(v):
    if v is None:
        return PSeq(0).take(0)
    return ToSeq(v)


# --- the impl region of make_field, verbatim -----------------------------------

def make_field(required_kw, disabled_kw):
    if required_kw is None:
        required = False
    else:
        required = required_kw
    if disabled_kw is None:
        disabled = True
    else:
        disabled = disabled_kw
    return Field(required, disabled)


# --- the impl region of differs, verbatim --------------------------------------

def differs(self, initial, data):
    if self.disabled:
        return False
    return norm_seq(initial) != norm_seq(data)


# --- bridges -------------------------------------------------------------------

def to_repo_text(v):
    """Optional[List[int]] code points -> Optional[str] (mapping.md sec. 2)."""
    if v is None:
        return None
    return "".join(chr(c) for c in v)


def make_kwargs(required_kw, disabled_kw):
    """Optional[bool] carriers -> constructor kwargs (None = key absent)."""
    kwargs = {}
    if required_kw is not None:
        kwargs["required"] = required_kw
    if disabled_kw is not None:
        kwargs["disabled"] = disabled_kw
    return kwargs


# --- input generators ----------------------------------------------------------

KWARG_COMBOS = [
    (None, None),
    (None, True), (None, False),
    (True, None), (False, None),
    (True, True), (True, False),
    (False, True), (False, False),
]


def boundary_value_pairs():
    """(initial, data) as Optional[List[int]] code-point lists."""
    a = [ord(c) for c in "aaa"]
    b = [ord(c) for c in "bbb"]
    h1 = [ord(c) for c in "hash$abc"]
    h2 = [ord(c) for c in "hash$xyz"]
    uni = [0x00E9, 0x4E2D, 0x1F600]          # non-ASCII incl. astral plane
    uni2 = [0x00E9, 0x4E2D, 0x1F601]
    nul = [0]                                 # NUL code point
    return [
        (None, None), (None, []), ([], None), ([], []),
        (a, b), (a, list(a)), (a, None), (None, b),
        ([], [ord("x")]), ([ord("x")], []),
        (h1, list(h1)), (h1, h2),
        (a, a[:-1]), (a[:-1], a),             # shared prefix, differing length
        (uni, list(uni)), (uni, uni2), (uni, None), (None, uni),
        (nul, []), (nul, list(nul)),
        ([ord("0")], [0]),                    # digit char vs NUL
        (a, [ord("A")] + a[1:]),              # case-differing head
        ([32], []), ([32], [32, 32]),         # whitespace-only content
        ([0x10FFFF], [0x10FFFF]), ([0x10FFFF], [0x10FFFE]),  # max code point
        (list(range(97, 123)), list(range(97, 123))),
        (list(range(97, 123)), list(range(97, 122)) + [122 + 1]),
    ]


def rand_text(rng):
    """None or a random code-point list, biased toward short lengths."""
    r = rng.random()
    if r < 0.15:
        return None
    if r < 0.30:
        return []
    n = rng.choice((1, 1, 2, 3, 5, 8, 20))
    out = []
    for _ in range(n):
        band = rng.random()
        if band < 0.7:
            out.append(rng.randint(32, 126))           # printable ASCII
        elif band < 0.9:
            out.append(rng.randint(0xA0, 0x2FFF))      # BMP non-ASCII
        else:
            out.append(rng.randint(0x10000, 0x10FFFF)) # astral plane
    return out


def rand_pair(rng):
    initial = rand_text(rng)
    if rng.random() < 0.35:
        # reuse content on the other side to exercise the equal case
        data = None if initial is None else list(initial)
    else:
        data = rand_text(rng)
    disabled = rng.random() < 0.5
    return disabled, initial, data


# --- checks ----------------------------------------------------------------------

def check_construct(RealFieldCls, required_kw, disabled_kw):
    shadow_field = make_field(required_kw, disabled_kw)
    real_field = RealFieldCls(**make_kwargs(required_kw, disabled_kw))
    if (shadow_field.required != real_field.required
            or shadow_field.disabled != real_field.disabled):
        return ("DISAGREEMENT (construct)\n"
                "  required_kw=%r disabled_kw=%r\n"
                "  shadow=(required=%r, disabled=%r)\n"
                "  real=(required=%r, disabled=%r)"
                % (required_kw, disabled_kw,
                   shadow_field.required, shadow_field.disabled,
                   real_field.required, real_field.disabled))
    return None


def check_differs(base_field_factory, disabled, initial, data):
    shadow_field = Field(False, disabled)
    shadow_out = differs(shadow_field, initial, data)
    real_field = base_field_factory(disabled)
    real_out = bool(real_field.has_changed(to_repo_text(initial),
                                           to_repo_text(data)))
    if shadow_out != real_out:
        return ("DISAGREEMENT (change decision)\n"
                "  disabled=%r initial=%r data=%r\n"
                "  shadow=%r\n  real=%r"
                % (disabled, initial, data, shadow_out, real_out))
    return None


def check_composed(RealFieldCls, required_kw, disabled_kw, initial, data):
    shadow_field = make_field(required_kw, disabled_kw)
    shadow_out = differs(shadow_field, initial, data)
    real_field = RealFieldCls(**make_kwargs(required_kw, disabled_kw))
    real_out = bool(real_field.has_changed(to_repo_text(initial),
                                           to_repo_text(data)))
    if shadow_out != real_out:
        return ("DISAGREEMENT (composed)\n"
                "  required_kw=%r disabled_kw=%r initial=%r data=%r\n"
                "  shadow=%r\n  real=%r"
                % (required_kw, disabled_kw, initial, data,
                   shadow_out, real_out))
    return None


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="confcheck-13741-not-secret",
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
        django.setup()

    from django import forms
    from django.contrib.auth.forms import ReadOnlyPasswordHashField

    def base_field(disabled):
        return forms.Field(required=False, disabled=disabled)

    checked = 0

    # (1) make_field vs the real specialised-field construction: full domain.
    for required_kw, disabled_kw in KWARG_COMBOS:
        err = check_construct(ReadOnlyPasswordHashField, required_kw, disabled_kw)
        if err:
            print(err)
            return 1
        checked += 1

    # (2) differs vs the real inherited change decision: boundary battery.
    pairs = boundary_value_pairs()
    for disabled in (True, False):
        for initial, data in pairs:
            err = check_differs(base_field, disabled, initial, data)
            if err:
                print(err)
                return 1
            checked += 1

    # (3) differs fuzz, pinned seed.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        disabled, initial, data = rand_pair(rng)
        err = check_differs(base_field, disabled, initial, data)
        if err:
            print(err)
            return 1
        checked += 1

    # (4) composed: real specialised field end-to-end over every kwarg combo.
    composed_pairs = [
        (None, None), ([], []),
        ([ord(c) for c in "aaa"], [ord(c) for c in "bbb"]),
        ([ord(c) for c in "aaa"], [ord(c) for c in "aaa"]),
        (None, [ord(c) for c in "bbb"]), ([ord(c) for c in "aaa"], None),
        ([], [ord("x")]), ([ord("x")], []),
    ]
    for required_kw, disabled_kw in KWARG_COMBOS:
        for initial, data in composed_pairs:
            err = check_composed(ReadOnlyPasswordHashField,
                                 required_kw, disabled_kw, initial, data)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real repo behaviour on %d inputs "
          "(%d construct + %d boundary + %d fuzz + %d composed, seed %d)."
          % (checked, len(KWARG_COMBOS), 2 * len(pairs), N_FUZZ,
             len(KWARG_COMBOS) * len(composed_pairs), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
