#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11163 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
``contains`` / ``passes_restriction`` / ``is_removed`` copy over as plain
functions on top of a small immutable-tuple PSeq shim; the sequence-valued
pure fold ``projection`` copies over too and serves as an internal cross-check
of the shadow. There are no @ContractOnly callees in this bundle (the axioms
region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.forms.models.model_to_dict``. The gate applies patch.diff to /testbed
before this script runs, so the imported function carries the patched
filtering behaviour. ``model_to_dict`` reads only ``instance._meta``'s three
field streams (concrete/private/many-to-many) and, per field, the ``name`` /
``editable`` attributes plus ``value_from_object``; a lightweight fake
instance therefore drives the real function without a database or settings
beyond a bare ``settings.configure()``.

Type bridge (mapping.md section 2): each attribute position carries an int
name code in the model and a str field name in the repo; the bridge is the
injective table ``code i <-> "f<i>"``. The two optional parameters bridge as
``None <-> None`` and ``List[int] of codes <-> list of the corresponding
names`` (present-but-empty maps to present-but-empty). The observable is the
returned dict's key sequence (insertion order == source order), bridged back
to the code sequence and compared ORDERED against the shadow's result. The
mapping restricts the domain to injective name codes (the repo observable is
a key set of unique names), so generation keeps per-record names distinct;
the optional lists may still carry duplicates and absent names.

Input domain (Requires): names/edit equal-length lists; allowed/blocked each
``None`` or a list. Generation covers the discriminating structure: the
restriction parameter absent vs present-empty vs present-nonempty, ditto the
removal parameter, non-editable attributes, and codes absent from the record.

>= 1e5 Requires-satisfying inputs: a boundary battery + a small-domain
exhaustive sweep + 100000 fuzz configurations. Pinned fuzz seed: 111631.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from itertools import product

SEED = 111631
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def contains(s, x):
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


def passes_restriction(allowed, n):
    if allowed is None:
        return True
    return contains(ToSeq(allowed), n)


def is_removed(blocked, n):
    if blocked is None:
        return False
    return len(blocked) > 0 and contains(ToSeq(blocked), n)


def projection(names, edit, allowed, blocked):
    if len(names) == 0 or len(edit) == 0:
        return PSeq(0).take(0)
    if edit[0] != 0 and passes_restriction(allowed, names[0]) and not is_removed(blocked, names[0]):
        return PSeq(names[0]) + projection(names.drop(1), edit.drop(1), allowed, blocked)
    return projection(names.drop(1), edit.drop(1), allowed, blocked)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def project_record(names, edit, allowed, blocked):
    result = []  # type: list
    i = len(names)
    while i > 0:
        n = names[i - 1]
        e = edit[i - 1]
        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
            result = [n] + result
        i = i - 1
    return result
    # (the stripped Assert lines carried only proof-side sequence facts)


# --- oracle: the REAL patched repo function ------------------------------------

def load_real():
    import django  # noqa: F401  (resolved from /testbed via PYTHONPATH)
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.forms.models import model_to_dict
    return model_to_dict


class FakeField(object):
    """Only the per-field attributes the real function reads."""

    def __init__(self, name, editable):
        self.name = name
        self.editable = editable

    def value_from_object(self, instance):
        # Stand-in for the real per-field value extraction (an unchanged
        # callee whose RESULT the key-sequence observable never inspects).
        return ("value", self.name)


class FakeOptions(object):
    def __init__(self, fields):
        # All attributes land in the concrete stream; the three streams are
        # chained in order, so the split point is not observable.
        self.concrete_fields = list(fields)
        self.private_fields = []
        self.many_to_many = []


class FakeInstance(object):
    def __init__(self, fields):
        self._meta = FakeOptions(fields)


# --- bridge: int name codes <-> str field names --------------------------------

def code_to_name(c):
    return "f%d" % c


def bridge_optional(codes):
    if codes is None:
        return None
    return [code_to_name(c) for c in codes]


# --- differential driver --------------------------------------------------------

def check(real_fn, spec, allowed, blocked):
    """spec: list of (code, editable_bool) with distinct codes. Returns an
    error string on disagreement, else None."""
    names = [c for (c, _e) in spec]
    edit = [1 if e else 0 for (_c, e) in spec]

    shadow = project_record(names, edit, allowed, blocked)

    inst = FakeInstance([FakeField(code_to_name(c), e) for (c, e) in spec])
    data = real_fn(inst, fields=bridge_optional(allowed),
                   exclude=bridge_optional(blocked))
    real_keys = list(data)  # insertion order == source order

    shadow_keys = [code_to_name(c) for c in shadow]
    if shadow_keys != real_keys:
        return ("DISAGREEMENT on spec=%r allowed=%r blocked=%r:\n"
                "  shadow (impl region) key sequence = %r\n"
                "  real (patched model_to_dict) key sequence = %r"
                % (spec, allowed, blocked, shadow_keys, real_keys))
    # internal cross-check: the executable impl agrees with the pure fold
    if ToSeq(shadow) != projection(ToSeq(names), ToSeq(edit), allowed, blocked):
        return ("INTERNAL: impl region and pure fold disagree on spec=%r "
                "allowed=%r blocked=%r" % (spec, allowed, blocked))
    return None


def boundary_configs():
    spec = [(1, True), (2, True), (3, False), (4, True)]
    return [
        # restriction absent / present-empty / present-nonempty
        (spec, None, None),
        (spec, [], None),
        (spec, [1, 4], None),
        (spec, [3], None),
        (spec, [1, 2, 3, 4], None),
        (spec, [9], None),            # restriction to an absent code
        # removal absent / present-empty / present-nonempty
        (spec, None, []),
        (spec, None, [1, 2]),
        (spec, None, [9]),
        # both filters together, incl. the present-empty restriction
        (spec, [], [1]),
        (spec, [], []),
        (spec, [1, 2, 4], [2]),
        (spec, [1, 1, 2], [2, 2]),    # duplicate entries in the lists
        # degenerate records
        ([], None, None),
        ([], [], []),
        ([(5, False)], None, None),
        ([(5, True)], [], None),
        ([(5, True)], [5], [5]),
    ]


def main():
    real_fn = load_real()

    checked = 0
    for (spec, allowed, blocked) in boundary_configs():
        err = check(real_fn, spec, allowed, blocked)
        if err:
            print(err)
            return 1
        checked += 1

    # exhaustive small-domain sweep: 0..3 attributes over codes {0,1,2}, all
    # editability combinations, each optional list absent / every subset
    small = [0, 1, 2]
    subsets = [None] + [list(s)
                        for k in range(len(small) + 1)
                        for s in _combos(small, k)]
    for k in range(0, 4):
        for name_pick in _combos(small, k):
            for edits in product([True, False], repeat=k):
                spec = list(zip(name_pick, edits))
                for allowed in subsets:
                    for blocked in subsets:
                        err = check(real_fn, spec, allowed, blocked)
                        if err:
                            print(err)
                            return 1
                        checked += 1

    # randomized fuzz (pinned seed): distinct per-record codes from a pool of
    # 8; each optional list absent | empty | a random multiset over the pool
    rng = random.Random(SEED)
    pool = list(range(8))
    for _ in range(N_FUZZ):
        k = rng.randint(0, 8)
        spec = [(c, rng.random() < 0.75) for c in rng.sample(pool, k)]

        opts = []
        for _sel in range(2):
            sel = rng.randint(0, 2)
            if sel == 0:
                opts.append(None)
            elif sel == 1:
                opts.append([])
            else:
                m = rng.randint(1, 10)
                opts.append([rng.choice(pool) for _ in range(m)])
        allowed, blocked = opts

        err = check(real_fn, spec, allowed, blocked)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched model_to_dict key sequence "
          "on %d configurations (boundary + exhaustive small-domain sweep + "
          "%d fuzz, seed %d); 0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


def _combos(pool, k):
    from itertools import combinations
    return combinations(pool, k)


if __name__ == "__main__":
    sys.exit(main())
