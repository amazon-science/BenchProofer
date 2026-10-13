#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12754 (nagini).

SHADOW: the impl region of model.py `removed_base_field_prereqs`, copied
verbatim below with the contract calls (Invariant/Assert; the Requires/Ensures
live outside the impl region) stripped. The @Pure helpers `qualifies` and
`selected` copy over as plain functions on a tuple-backed PSeq shim and serve
as an internal cross-check of the shadow. There are no @ContractOnly callees.

ORACLE: the REAL patched repo routine the model models per mapping.md --
`django.db.migrations.autodetector.MigrationAutodetector
.generate_created_models`, specifically its per-base loop body for a dotted
string base. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. The detector is
driven with duck-typed project states: `.models` registries mapping
(app_label, name) keys to duck-typed model-state objects whose `.fields`
are plain dicts keyed by field-name strings (only key membership is consumed
at the modeled site), and a duck-typed apps registry whose `_meta` reports an
unmanaged model with no local fields, so the loop performs exactly the
per-added-model dependency assembly and creation-operation emission and then
moves on. The emitted dependency 4-tuples are read off the recorded creation
operation's `_auto_deps`; for each dotted base, the modeled output is the set
of field-name slots of that base's entries whose boolean slot is False (the
existence entry carries None there and is excluded), matching mapping.md
section 1 row 7.

Type bridge (mapping.md section 2): int field-name id i <-> the field-name
string "f%d" % i (injective; the modeled site performs only set membership /
equality / hashing on the names). `candidates` = the prior parent registry
entry's fields-dict keys in enumeration order; `parent_after` / `child` = the
key sets of the target parent / child fields dicts. The shadow's List[int]
output and the oracle's emitted name set are compared AS SETS: dict keys are
distinct, so the shadow list is duplicate-free and set equality is exact;
candidate enumeration order vs. Python set iteration order is the documented
behaviorally-immaterial representation difference (dependencies are consumed
by membership downstream -- mapping.md sections 2-3).

Input domain: the model's Requires are pure access permissions, so every
(candidates, parent_after, child) triple over distinct int ids is
Requires-satisfying. Generation mirrors axiom_check.py: its boundary triples,
plus randomized subsets of a small id universe. Each oracle call carries 1-3
dotted bases (each base = one modeled-function input) and occasionally
guard-exercising extras outside the modeled precondition (a missing prior or
target registry entry, a dotless base), for which the oracle is asserted to
emit nothing.

>= 1e5 Requires-satisfying inputs: boundary cases + fuzz until 100000 modeled
(candidates, parent_after, child) triples are checked. Pinned fuzz seed:
12754.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12754
N_TARGET = 100_000

APP = "app"
CHILD_NAME = "child"


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, decorators/contracts stripped ---------------

def qualifies(name, parent_after, child):
    return (not (name in parent_after)) and (name in child)


def selected(candidates, parent_after, child):
    if len(candidates) == 0:
        return PSeq(0).take(0)
    if qualifies(candidates[0], parent_after, child):
        return PSeq(candidates[0]) + selected(candidates.drop(1), parent_after, child)
    return selected(candidates.drop(1), parent_after, child)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def removed_base_field_prereqs(candidates, parent_after, child):
    result = []  # type: List[int]
    i = len(candidates)
    while i > 0:
        c = candidates[i - 1]
        if (not (c in parent_after)) and (c in child):
            result = [c] + result
        i = i - 1
    return result


# --- type bridge: int ids <-> field-name strings ------------------------------

def name_str(i):
    return "f%d" % i


def id_of_name(name):
    assert name.startswith("f"), "unexpected field name %r" % (name,)
    return int(name[1:])


# --- duck-typed project-state plumbing for the real detector ------------------

class _DuckState(object):
    """A project state as consumed here: just a `.models` registry."""

    def __init__(self, models):
        self.models = models


class _DuckModelState(object):
    """A model-state entry: name/fields/bases/options/managers, the members
    the per-added-model loop touches. `fields` is a plain dict keyed by
    field-name strings; only key membership is consumed at the modeled site.
    """

    def __init__(self, name, fields, bases=()):
        self.name = name
        self.fields = fields
        self.bases = tuple(bases)
        # the loop pops these two unconditionally, the rest with defaults
        self.options = {"indexes": [], "constraints": []}
        self.managers = []


class _DuckMeta(object):
    swappable = None
    managed = False          # ends the per-model iteration right after the
    local_fields = ()        # creation operation is recorded
    local_many_to_many = ()


class _DuckModel(object):
    _meta = _DuckMeta()


class _DuckApps(object):
    def get_model(self, app_label, model_name):
        return _DuckModel


def make_detector():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    from django.db.migrations.autodetector import MigrationAutodetector
    return MigrationAutodetector(_DuckState({}), _DuckState({}))


def run_oracle(det, bases, child_fields):
    """One real generate_created_models pass for a single added child model.

    bases: list of (base_string, old_fields_or_None, new_fields_or_None);
    a None registry entry realizes the absent-state guard arm. Returns
    {base_string: set of emitted field-name strings} for every base,
    read off the recorded creation operation's dependency tuples.
    """
    child_key = (APP, CHILD_NAME)
    from_models = {}
    to_models = {child_key: _DuckModelState(
        CHILD_NAME, child_fields, [b for b, _, _ in bases])}
    for base, old_fields, new_fields in bases:
        if "." not in base:
            continue
        b_app, b_name = base.split(".", 1)
        if old_fields is not None:
            from_models[(b_app, b_name)] = _DuckModelState(b_name, old_fields)
        if new_fields is not None:
            to_models[(b_app, b_name)] = _DuckModelState(b_name, new_fields)

    det.from_state = _DuckState(from_models)
    det.to_state = _DuckState(to_models)
    det.new_apps = _DuckApps()
    det.old_model_keys = set()
    det.old_unmanaged_keys = set()
    det.new_model_keys = {child_key}
    det.new_unmanaged_keys = set()
    det.generated_operations = {}

    det.generate_created_models()

    ops = det.generated_operations.get(APP, [])
    assert len(ops) == 1, "expected one recorded creation operation, got %r" % (ops,)
    deps = ops[0]._auto_deps

    out = {}
    for base, _old, _new in bases:
        if "." not in base:
            out[base] = set()
            continue
        b_app, b_name = base.split(".", 1)
        out[base] = set(
            d[2] for d in deps
            if d[0] == b_app and d[1] == b_name and d[3] is False
            and d[2] is not None
        )
    return out


# --- differential driver -------------------------------------------------------

def check_case(det, bases_spec, child_ids, tag):
    """bases_spec: list of (base_string, old_ids_or_None, new_ids_or_None) with
    int-id lists (order of old_ids = candidate enumeration order). Runs one
    real pass and diffs the shadow per modeled base. Returns (n_modeled, err).
    """
    child_fields = dict((name_str(i), object()) for i in child_ids)
    bases = []
    for base, old_ids, new_ids in bases_spec:
        old_f = None if old_ids is None else dict(
            (name_str(i), object()) for i in old_ids)
        new_f = None if new_ids is None else dict(
            (name_str(i), object()) for i in new_ids)
        bases.append((base, old_f, new_f))

    real = run_oracle(det, bases, child_fields)

    n_modeled = 0
    child_set = frozenset(child_ids)
    for base, old_ids, new_ids in bases_spec:
        if "." not in base or old_ids is None or new_ids is None:
            # outside the modeled precondition (guard arm / dotless base):
            # the real pass must emit nothing for this base
            if real[base]:
                return n_modeled, (
                    "DISAGREEMENT [%s]\n  base=%r old=%r new=%r child=%r\n"
                    "  expected no emissions (guard arm), real=%r"
                    % (tag, base, old_ids, new_ids, sorted(child_ids),
                       sorted(real[base])))
            continue

        candidates = PSeq._wrap(old_ids)
        parent_after = frozenset(new_ids)
        shadow_list = removed_base_field_prereqs(candidates, parent_after,
                                                 child_set)
        # internal cross-check: impl agrees with the pure deep model
        assert PSeq._wrap(shadow_list) == selected(candidates, parent_after,
                                                   child_set)
        shadow_names = set(name_str(i) for i in shadow_list)
        assert len(shadow_names) == len(shadow_list), \
            "distinct candidates must yield a duplicate-free emission list"

        n_modeled += 1
        if shadow_names != real[base]:
            return n_modeled, (
                "DISAGREEMENT [%s]\n  base=%r\n  candidates(old)=%r\n"
                "  parent_after(new)=%r\n  child=%r\n  shadow=%r\n  real=%r"
                % (tag, base, old_ids, sorted(new_ids), sorted(child_ids),
                   sorted(shadow_names), sorted(real[base])))
    return n_modeled, None


def boundary_cases():
    """Mirrors axiom_check.py's boundary triples (old, new, child), one dotted
    base per case, plus guard-arm and multi-base shapes."""
    triples = [
        ([], [], []),
        ([1], [], []),
        ([1], [], [1]),
        ([1], [1], [1]),
        ([1, 2], [2], [1]),
        ([1, 2], [2], [1, 2]),
        ([1, 2, 3], [3], [1, 2]),
        ([1, 2, 3], [], [1, 2, 3]),
        ([1, 2, 3], [1, 2, 3], [1, 2, 3]),
        ([1], [], [2]),
        ([1, 2], [1, 2], []),
        ([5, 6, 7], [6], [7, 8]),
        (list(range(10)), [0, 1, 2], list(range(5, 10))),
    ]
    cases = []
    for old, new, child in triples:
        cases.append(([("%s.parent" % APP, old, new)], child))
    # guard arms: absent prior / absent target registry entry; dotless base
    cases.append(([("%s.parent" % APP, None, [1])], [1]))
    cases.append(([("%s.parent" % APP, [1], None)], [1]))
    cases.append(([("plainbase", [1], [])], [1]))
    # several bases in one pass, mixed app labels and guard arms
    cases.append(([
        ("%s.parent" % APP, [1, 2], [2]),
        ("other.mixin", [1, 3], []),
        ("%s.gone" % APP, None, [4]),
    ], [1, 3]))
    return cases


def rand_ids(rng, universe, p):
    return [i for i in universe if rng.random() < p]


def main():
    det = make_detector()

    checked = 0
    n_boundary = 0
    for bases_spec, child_ids in boundary_cases():
        n, err = check_case(det, bases_spec, child_ids, "boundary")
        if err:
            print(err)
            return 1
        checked += n
        n_boundary += n

    rng = random.Random(SEED)
    base_pool = ["%s.parent" % APP, "%s.mixin" % APP, "other.remote"]
    while checked < N_TARGET:
        universe = list(range(rng.randint(0, 14)))
        rng.shuffle(universe)
        child_ids = rand_ids(rng, universe, 0.5)
        nb = rng.randint(1, 3)
        bases_spec = []
        for base in base_pool[:nb]:
            r = rng.random()
            if r < 0.04:
                bases_spec.append((base, None, rand_ids(rng, universe, 0.4)))
                continue
            if r < 0.08:
                bases_spec.append((base, rand_ids(rng, universe, 0.4), None))
                continue
            old = rand_ids(rng, universe, 0.7)
            rng.shuffle(old)
            new = [i for i in old if rng.random() < 0.6]
            new += [i for i in universe if i not in old and rng.random() < 0.2]
            bases_spec.append((base, old, new))
        if rng.random() < 0.03:
            bases_spec.append(("plainbase", rand_ids(rng, universe, 0.4),
                               rand_ids(rng, universe, 0.4)))
        n, err = check_case(det, bases_spec, child_ids, "fuzz")
        if err:
            print(err)
            return 1
        checked += n

    print("G-CONF OK: shadow impl == real patched per-base emission on %d "
          "modeled inputs (%d boundary + %d fuzz, seed %d), 0 disagreements."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
