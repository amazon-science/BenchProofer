#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11163.

This bundle consumes NO `@ContractOnly` axiom: the changed operation is pure
membership/structure logic over a record's attributes and two optional lists,
modelled DEEPLY by the `projection` fold (a per-attribute keep decision). G-AX
therefore validates the *behavioural fact the deep model rests on* against the
REAL runtime semantics the patched code uses: the per-attribute keep decision of
the real projection loop.

The real loop (post-patch) is, verbatim, three filters applied while iterating
the record's editable-and-private-and-m2m attributes:

    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if not getattr(f, 'editable', False):
            continue
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)

`data` is then observed by its key set (the FAIL_TO_PASS test compares
`sorted(model_to_dict(...))`, i.e. the projected attribute names). G-AX
reconstructs that exact loop over lightweight field objects (a `name` and an
`editable` flag — the only attributes the three filters read) WITHOUT a database
or Django settings, and asserts:

  (1) the deep model `projection` (re-expressed in plain Python here) yields the
      same projected names as the real post-patch loop, over boundary + fuzz
      configurations covering the discriminating cases (restriction list absent
      vs present-empty vs present-nonempty; removal list absent vs present-empty
      vs present-nonempty; non-editable attributes);
  (2) the PRE-patch loop (`if fields and f.name not in fields`) diverges from the
      deep model on EXACTLY the present-but-empty restriction list (the clause
      `model_prepatch.py` fails on): it returns all editable, non-removed names
      where the model / post-patch loop return none.

Imports only the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys
from itertools import chain


# --- a lightweight field object: only the attributes the filters read --------

class FakeField:
    def __init__(self, name, editable):
        self.name = name
        self.editable = editable

    def value_from_object(self, instance):
        # Stand-in for the real per-field value extraction (an unchanged callee
        # whose RESULT the keyset observable never inspects); a sentinel keyed by
        # the field name is sufficient for the keyset comparison.
        return ('value', self.name)


# --- the REAL post-patch model_to_dict filtering loop, verbatim --------------

def real_model_to_dict_keys(fields_iter, fields=None, exclude=None):
    data = {}
    for f in chain(fields_iter, [], []):     # concrete + private + m2m streams
        if not getattr(f, 'editable', False):
            continue
        if fields is not None and f.name not in fields:      # the gold fix
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(None)
    return sorted(data)


# --- the PRE-patch (buggy) loop: `if fields and ...` -------------------------

def prepatch_model_to_dict_keys(fields_iter, fields=None, exclude=None):
    data = {}
    for f in chain(fields_iter, [], []):
        if not getattr(f, 'editable', False):
            continue
        if fields and f.name not in fields:                  # the bug
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(None)
    return sorted(data)


# --- the deep model `projection`, re-expressed in plain Python ----------------
# Mirrors model.py: contains / passes_restriction / is_removed / projection.

def m_contains(seq, x):
    return x in seq


def m_passes_restriction(allowed, n):
    if allowed is None:
        return True
    return m_contains(allowed, n)


def m_is_removed(blocked, n):
    if blocked is None:
        return False
    return len(blocked) > 0 and m_contains(blocked, n)


def model_projection(names, edit, allowed, blocked):
    out = []
    for k in range(min(len(names), len(edit))):
        n = names[k]
        e = edit[k]
        if e != 0 and m_passes_restriction(allowed, n) and not m_is_removed(blocked, n):
            out.append(n)
    return out


# --- harness ------------------------------------------------------------------

def make_fields(spec):
    """spec: list of (name, editable_bool)."""
    return [FakeField(name, ed) for (name, ed) in spec]


def names_and_edit(spec):
    names = [name for (name, _ed) in spec]
    edit = [1 if ed else 0 for (_name, ed) in spec]
    return names, edit


def check_config(spec, allowed, blocked):
    flds = make_fields(spec)
    real = real_model_to_dict_keys(flds, fields=allowed, exclude=blocked)

    names, edit = names_and_edit(spec)
    model_keys = sorted(model_projection(names, edit, allowed, blocked))

    assert model_keys == real, (
        "deep model projection disagrees with the real post-patch loop:\n"
        "  spec=%r allowed=%r blocked=%r\n  model=%r real=%r"
        % (spec, allowed, blocked, model_keys, real))
    return real


def check_boundary():
    # An editable + a non-editable attribute, distinct names.
    spec = [(1, True), (2, True), (3, False), (4, True)]
    editable_names = [1, 2, 4]

    # restriction absent -> all editable, non-removed names
    assert check_boundary_eq(spec, None, None, editable_names)
    # restriction present-empty -> NOTHING (the headline behaviour)
    assert check_boundary_eq(spec, [], None, [])
    # restriction present-nonempty -> intersection with editable
    assert check_boundary_eq(spec, [1, 4], None, [1, 4])
    assert check_boundary_eq(spec, [3], None, [])      # 3 not editable
    assert check_boundary_eq(spec, [1, 2, 4], None, [1, 2, 4])
    # removal absent / present-empty removes nothing
    assert check_boundary_eq(spec, None, None, editable_names)
    assert check_boundary_eq(spec, None, [], editable_names)
    # removal present-nonempty removes members
    assert check_boundary_eq(spec, None, [1, 2], [4])
    # restriction empty wins regardless of removal
    assert check_boundary_eq(spec, [], [1], [])
    # restriction + removal together
    assert check_boundary_eq(spec, [1, 2, 4], [2], [1, 4])


def check_boundary_eq(spec, allowed, blocked, expected):
    got = check_config(spec, allowed, blocked)
    assert got == sorted(expected), (
        "real loop gave %r, expected %r (spec=%r allowed=%r blocked=%r)"
        % (got, sorted(expected), spec, allowed, blocked))
    return True


def check_prepatch_divergence():
    """The pre-patch loop must equal the model EXCEPT on a present-empty
    restriction list, where it returns all editable, non-removed names while the
    model / post-patch loop return none (model_prepatch.py's failing clause)."""
    spec = [(1, True), (2, True), (3, False), (4, True)]

    # present-empty restriction: divergence point
    pre = prepatch_model_to_dict_keys(make_fields(spec), fields=[], exclude=None)
    post = real_model_to_dict_keys(make_fields(spec), fields=[], exclude=None)
    assert post == [], "post-patch must drop everything for fields=[]"
    assert pre == [1, 2, 4], (
        "pre-patch must (buggily) keep all editable names for fields=[]; got %r"
        % (pre,))
    assert pre != post, "the bug must be observable at fields=[]"


def main():
    check_boundary()
    check_prepatch_divergence()

    rng = random.Random(11163)
    pool = list(range(8))
    fuzz = 0
    diverged_only_on_empty = True
    for _ in range(20000):
        k = rng.randint(0, 8)
        # distinct attribute names so the keyset is a clean set
        spec = [(name, rng.random() < 0.75) for name in rng.sample(pool, k)]
        names = [n for (n, _e) in spec]

        # restriction: None | [] | random subset (incl. names not present)
        rsel = rng.randint(0, 2)
        if rsel == 0:
            allowed = None
        elif rsel == 1:
            allowed = []
        else:
            allowed = rng.sample(pool, rng.randint(0, len(pool)))

        bsel = rng.randint(0, 2)
        if bsel == 0:
            blocked = None
        elif bsel == 1:
            blocked = []
        else:
            blocked = rng.sample(pool, rng.randint(0, len(pool)))

        check_config(spec, allowed, blocked)

        # confirm the pre-patch loop differs from post-patch ONLY when the
        # restriction list is present-and-empty (and something would survive)
        pre = prepatch_model_to_dict_keys(make_fields(spec), fields=allowed, exclude=blocked)
        post = real_model_to_dict_keys(make_fields(spec), fields=allowed, exclude=blocked)
        if pre != post:
            if allowed != []:
                diverged_only_on_empty = False
        fuzz += 1

    assert diverged_only_on_empty, (
        "pre/post-patch divergence observed outside the present-empty "
        "restriction list -- the bug is not localised as modelled")

    print("G-AX OK: deep model `projection` matches the real post-patch "
          "model_to_dict filtering loop over the boundary battery + %d fuzz "
          "configurations (restriction absent/empty/subset x removal "
          "absent/empty/subset x non-editable attributes); the pre-patch loop "
          "diverges on EXACTLY the present-empty restriction list "
          "(model_prepatch.py's failing clause)." % fuzz)
    return 0


if __name__ == "__main__":
    sys.exit(main())
