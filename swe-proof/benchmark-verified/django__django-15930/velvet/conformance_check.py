#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15930 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`assembleConditionalBranch`) transliterated to Python over the
              real `(sql, params)` carrier, via the mapping.md §2 bijection
              (`List Char` ↔ str, empty `[]` ↔ "", `List Int` params ↔ list).
              The empty-condition substitution `if cond.sql = [] then
              truePredicate else cond` and the `branchClause` splice are the R/I
              ops under test.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched assembly of one
              `When.as_sql` branch, transliterated VERBATIM from
              django/db/models/expressions.py (post-patch, lines 1299-1308).

ORACLE CHOICE — why we transliterate the patched source instead of calling the
real `When.as_sql`:
  `When.as_sql` does its own `compiler.compile(self.condition)` /
  `compiler.compile(self.result)` internally — it takes a live SQLCompiler and
  resolved expression nodes, not already-compiled `(sql, params)` fragments. The
  behaviour under test is the pure assembly *downstream* of those compiles: the
  empty-condition substitution + the template splice. So, per the worker prompt,
  the ORACLE is the patched source lines transliterated verbatim. The single
  A-tagged callee in that span, `compiler.compile(Value(True))`, is left as the
  real callee's compiled form `("%s", [1])` (mapping.md §3.1, validated by G-AX),
  NOT replaced by anything weaker. SHADOW vs ORACLE are differential-tested over
  fuzzed condition/result fragment pairs (including the empty-condition boundary)
  under the mapping.md §2 bridge. Exit 0 iff zero disagreements. stdlib only.

The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15930
N_FUZZ = 100_000

# The compiled form of Value(True): the always-true predicate the empty-
# condition case falls back to (mapping.md §3.1; A-reference, G-AX-validated).
TRUE_SQL = "%s"
TRUE_PARAMS = [1]

# The fixed When template (django/db/models/expressions.py:1246).
TEMPLATE = "WHEN %(condition)s THEN %(result)s"


def shadow(cond_sql, cond_params, res_sql, res_params):
    """assembleConditionalBranch transliterated: substitute the always-true
    predicate iff the condition text is empty, then splice the branch.
    Mirrors `let effCond := if cond.sql = [] then truePredicate else cond;
    return branchClause effCond res` exactly (mapping.md §2 bridge)."""
    if cond_sql == "":
        eff_sql, eff_params = TRUE_SQL, list(TRUE_PARAMS)
    else:
        eff_sql, eff_params = cond_sql, list(cond_params)
    out_sql = "WHEN " + eff_sql + " THEN " + res_sql
    out_params = eff_params + list(res_params)
    return out_sql, out_params


def oracle(cond_sql, cond_params, res_sql, res_params):
    """patch.diff's behaviour: the gold-patched branch assembly of
    When.as_sql, transliterated VERBATIM (expressions.py:1299-1308 post-patch).
    `compiler.compile(Value(True))` -> its real compiled form ("%s", [1])."""
    template_params = {}
    sql_params = []
    condition_sql, condition_params = cond_sql, list(cond_params)
    # --- the gold hunk, verbatim ---
    if condition_sql == "":
        condition_sql, condition_params = TRUE_SQL, list(TRUE_PARAMS)
    # --- unchanged surrounding assembly ---
    template_params["condition"] = condition_sql
    sql_params.extend(condition_params)
    result_sql, result_params = res_sql, list(res_params)
    template_params["result"] = result_sql
    sql_params.extend(result_params)
    return TEMPLATE % template_params, sql_params


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the empty condition is THE bug
    yield ("", [], "%s", [1])                       # ~Q(pk__in=[]) -> empty cond
    yield ("", [], "true", [])                      # empty cond, literal result
    yield ("", [], "", [])                          # both empty (degenerate)
    yield ('"t"."x" = %s', [7], "%s", [42])         # ordinary condition
    yield ('"t"."x" IN (%s, %s)', [1, 2], "%s", [0])
    yield ("1 = 1", [], "0", [])                    # non-empty, no params
    frags = ['"t"."c" = %s', '"a"."b" IN (%s)', "NOT (%s)", "x", "%s", ""]
    results = ["%s", "true", "1", '"t"."r"', ""]
    for _ in range(n):
        cond_sql = rng.choice(frags)
        cond_params = [rng.randint(0, 9) for _ in range(rng.randint(0, 3))]
        res_sql = rng.choice(results)
        res_params = [rng.randint(0, 9) for _ in range(rng.randint(0, 2))]
        yield (cond_sql, cond_params, res_sql, res_params)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cond_sql, cond_params, res_sql, res_params in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(cond_sql, cond_params, res_sql, res_params)
        orc = oracle(cond_sql, cond_params, res_sql, res_params)
        if sh != orc:
            disagreements.append((cond_sql, cond_params, res_sql, res_params,
                                  sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cs, cp, rs, rp, sh, orc in disagreements:
            print("  cond=(%r,%r) res=(%r,%r) shadow=%r oracle=%r"
                  % (cs, cp, rs, rp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assembleConditionalBranch agrees with the "
          "gold-patched When.as_sql branch assembly on %d fragment pairs "
          "(boundary + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
