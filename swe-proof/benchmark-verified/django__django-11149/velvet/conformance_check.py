#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11149.

Refutes the R/I refinement leg of the four permission gates and the disjunctive
probe `holdsAnyTargetPerm` modeled in Solution.lean. There are NO axioms in this
bundle: every op is pure boolean / list-fold logic over free inputs, so the whole
impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched source instead of running the
real `InlineModelAdmin.has_*_permission`:
  The patched methods live on `InlineModelAdmin` and read
  `self.opts.auto_created`, walk `self.opts.fields` to resolve the target
  model, then call `request.user.has_perm('%s.%s' % (app_label,
  get_permission_codename(perm, opts)))`. Exercising the REAL methods requires a
  fully-migrated admin site: a registered through-model `ModelAdmin`, a `User`
  with a permission set, a `Meta.auto_created` relation, a request, and the auth
  backend — i.e. essentially the F2P Django test harness. Building that purely to
  read back four booleans is impractical and would not isolate the modeled
  decision. So, per the worker prompt, the ORACLE is the patched decision logic
  transliterated VERBATIM from the gold-patched
  django/contrib/admin/options.py:

    def _has_any_perms_for_target_model(user_has_perm, perms):
        return any(user_has_perm(perm) for perm in perms)
    has_add_permission    = _has_any('change') if auto_created else super_result
    has_change_permission = _has_any('change') if auto_created else super_result
    has_delete_permission = _has_any('change') if auto_created else super_result
    has_view_permission   = _has_any('view','change') if auto_created else super_result

  (The field-walk that resolves `opts` to the target model is UNCHANGED by the
  patch — pre- and post-patch both run it — and only selects WHICH model the
  per-permission test queries; it does not change the disjunctive decision being
  modeled. It is folded into the free input `user_has_perm`, which abstracts
  "the principal holds permission P on the resolved related model." mapping.md
  §1/§3.)

  The SHADOW is the model from Solution.lean (anyPerm fold + the four gates).
  We differential-test SHADOW vs ORACLE over every assignment of the free inputs
  (auto_created, the VIEW/CHANGE bits of user_has_perm, super_result) — an
  exhaustive 2^4 = 16-point cube — plus seeded fuzz. Exit 0 iff zero
  disagreements. stdlib only.
"""
import itertools
import random
import sys

SEED = 11149
N_FUZZ = 100_000

# Perm domain modeled in Solution.lean (the only codenames ever queried).
VIEW = "view"
CHANGE = "change"


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def any_perm(user_has_perm, perms):
    """`anyPerm` (front-recursive fold) transliterated: disjunction of the
    per-permission test over the list. Empty list -> False."""
    result = False
    for p in perms:
        result = result or user_has_perm(p)
    return result


def shadow_add(auto_created, user_has_perm, super_result):
    """addRelationAllowed post-image."""
    return any_perm(user_has_perm, [CHANGE]) if auto_created else super_result


def shadow_change(auto_created, user_has_perm, super_result):
    """changeRelationAllowed post-image."""
    return any_perm(user_has_perm, [CHANGE]) if auto_created else super_result


def shadow_delete(auto_created, user_has_perm, super_result):
    """deleteRelationAllowed post-image."""
    return any_perm(user_has_perm, [CHANGE]) if auto_created else super_result


def shadow_view(auto_created, user_has_perm, super_result):
    """viewRelationAllowed post-image (VIEW or CHANGE)."""
    return any_perm(user_has_perm, [VIEW, CHANGE]) if auto_created else super_result


# ---- ORACLE: patched django/contrib/admin/options.py transliterated -------

def oracle_has_any(user_has_perm, perms):
    """`_has_any_perms_for_target_model`'s decision, verbatim:
        any(user.has_perm('%s.%s' % (opts.app_label,
            get_permission_codename(perm, opts))) for perm in perms)
    with the unchanged app_label/codename/field-walk folded into
    `user_has_perm` (mapping.md §3)."""
    return any(user_has_perm(perm) for perm in perms)


def oracle_add(auto_created, user_has_perm, super_result):
    # has_add_permission: if self.opts.auto_created -> _has_any(['change'])
    if auto_created:
        return oracle_has_any(user_has_perm, ['change'])
    return super_result


def oracle_change(auto_created, user_has_perm, super_result):
    if auto_created:
        return oracle_has_any(user_has_perm, ['change'])
    return super_result


def oracle_delete(auto_created, user_has_perm, super_result):
    if auto_created:
        return oracle_has_any(user_has_perm, ['change'])
    return super_result


def oracle_view(auto_created, user_has_perm, super_result):
    if auto_created:
        return oracle_has_any(user_has_perm, ['view', 'change'])
    return super_result


GATES = [
    ("add", shadow_add, oracle_add),
    ("change", shadow_change, oracle_change),
    ("delete", shadow_delete, oracle_delete),
    ("view", shadow_view, oracle_view),
]


def make_user_has_perm(has_view, has_change):
    def f(perm):
        if perm == VIEW:
            return has_view
        if perm == CHANGE:
            return has_change
        # No other codename is ever queried by the modeled methods.
        raise AssertionError("unexpected permission codename: %r" % (perm,))
    return f


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: every assignment of (auto_created, has_view, has_change,
    # super_result) -> 2^4 = 16 points.
    cube = list(itertools.product([False, True], repeat=4))
    # Plus seeded fuzz over the same cube (redundant coverage; the prompt asks
    # for fuzz and it re-exercises the per-gate decision independently).
    fuzz = [tuple(rng.random() < 0.5 for _ in range(4)) for _ in range(N_FUZZ)]

    for auto_created, has_view, has_change, super_result in cube + fuzz:
        uhp = make_user_has_perm(has_view, has_change)
        for name, sh, orc in GATES:
            count += 1
            s = bool(sh(auto_created, uhp, super_result))
            o = bool(orc(auto_created, uhp, super_result))
            if s != o:
                disagreements.append(
                    (name, auto_created, has_view, has_change, super_result, s, o))
                if len(disagreements) >= 8:
                    break
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of the four permission gates + holdsAnyTargetPerm "
          "agrees with the patched options.py decision logic on %d checks "
          "(16 exhaustive x 4 gates + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
