#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11555 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of the single modeled function
`expandOrdering` (the default-ordering expansion loop of
`SQLCompiler.find_ordering_name`). There are NO axioms in this bundle: the
recursive name resolution is a FREE input (mapping.md §3.1), so the whole impl
region is R/I (conf_skip=false).

  * SHADOW  — Solution.lean's `expandItems`/`itemContribution` fold,
              transliterated to Python over the mapping.md §2 bijection
              (`Item.expr e` ↔ a tagged OrderBy-like item carrying identity `e`;
              `Item.name n` ↔ a tagged field-name item carrying identity `n`;
              `Pair` ↔ the `(expr_id, flag)` tuple; `resolve` ↔ a fixed pure
              closure).
  * ORACLE  — `patch.diff`'s behaviour: the GOLD-PATCHED loop body of
              `find_ordering_name`, transliterated VERBATIM with its real
              control flow:

                  results = []
                  for item in ordering:
                      if is_orderby(item):              # isinstance(item, OrderBy)
                          results.append((expr_id(item), False))
                          continue
                      results.extend(resolve(name_id(item)))
                  return results

ORACLE CHOICE — why we transliterate the patched loop instead of running the
real `SQLCompiler.find_ordering_name`:
  The real method needs a fully-configured ORM: concrete model classes with a
  `Meta.ordering`, migrated `Options`, a relation/join graph, the query's
  `alias_map`, and a compiled query — essentially the F2P Django test harness —
  purely to drive one expansion loop. The recursive resolution of a *name* item
  (`self.find_ordering_name(item, …)`) is UNCHANGED by the patch; only the
  per-item dispatch (route an `OrderBy` straight into the result vs. hand it to
  name resolution) changes. So, per the worker prompt and the django-12858
  precedent, the ORACLE is the patched control flow transliterated verbatim, and
  the unchanged recursive resolution is abstracted into the free closure
  `resolve` — the SAME closure is handed to both SHADOW and ORACLE, so the only
  thing under differential test is the `OrderBy` branch the patch actually adds.

We fuzz random specifications mixing OrderBy-like and field-name items (boundary
cases first, incl. the F2P scenario: a default ordering that contains an
`OrderBy(F(...))` expression). Exit 0 iff zero disagreements. stdlib only; fuzz
seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 11555
N_FUZZ = 100_000


# ---- the free recursive resolver (mapping.md §3.1) -------------------------
# `resolve : Name -> List Pair`. The SAME closure is handed to shadow and oracle;
# it stands in for the UNCHANGED `self.find_ordering_name(item, …)` on a name
# item. Its concrete shape is irrelevant (the postcondition holds for every
# resolver) — we just need one fixed total function both sides agree on. A name
# `n` resolves to a small deterministic list of (expr_id, flag) entries.
def make_resolve():
    def resolve(n):
        # deterministic, length 0..3, derived purely from n (a name identity)
        k = n % 4
        return [((-1000 - n * 10 - j), bool((n + j) % 2)) for j in range(k)]
    return resolve


# ---- item model (mapping.md §2) --------------------------------------------
# An item is a tagged tuple: ("expr", e) for an OrderBy-like expression with
# identity e, or ("name", n) for a field-name lookup with identity n.
def is_orderby(item):
    return item[0] == "expr"


def expr_id(item):
    return item[1]


def name_id(item):
    return item[1]


# ---- SHADOW: Solution.lean's expandItems/itemContribution ------------------
def item_contribution(resolve, item):
    # `itemContribution`: an expression contributes [(e, false)]; a name
    # contributes its recursive resolution.
    if is_orderby(item):
        return [(expr_id(item), False)]
    return list(resolve(name_id(item)))


def shadow_expand(resolve, items):
    # `expandItems`: in-order concatenation of each item's contribution.
    out = []
    for it in items:
        out.extend(item_contribution(resolve, it))
    return out


# ---- ORACLE: gold-patched loop body, verbatim ------------------------------
def oracle_expand(resolve, items):
    results = []
    for item in items:
        if is_orderby(item):                       # isinstance(item, OrderBy)
            results.append((expr_id(item), False))
            continue
        results.extend(resolve(name_id(item)))     # self.find_ordering_name(...)
    return results


# ---- fuzz inputs -----------------------------------------------------------
def rand_items(rng):
    k = rng.randint(0, 8)
    items = []
    for _ in range(k):
        if rng.random() < 0.5:
            items.append(("expr", rng.randint(0, 50)))
        else:
            items.append(("name", rng.randint(0, 50)))
    return items


def boundary_cases():
    """Structural boundaries + the F2P scenario (a default ordering containing an
    OrderBy expression alongside name lookups), asserted against BOTH shadow and
    oracle and against the hand-computed expected expansion."""
    cases = []
    # (a) empty spec -> []
    cases.append(("empty", [], []))
    # (b) single OrderBy expression -> [(e, False)], NOT routed to resolve.
    cases.append(("single_expr", [("expr", 7)], [(7, False)]))
    # (c) F2P-shaped: -pub_date(name), headline(name), F('author__name')(expr),
    #     OrderBy(F('second_author__name'))(expr).  The two expressions pass
    #     through as (e, False); the two names expand via resolve.
    rsv = make_resolve()
    spec_c = [("name", 1), ("name", 2), ("expr", 3), ("expr", 4)]
    exp_c = (rsv(1) + rsv(2) + [(3, False)] + [(4, False)])
    cases.append(("f2p_mixed", spec_c, exp_c))
    # (d) all-expressions spec -> every item a singleton (e, False).
    spec_d = [("expr", 9), ("expr", 10), ("expr", 11)]
    cases.append(("all_expr", spec_d, [(9, False), (10, False), (11, False)]))
    # (e) all-names spec -> concatenated resolutions.
    spec_e = [("name", 5), ("name", 6)]
    cases.append(("all_name", spec_e, rsv(5) + rsv(6)))
    return cases


def main():
    rng = random.Random(SEED)
    resolve = make_resolve()
    disagreements = []
    count = 0

    # Boundary scenarios: shadow == oracle AND both == the hand-computed result.
    for name, spec, expected in boundary_cases():
        count += 1
        s = shadow_expand(resolve, spec)
        o = oracle_expand(resolve, spec)
        if s != o:
            disagreements.append(("boundary:%s shadow!=oracle" % name, s, o))
        elif s != expected:
            disagreements.append(("boundary:%s != expected" % name, s, expected))

    # Random sweep: shadow vs oracle over fuzzed specifications.
    for _ in range(N_FUZZ):
        items = rand_items(rng)
        count += 1
        s = shadow_expand(resolve, items)
        o = oracle_expand(resolve, items)
        if s != o:
            disagreements.append((("items=%r" % items), s, o))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d checks:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  %r shadow/oracle/expected=%r/%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of expandOrdering agrees with the gold-patched "
          "find_ordering_name expansion loop on %d specifications (boundary F2P "
          "scenario + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
