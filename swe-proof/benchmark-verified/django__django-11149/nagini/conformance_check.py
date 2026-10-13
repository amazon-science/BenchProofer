#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11149 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. `target_decision` is a plain
short-circuit membership loop over the required-code list; the four
`inline_*_decision` wrappers each build their required-code list via a PSeq
shim (tuple-backed) and call `target_decision`. The @Pure helper `holds_any`
(an Exists over the required list) copies over as a plain any-over-range
function and is used only as an internal cross-check of the shadow. There are
no @ContractOnly callees.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`InlineModelAdmin._has_any_perms_for_target_model` and the four
`InlineModelAdmin.has_add/change/delete/view_permission` methods (their
auto-created branch) from django/contrib/admin/options.py. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. The instance is driven with stub meta/field
objects shaping an auto-created link table between a parent record and a
target record, and a stub request whose user answers `has_perm(p)` by set
membership over a set of held permission strings. This isolates exactly the
modeled operation: which permission strings each decision queries on the
target record and how the answers combine.

TYPE BRIDGE (mapping.md section 2): each distinct int code <-> a distinct
permission string on the target record. `inspect_code` maps to the target's
'view' action and `modify_code` to its 'change' action; any other code c maps
to a synthetic action 'x<c>' (injective, never colliding with view/change).
Full permission strings are built with the REAL
`django.contrib.auth.get_permission_codename` on the stub target meta, so the
bridge and the oracle use the same string construction. `held: PSet[int]`
becomes the set of bridged strings; `required: PSeq[int]` becomes the action
list handed to the helper; bool results carry over identically.

INPUT DOMAIN: `target_decision` Requires only read access, so any
(held, required) is admissible; the four wrappers additionally Require
inspect_code != modify_code, which the generators respect. Boundary: every
held subset of an 8-code universe x several code-pair placements x a battery
of required lists (empty / singletons / the two-code list in both orders /
duplicates) plus all four decisions. Fuzz: random held sets, random distinct
code pairs, random required lists.

>= 1e5 Requires-satisfying inputs: ~13k boundary checks + 22000 fuzz
iterations x 5 checks each. Pinned fuzz seed: 11149.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 11149
N_FUZZ_ITER = 22_000


# --- PSeq shim: the only operations the impl uses ----------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


# --- pure helper from model.py, as a plain function (cross-check only) -------

def holds_any(held, required):
    # Exists(int, lambda j: 0 <= j and j < len(required) and required[j] in held)
    return any(required[j] in held for j in range(len(required)))


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def target_decision(held, required):
    i = 0
    while i < len(required):
        if required[i] in held:
            return True
        i = i + 1
    return False


def inline_inspect_decision(held, inspect_code, modify_code):
    required = PSeq(inspect_code, modify_code)
    return target_decision(held, required)


def inline_create_decision(held, inspect_code, modify_code):
    required = PSeq(modify_code)
    return target_decision(held, required)


def inline_modify_decision(held, inspect_code, modify_code):
    required = PSeq(modify_code)
    return target_decision(held, required)


def inline_remove_decision(held, inspect_code, modify_code):
    required = PSeq(modify_code)
    return target_decision(held, required)


# --- oracle plumbing: drive the REAL patched InlineModelAdmin methods --------

class _StubRemoteField:
    def __init__(self, model):
        self.model = model


class _StubField:
    def __init__(self, remote_field):
        self.remote_field = remote_field


class _StubTargetMeta:
    app_label = "app"
    model_name = "target"


class _StubTargetModel:
    _meta = _StubTargetMeta()


class _StubParentModel:
    pass


class _StubThroughMeta:
    """Meta of an auto-created link table: one plain column, one relation back
    to the parent record, one relation to the target record."""
    auto_created = True

    def __init__(self, parent_model, target_model):
        self.fields = [
            _StubField(None),
            _StubField(_StubRemoteField(parent_model)),
            _StubField(_StubRemoteField(target_model)),
        ]


class _StubUser:
    def __init__(self, held_strings):
        self._held = held_strings

    def has_perm(self, perm):
        return perm in self._held


class _StubRequest:
    def __init__(self, held_strings):
        self.user = _StubUser(held_strings)


class Oracle:
    def __init__(self):
        from django.conf import settings
        if not settings.configured:
            settings.configure()
        import django
        django.setup()
        from django.contrib.admin.options import InlineModelAdmin
        from django.contrib.auth import get_permission_codename
        self._get_permission_codename = get_permission_codename
        self._target_meta = _StubTargetModel._meta
        inline = InlineModelAdmin.__new__(InlineModelAdmin)
        inline.parent_model = _StubParentModel
        inline.opts = _StubThroughMeta(_StubParentModel, _StubTargetModel)
        self._inline = inline

    # -- the code <-> permission-string bridge (mapping.md section 2) --------
    def action_for_code(self, code, inspect_code, modify_code):
        if code == inspect_code:
            return "view"
        if code == modify_code:
            return "change"
        return "x%d" % code

    def perm_string(self, code, inspect_code, modify_code):
        action = self.action_for_code(code, inspect_code, modify_code)
        return "%s.%s" % (
            self._target_meta.app_label,
            self._get_permission_codename(action, self._target_meta))

    def request_for(self, held, inspect_code, modify_code):
        held_strings = {self.perm_string(c, inspect_code, modify_code)
                        for c in held}
        return _StubRequest(held_strings)

    # -- the five real functions under test ----------------------------------
    def helper(self, held, required, inspect_code, modify_code):
        request = self.request_for(held, inspect_code, modify_code)
        perms = [self.action_for_code(c, inspect_code, modify_code)
                 for c in required]
        return self._inline._has_any_perms_for_target_model(request, perms)

    def add(self, held, inspect_code, modify_code):
        request = self.request_for(held, inspect_code, modify_code)
        return self._inline.has_add_permission(request, None)

    def change(self, held, inspect_code, modify_code):
        request = self.request_for(held, inspect_code, modify_code)
        return self._inline.has_change_permission(request, None)

    def delete(self, held, inspect_code, modify_code):
        request = self.request_for(held, inspect_code, modify_code)
        return self._inline.has_delete_permission(request, None)

    def view(self, held, inspect_code, modify_code):
        request = self.request_for(held, inspect_code, modify_code)
        return self._inline.has_view_permission(request, None)


# --- differential driver ------------------------------------------------------

def fail(name, held, required, inspect_code, modify_code, shadow, real):
    print("DISAGREEMENT on %s\n  held=%r\n  required=%r\n"
          "  inspect_code=%r modify_code=%r\n  shadow=%r\n  real=%r"
          % (name, sorted(held), required, inspect_code, modify_code,
             shadow, real))
    return 1


def check_helper(oracle, held, required, inspect_code, modify_code):
    shadow = target_decision(held, list(required))
    # internal cross-check: impl loop agrees with the pure existential
    assert shadow == holds_any(held, list(required))
    real = bool(oracle.helper(held, required, inspect_code, modify_code))
    if shadow != real:
        return fail("target_decision", held, required,
                    inspect_code, modify_code, shadow, real)
    return 0


def check_decisions(oracle, held, inspect_code, modify_code):
    pairs = [
        ("inline_create_decision", inline_create_decision, oracle.add),
        ("inline_modify_decision", inline_modify_decision, oracle.change),
        ("inline_remove_decision", inline_remove_decision, oracle.delete),
        ("inline_inspect_decision", inline_inspect_decision, oracle.view),
    ]
    for name, shadow_fn, real_fn in pairs:
        shadow = shadow_fn(held, inspect_code, modify_code)
        real = bool(real_fn(held, inspect_code, modify_code))
        if shadow != real:
            return fail(name, held, None, inspect_code, modify_code,
                        shadow, real)
    return 0


def main():
    oracle = Oracle()
    checked = 0
    rc = 0

    # boundary: all held subsets of an 8-code universe x code-pair placements
    import itertools
    universe = list(range(8))
    code_pairs = [(0, 1), (1, 0), (6, 7), (0, 7)]
    for inspect_code, modify_code in code_pairs:
        boundary_required = [
            [],                              # no required codes
            [inspect_code],
            [modify_code],
            [inspect_code, modify_code],
            [modify_code, inspect_code],     # order independence
            [modify_code, modify_code],      # duplicate
            [2],                             # unrelated code
            [2, inspect_code, modify_code],
        ]
        for r in range(len(universe) + 1):
            for held_t in itertools.combinations(universe, r):
                held = set(held_t)
                for required in boundary_required:
                    rc |= check_helper(oracle, held, required,
                                       inspect_code, modify_code)
                    checked += 1
                    if rc:
                        return 1
                rc |= check_decisions(oracle, held, inspect_code, modify_code)
                checked += 4
                if rc:
                    return 1

    # fuzz (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_ITER):
        code_universe = range(-3, 12)
        inspect_code = rng.choice(list(code_universe))
        modify_code = rng.choice([c for c in code_universe
                                  if c != inspect_code])
        held = set(rng.sample(list(code_universe),
                              rng.randint(0, len(list(code_universe)))))
        n = rng.randint(0, 5)
        required = [rng.choice(list(code_universe)) for _ in range(n)]
        rc |= check_helper(oracle, held, required, inspect_code, modify_code)
        rc |= check_decisions(oracle, held, inspect_code, modify_code)
        checked += 5
        if rc:
            return 1

    print("G-CONF OK: shadow impl == real patched decisions on %d checks "
          "(boundary + %d fuzz iterations, seed %d)."
          % (checked, N_FUZZ_ITER, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
