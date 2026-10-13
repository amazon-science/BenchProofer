#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11095.

Refutes the R/I refinement leg of the inline-instance builder modeled in
Solution.lean (`getInlineInstances` + `getInlines` + the pure `kept` fold).
There are NO axioms in this bundle: every op is pure list logic over free
inputs (the selection list and a per-inline admissibility predicate), so the
whole impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched source instead of running the
real `ModelAdmin.get_inline_instances`:
  The real method instantiates each inline class
  (`inline = inline_class(self.model, self.admin_site)`), then for a truthy
  request keeps it iff
      inline.has_view_or_change_permission(request, obj)
      or inline.has_add_permission(request, obj)
      or inline.has_delete_permission(request, obj)
  (and zeroes `max_num` when add is denied). Exercising the REAL method requires
  a fully-migrated admin site: registered `ModelAdmin`/`InlineModelAdmin`
  classes, a model with `_meta`, an `AdminSite`, a `User` with a permission set,
  and a request — i.e. essentially the F2P Django test harness. Building that
  purely to read back a list of instance classes is impractical and would not
  isolate the modeled change. So, per the worker prompt, the ORACLE is the
  patched control/data flow transliterated VERBATIM from the gold-patched
  django/contrib/admin/options.py:

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        for inline_class in self.get_inlines(request, obj):   # <-- the change
            inline = inline_class(self.model, self.admin_site)
            if request:
                if not (inline.has_view_or_change_permission(request, obj) or
                        inline.has_add_permission(request, obj) or
                        inline.has_delete_permission(request, obj)):
                    continue
                if not inline.has_add_permission(request, obj):
                    inline.max_num = 0
            inline_instances.append(inline)
        return inline_instances

    def get_inlines(self, request, obj):     # new hook; default = self.inlines
        return self.inlines

  The single behavioural change is the SOURCE iterated: `self.get_inlines(
  request, obj)` (an overridable hook, default `self.inlines`) instead of
  `self.inlines` directly. Everything else — the per-inline instantiation, the
  view-or-change/add/delete admissibility disjunction, the `max_num` zeroing —
  is UNCHANGED by the patch (pre- and post-patch run it identically). It only
  selects WHICH registrations are admitted, not WHETHER an admitted one is kept.
  So it is folded into:
    * `selected`  — the value the (possibly overridden) hook yields; the list
                    actually iterated. The default hook returns `declared`.
    * `admissible(c)` — a free Bool: "this inline survives the unchanged
                    access-control disjunction for this request/obj". The
                    `max_num` mutation does not change the membership of the
                    returned instance list, so it is observationally invisible
                    to the modeled `kept` result and abstracted away.

  The SHADOW is the model from Solution.lean (`kept` fold over `selected`).
  We differential-test SHADOW vs ORACLE over fuzzed (selected-list,
  admissibility-mask) pairs, including the override scenario the F2P test
  exercises (the hook returns a sublist / empty / reordering of `declared`).
  Exit 0 iff zero disagreements. stdlib only.
"""
import random
import sys

SEED = 11095
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def kept(admissible, selected):
    """`kept` (front-recursive fold) transliterated: keep, in order, exactly the
    elements for which the per-inline admissibility test holds."""
    result = []
    for c in selected:
        if admissible(c):
            result.append(c)
    return result


def shadow_get_inlines(declared):
    """getInlines default: yields the declared set unchanged."""
    return declared


def shadow_get_inline_instances(selected, admissible):
    """getInlineInstances post-image: the kept-sublist of the SELECTED list."""
    return kept(admissible, selected)


# ---- ORACLE: patched django/contrib/admin/options.py transliterated -------

def oracle_get_inline_instances(selected, declared, admissible, request=True):
    """get_inline_instances, patched, with the unchanged per-inline pieces
    folded into `admissible` (mapping.md §3). `selected` is the value the
    (possibly overridden) `get_inlines` hook yields; the default hook returns
    `declared` (modeled by passing selected == declared)."""
    inline_instances = []
    for inline_class in selected:            # patched: self.get_inlines(request, obj)
        # inline = inline_class(self.model, self.admin_site)   # unchanged build
        if request:
            if not admissible(inline_class):  # unchanged view/add/delete disjunction
                continue
            # if not has_add: inline.max_num = 0  # unchanged; invisible to list membership
        inline_instances.append(inline_class)
    return inline_instances


def make_admissible(admit_set):
    """A free per-inline admissibility predicate keyed on the inline id."""
    s = frozenset(admit_set)
    return lambda c: c in s


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # The statically declared set (fixed identity pool the hook may select from).
    declared = list(range(6))

    def selection_space():
        # Boundary / F2P-shaped cases first (plan §4.1 step 4).
        yield []                       # hook returns [] (the F2P "return []" branch)
        yield declared                 # default hook (no override)
        yield declared[:1]             # F2P "self.inlines[:1]"
        yield declared[1:2]            # F2P "self.inlines[1:2]"
        yield list(reversed(declared)) # reordering override
        yield [9, 10]                  # hook yields classes NOT in declared
        yield [0, 0, 1]                # repeats
        yield [3]
        # Fuzz: arbitrary selection lists drawn from a pool wider than declared.
        pool = list(range(12))
        for _ in range(N_FUZZ):
            k = rng.randint(0, 8)
            yield [rng.choice(pool) for _ in range(k)]

    for selected in selection_space():
        # Fuzz the admissibility mask independently of the selection.
        admit_set = {c for c in set(selected) | set(declared) if rng.random() < 0.5}
        admissible = make_admissible(admit_set)
        count += 1
        shadow = shadow_get_inline_instances(selected, admissible)
        oracle = oracle_get_inline_instances(selected, declared, admissible)
        if shadow != oracle:
            disagreements.append((selected, sorted(admit_set), shadow, oracle))
            if len(disagreements) >= 8:
                break

    # Also pin the default-hook identity: getInlines(declared) == declared, and
    # with no override the builder reduces to the kept-sublist of declared.
    for _ in range(1000):
        admit_set = {c for c in declared if rng.random() < 0.5}
        admissible = make_admissible(admit_set)
        sel = shadow_get_inlines(declared)
        count += 1
        if shadow_get_inline_instances(sel, admissible) != \
                oracle_get_inline_instances(declared, declared, admissible):
            disagreements.append(("default-hook", sorted(admit_set), None, None))
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of getInlineInstances + getInlines (kept fold) "
          "agrees with the patched options.py build loop on %d checks "
          "(override + default-hook + fuzz, seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
