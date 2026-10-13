#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11149.

This bundle consumes NO `@ContractOnly` axiom: the changed operation (which set
of required permission codes each authorisation decision queries on the target
record) is modelled deeply over `PSet[int]` / `PSeq[int]`. The unchanged callees
the patched helper invokes are *refinements* (kind R), not axioms:

  * `request.user.has_perm('<app_label>.<codename>')` -> set membership
    `code in held`;
  * `django.contrib.auth.get_permission_codename(action, opts)` -> a distinct
    int code per action (faithful only if distinct actions yield distinct
    codename strings);
  * the builtin `any(...)` over the requested actions -> the existential of
    per-code membership (`holds_any`).

There is no axiom Ensures for G-AX to reject. This script instead validates the
two refinement facts the bundle relies on, as an in-container sanity oracle, so
the R-refinements are demonstrably sound:

  (R1) `get_permission_codename` produces DISTINCT codename strings for the two
       relevant actions ('view' vs 'change') on a fixed model — justifying
       `inspect_code != modify_code` in the model;
  (R2) `any(membership(c) for c in required)` == `exists c in required: c in held`
       — the deep model `holds_any` / the short-circuit loop of `target_decision`
       is exactly the builtin `any` over the requested list.

(R1) reimplements the one-line stdlib function verbatim (it has no external
dependency), matching its source at django/contrib/auth/__init__.py:195:
    `return '%s_%s' % (action, opts.model_name)`.

Imports only the Python standard library; exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


# --- (R1) get_permission_codename distinctness ------------------------------

def get_permission_codename(action, model_name):
    """Verbatim reimplementation of django.contrib.auth.get_permission_codename
    (a one-line stdlib-free function): '%s_%s' % (action, opts.model_name)."""
    return '%s_%s' % (action, model_name)


def check_codename_distinct():
    """The two relevant actions must yield distinct codename strings on the same
    model, so the model's `inspect_code != modify_code` precondition is faithful.
    Also check the full 'app_label.codename' strings are distinct."""
    model_names = ['book', 'photo', 'report', 'author_books', 'x', '0', 'm_2_m']
    app_labels = ['admin_inlines', 'issue', 'app', 'a']
    for model_name in model_names:
        view_cn = get_permission_codename('view', model_name)
        change_cn = get_permission_codename('change', model_name)
        assert view_cn != change_cn, (
            "codename collision for view vs change on model %r: %r" %
            (model_name, view_cn))
        for app in app_labels:
            view_full = '%s.%s' % (app, view_cn)
            change_full = '%s.%s' % (app, change_cn)
            assert view_full != change_full, (
                "full permission string collision on %r/%r: %r" %
                (app, model_name, view_full))


# --- (R2) any == existential of membership ----------------------------------

def holds_any_existential(held, required):
    """The deep model `holds_any`: exists a required code that is held."""
    return any(code in held for code in required)


def holds_any_loop(held, required):
    """The short-circuit loop of `target_decision`."""
    for code in required:
        if code in held:
            return True
    return False


def check_any_equals_existential():
    """Over boundary + fuzz (held, required), the builtin `any` over membership,
    the existential, and the short-circuit loop all agree, and each equals the
    plain set-intersection-nonempty truth."""
    rng = random.Random(11149)
    universe = list(range(8))
    # boundary: all subsets of a small universe as held, all short lists as
    # required (incl. empty, the two-element view rule, the one-element rules)
    boundary_required = [
        [],            # no required codes
        [0],           # one-element rule (e.g. ['change'])
        [1],
        [0, 1],        # two-element rule (e.g. ['view','change'])
        [1, 0],        # order independence
        [0, 0],        # duplicate
    ]
    for r in range(len(universe) + 1):
        for held_t in itertools.combinations(universe, r):
            held = set(held_t)
            for required in boundary_required:
                truth = any(c in held for c in required)
                assert holds_any_existential(held, required) == truth
                assert holds_any_loop(held, required) == truth
                # ground truth: nonempty intersection of required with held
                assert truth == (len(set(required) & held) > 0)
    # fuzz
    for _ in range(50000):
        held = set(rng.sample(universe, rng.randint(0, len(universe))))
        n = rng.randint(0, 4)
        required = [rng.randint(0, 7) for _ in range(n)]
        truth = any(c in held for c in required)
        assert holds_any_existential(held, required) == truth
        assert holds_any_loop(held, required) == truth
        assert truth == (len(set(required) & held) > 0)


# --- (R2b) the four decisions match the gold rule ---------------------------

def check_decision_rules():
    """With inspect_code/modify_code distinct, the four modelled decisions equal
    the gold helper-based rules, and an inspect-only actor is denied
    create/modify/remove (the bug fix the F2P tests demand)."""
    inspect_code, modify_code = 0, 1
    assert inspect_code != modify_code
    # held permission sets to exercise: none, inspect-only, change-only, both
    for held in [set(), {inspect_code}, {modify_code}, {inspect_code, modify_code}]:
        create = holds_any_loop(held, [modify_code])
        modify = holds_any_loop(held, [modify_code])
        remove = holds_any_loop(held, [modify_code])
        inspect = holds_any_loop(held, [inspect_code, modify_code])
        # gold semantics
        assert create == (modify_code in held)
        assert modify == (modify_code in held)
        assert remove == (modify_code in held)
        assert inspect == ((inspect_code in held) or (modify_code in held))
    # the regression: inspect-only must NOT permit create/modify/remove
    inspect_only = {inspect_code}
    assert holds_any_loop(inspect_only, [modify_code]) is False
    assert holds_any_loop(inspect_only, [inspect_code, modify_code]) is True


def main():
    check_codename_distinct()
    check_any_equals_existential()
    check_decision_rules()
    print("G-AX OK: no consumed axiom; refinements sound — "
          "get_permission_codename('view') != ('change') on all probed models; "
          "any(membership) == existential == short-circuit loop over "
          "boundary (all subsets of |U|=8) + 50000 fuzz; the four decisions "
          "match the gold rule and deny inspect-only create/modify/remove.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
