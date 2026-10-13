#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13346 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`buildMembershipClause`) transliterated to Python over the real
              `(rhs_template, rhs_params, native, vendor)` carrier, via the
              mapping.md §2 bijection (`List Char` ↔ str, `List Int` ↔ params,
              `has_native_json_field` ↔ `native`, `Int → List Char` ↔ the
              per-value operand-expression map, `wrapHoldsValue` ↔ whether the
              branch's operand expressions hold the value they were built for).
              The per-slot choice `if native then bareTok else wrapOf v`, the
              per-slot fold `clauseTokens`, and the per-branch value list
              `clauseSuppliedValues` are the R/I ops under test.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched
              `KeyTransformIn.process_rhs`, transliterated VERBATIM from
              django/db/models/fields/json.py (the `func` construction + the
              `rhs = rhs % func` substitution), across every vendor/native
              configuration.

ORACLE CHOICE — why we transliterate the patched source instead of calling the
real `KeyTransformIn.process_rhs`:
  `process_rhs` takes a live SQLCompiler + a DB `connection` and calls
  `super().process_rhs(...)` to obtain the plain comma-joined `%s` template; the
  behaviour the patch adds is the pure post-processing DOWNSTREAM of that — the
  per-slot template substitution `rhs = rhs % func`, gated on
  `has_native_json_field` and dispatched on `connection.vendor`. So, per the
  worker prompt, the ORACLE is the patched source's `func`/substitution lines
  transliterated VERBATIM. There is NO axiomatized callee to leave in place
  (mapping.md §3.1).

WHAT IS COMPARED. EXACT per-slot token equality AND exact equality of the values
travelling alongside the clause, on every supported vendor/native configuration,
with NO per-vendor downgrade:

  shadow_tokens(...)          == oracle_tokens(...)          as lists of strings
  shadow_supplied_values(...) == oracle's out_params         as lists of strings

The model's `wrapOf` is a MAP from a listed value to that value's operand token,
so the shadow can reproduce the real token BYTE FOR BYTE on every branch —
including the branch where the token varies from slot to slot and embeds the
value itself. `wrap_of(vendor)` below is the bijection image of `wrapOf`: it is
built per configuration from the gold code's own per-value token construction, so
what this script tests is precisely the modeled claim — one token per listed
value, in order, each token being the one THAT value maps to, and the plain
placeholder on the native branch.

  An earlier revision of this script compared only a per-slot BARE-vs-WRAPPED
  classification, and on the one vendor whose tokens are not uniform across
  slots it further downgraded to "every slot is non-bare" against a `"<wrapped>"`
  sentinel. That masked a real divergence: the model of the day asserted per-slot
  uniformity, which that branch does not have. Both the model and this check are
  now pointwise, so the check compares the tokens themselves and the sentinel is
  gone.

  A later revision compared the accompanying values, but derived the shadow's
  side by TESTING EACH EMITTED TOKEN for the plain mark. That is not what the
  gold code does: it clears the accompanying values per BRANCH and
  unconditionally (`rhs_params = ()` at json.py:396 in the patched tree — inside
  the vendor arm, AFTER the per-value loop and outside it, so no token is ever
  consulted). The two rules coincide on every input whose values
  contain no `%` — which is every input the fuzz pool of the day could produce —
  and part company as soon as a listed value's own text contains the mark, since
  the branch's expression then holds a value whose bytes include `%s` while
  leaving no place to fill. So `wrap_holds_value(vendor)` below is the bijection
  image of `wrapHoldsValue`, read off the gold's per-branch STRUCTURE rather than
  off the token bytes, and `rand_param` now emits `%`- and `%s`-bearing values
  (bare, embedded, and inside lists and dicts) so the distinction is exercised
  rather than assumed. `main` COUNTS the inputs that reach the value-holding
  branch carrying the mark, reports the count, and FAILS if it is zero — so this
  comparison can never go blind again by a narrowing of the pool.

SCOPE. `has_native_json_field` and `vendor` are the two configuration inputs the
gold hunk dispatches on. The gold code assigns a `func` tuple only for the
vendors it enumerates; for a non-native vendor outside that set it leaves
`func = ()` and `rhs % func` RAISES `TypeError` on any non-empty clause. That
configuration is not a behaviour the spec can be faithful to (the modeled method
is total), so it is EXCLUDED from the comparison and asserted to raise, rather
than silently compared — see `test_unenumerated_vendor_raises`, which is run and
whose count is reported. The vendors compared are exactly those the gold hunk
enumerates, plus the native short-circuit.

Exit 0 iff zero disagreements. stdlib only; DB-free.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import json
import random
import sys

SEED = 13346
N_FUZZ = 120_000

BARE = "%s"

# The vendors the gold hunk enumerates on the non-native path. A non-native
# vendor OUTSIDE this set leaves `func = ()` and makes `rhs % func` raise; that
# is out of scope (see module docstring / test_unenumerated_vendor_raises).
ENUMERATED = ("sqlite", "mysql", "mariadb", "oracle")


def bare_template(n):
    """The super-class In.process_rhs template: one plain `%s` per listed value,
    comma-joined inside parens (django/db/models/lookups.py:384)."""
    return "(" + ", ".join([BARE] * n) + ")"


# ----------------------------- ORACLE (gold, verbatim) -----------------------

def oracle_func_and_params(native, vendor, rhs_params):
    """The gold KeyTransformIn.process_rhs, transliterated VERBATIM. Returns the
    per-slot token tuple `func` actually substituted into the template, plus the
    resulting rhs_params. (json import is the stdlib one the gold hunk uses.)"""
    func = ()
    out_params = list(rhs_params)
    if not native:
        if vendor == "oracle":
            func = []
            for value in rhs_params:
                value = json.loads(value)
                function = "JSON_QUERY" if isinstance(value, (list, dict)) else "JSON_VALUE"
                func.append("%s('%s', '$.value')" % (
                    function,
                    json.dumps({"value": value}),
                ))
            func = tuple(func)
            out_params = []
        elif vendor == "mariadb":  # connection.vendor=='mysql' and mysql_is_mariadb
            func = ("JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))",) * len(rhs_params)
        elif vendor in {"sqlite", "mysql"}:
            func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)
    return func, out_params


def oracle_tokens(native, vendor, rhs_params):
    """The per-slot operand tokens the gold patch emits.

    Mirrors the gold control flow exactly: on the NATIVE branch the template is
    returned untouched, so every slot is the plain `%s`. On the non-native branch
    the gold code performs `rhs = rhs % func` UNCONDITIONALLY — so the assembly
    is run here unconditionally too, and it PROPAGATES whatever the gold code
    would raise. That matters for a vendor the gold hunk does not enumerate:
    `func` stays `()` and the substitution raises `TypeError`, which is exactly
    the out-of-scope configuration `test_unenumerated_vendor_raises` asserts."""
    n = len(rhs_params)
    func, out_params = oracle_func_and_params(native, vendor, rhs_params)
    if native:
        return [BARE] * n, out_params
    # the gold assembly step, run for EVERY non-native vendor, as in the gold.
    _ = bare_template(n) % func
    return list(func), out_params


# ----------------------------- SHADOW (model) --------------------------------

def wrap_of(vendor):
    """The bijection image of the model's `wrapOf : Int → List Char`: the map
    from ONE listed value to the operand token that value's slot carries on a
    non-native backend. Built per vendor from the gold hunk's own per-value token
    construction, which is what makes the shadow able to match byte for byte on
    every branch — including the vendor whose token varies with the value."""
    if vendor == "oracle":
        def f(param):
            value = json.loads(param)
            function = "JSON_QUERY" if isinstance(value, (list, dict)) else "JSON_VALUE"
            return "%s('%s', '$.value')" % (function, json.dumps({"value": value}))
        return f
    if vendor == "mariadb":
        return lambda _param: "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))"
    if vendor in {"sqlite", "mysql"}:
        return lambda _param: "JSON_EXTRACT(%s, '$')"
    raise AssertionError("out-of-scope vendor reached the shadow: %r" % (vendor,))


def shadow_tokens(native, vendor, rhs_params):
    """buildMembershipClause transliterated: per-slot
    `if native then bareTok else wrapOf v`, one token per listed value, in order,
    each looked up from THAT slot's own value (the `clauseTokens` fold)."""
    if native:
        return [BARE] * len(rhs_params)
    w = wrap_of(vendor)
    return [w(p) for p in rhs_params]


def wrap_holds_value(vendor):
    """The bijection image of the model's `wrapHoldsValue`: whether this branch's
    operand expressions hold the value they were built for, leaving no place for
    it to be supplied into.

    Read off the gold hunk's per-branch STRUCTURE, not off the emitted bytes: the
    oracle arm builds each expression around `json.dumps({'value': value})` and
    then clears the accompanying values for the WHOLE clause, unconditionally,
    inside that arm (`rhs_params = ()` — see oracle_func_and_params below, which
    transliterates it in place); the other arms leave a plain `%s` inside their
    expression and forward the values untouched. So this is a property of the
    branch, decided once per clause, and it is deliberately NOT computed by
    inspecting a token for the plain mark — a listed value whose own text
    contains `%s` produces an oracle-arm expression that CONTAINS the mark while
    still leaving nothing to fill."""
    return vendor == "oracle"


def shadow_supplied_values(native, vendor, rhs_params):
    """The model's `clauseSuppliedValues` transliterated: the listed values that
    still travel ALONGSIDE the clause. It follows the BRANCH, all of them or none
    — every listed value on the native branch; on the non-native branch none at
    all where the branch's expressions hold their own value, and every listed
    value where they leave a place open. This is the bijection image of
    `clauseSuppliedValues native wrapHoldsValue vals`, which reads the two flags
    and the list and nothing else."""
    if native:
        return list(rhs_params)
    if wrap_holds_value(vendor):
        return []
    return list(rhs_params)


def shadow_require(native, vendor, rhs_params):
    """The modeled precondition `∀ v ∈ vals, wrapOf v ≠ bareTok`. Checked as part
    of conformance: if the real per-value token ever equalled the plain
    placeholder the precondition would be false at a real input."""
    if native:
        return True
    w = wrap_of(vendor)
    return all(w(p) != BARE for p in rhs_params)


# ----------------------------- fuzz ------------------------------------------

# Values whose own text carries the substitution mark. These are the inputs that
# separate a per-BRANCH accompanying-values rule from one derived by testing the
# emitted token for `%s`: on the oracle arm the expression built around such a
# value contains the mark and still leaves nothing to fill, while on the other
# non-native arms the mark inside the value is irrelevant because the value is
# forwarded rather than embedded. A pool without them cannot tell the two rules
# apart (which is how an unfaithful shadow passed this check before).
MARKED = ("%s", "%", "100%sale", "a%sb", "%%", "%s%s", "%d", "x%")


def rand_param(rng):
    """A JSON-encoded prepared parameter, as rhs_params holds on non-native
    backends (get_prep_value json-dumps the value; the oracle branch json.loads
    parses it back). Covers scalars, lists, and dicts (the F2P value kinds), and
    — bare, embedded, and nested inside a list or a dict — values whose own text
    carries the substitution mark."""
    kind = rng.randint(0, 7)
    if kind == 0:
        return json.dumps(rng.randint(-20, 20))
    if kind == 1:
        return json.dumps(rng.choice(["bar", "baz", "BaR", ""]))
    if kind == 2:
        return json.dumps([rng.choice(["foo", "bar", "a"]) for _ in range(rng.randint(1, 2))])
    if kind == 3:
        return json.dumps({rng.choice(["foo", "a"]): rng.choice(["bar", "b"])})
    if kind == 4:
        return json.dumps(rng.choice(MARKED))
    if kind == 5:
        return json.dumps([rng.choice(MARKED) for _ in range(rng.randint(1, 2))])
    if kind == 6:
        return json.dumps({rng.choice(MARKED): rng.choice(MARKED)})
    return json.dumps(rng.choice([True, False]))


def carries_mark(param):
    """Whether this listed value's own text carries the substitution mark."""
    return BARE in param


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1): the F2P value kinds on sqlite, the native
    # short-circuit, single + multi-value lists, each enumerated vendor, and the
    # MIXED-KIND clauses that separate a pointwise model from a uniform one.
    yield (False, "sqlite", [json.dumps(14)])                       # value__c__in=[14]
    yield (False, "sqlite", [json.dumps(14), json.dumps(15)])       # [14,15]
    yield (False, "sqlite", [json.dumps("bar"), json.dumps("baz")]) # ['bar','baz']
    yield (False, "sqlite", [json.dumps(["foo", "bar"])])           # [['foo','bar']]
    yield (False, "sqlite", [json.dumps({"foo": "bar"})])           # [{'foo':'bar'}]
    yield (True, "postgresql", [json.dumps(14), json.dumps(15)])    # native: plain
    # the two witnesses the panel raised: distinct scalars, and a scalar mixed
    # with a composite, on the vendor whose tokens are NOT uniform across slots.
    yield (False, "oracle", [json.dumps(14), json.dumps(15)])
    yield (False, "oracle", [json.dumps(14), json.dumps(["a"])])
    yield (False, "oracle", [json.dumps({"a": "b"}), json.dumps("s"), json.dumps(0)])
    yield (False, "mariadb", [json.dumps(1), json.dumps(2)])
    yield (True, "sqlite", [json.dumps(1)])                         # native+sqlite
    # the accompanying-values witness class: a listed value whose OWN text
    # carries the substitution mark, on each branch. On the arm that embeds the
    # value the emitted expression then contains the mark and still leaves
    # nothing to fill, so a rule derived from the token bytes and the real
    # per-branch rule part company here — these are the inputs that catch it.
    for marked in ("%s", "100%sale", "%", "a%sb"):
        yield (False, "oracle", [json.dumps(marked)])
        yield (False, "sqlite", [json.dumps(marked)])
        yield (False, "mariadb", [json.dumps(marked)])
        yield (True, "postgresql", [json.dumps(marked)])
    yield (False, "oracle", [json.dumps(["%s", "x"])])
    yield (False, "oracle", [json.dumps({"%s": "v"})])
    yield (False, "oracle", [json.dumps("%s"), json.dumps(14)])
    yield (False, "sqlite", [json.dumps("%s"), json.dumps(14)])
    for _ in range(n):
        native = rng.random() < 0.25
        vendor = rng.choice(list(ENUMERATED))
        k = rng.randint(1, 4)  # In raises EmptyResultSet on []; >=1 value
        rhs_params = [rand_param(rng) for _ in range(k)]
        yield (native, vendor, rhs_params)


# ------------------- out-of-scope configuration, asserted -------------------

def test_unenumerated_vendor_raises():
    """A non-native vendor the gold hunk does not enumerate leaves `func = ()`,
    so `rhs % func` raises for any non-empty clause. Not a behaviour the total
    modeled method can be faithful to, so it is EXCLUDED from the differential
    above — but asserted here rather than left unstated."""
    checked = 0
    for vendor in ("cockroachdb", "firebird", ""):
        for params in ([json.dumps(1)], [json.dumps(1), json.dumps(2)]):
            try:
                oracle_tokens(False, vendor, params)
            except TypeError:
                checked += 1
            else:
                return None, ("expected TypeError for unenumerated vendor %r"
                              % (vendor,))
    return checked, None


def main():
    excl, err = test_unenumerated_vendor_raises()
    if err:
        print("G-CONF FAIL: out-of-scope assertion broke: %s" % err)
        return 1

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    marked = 0          # inputs carrying the mark in a listed value's own text
    marked_holding = 0  # ...of those, the ones on the value-holding branch
    for native, vendor, rhs_params in fuzz_inputs(N_FUZZ, rng):
        count += 1
        if any(carries_mark(p) for p in rhs_params):
            marked += 1
            if not native and wrap_holds_value(vendor):
                marked_holding += 1
        orc_tokens, orc_params = oracle_tokens(native, vendor, rhs_params)
        sh_tokens = shadow_tokens(native, vendor, rhs_params)
        sh_params = shadow_supplied_values(native, vendor, rhs_params)
        # (1) EXACT per-slot token equality — count, order, and bytes.
        if sh_tokens != orc_tokens:
            disagreements.append((native, vendor, rhs_params, "tokens",
                                  sh_tokens[:3], orc_tokens[:3]))
        # (2) EXACT equality of the values that travel alongside the clause.
        #     Formerly excluded from the differential; that exclusion is what
        #     let a token-identical, behaviourally broken implementation pass.
        elif sh_params != orc_params:
            disagreements.append((native, vendor, rhs_params, "supplied-values",
                                  sh_params[:3], orc_params[:3]))
        # (3) the modeled precondition holds at every real input.
        elif not shadow_require(native, vendor, rhs_params):
            disagreements.append((native, vendor, rhs_params, "require",
                                  sh_tokens[:3], orc_tokens[:3]))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for native, vendor, rp, why, sh, orc in disagreements:
            print("  native=%s vendor=%s n=%d why=%s shadow=%r oracle=%r"
                  % (native, vendor, len(rp), why, sh, orc))
        return 1
    if marked_holding == 0:
        print("G-CONF FAIL: no listed value carrying the substitution mark "
              "reached the value-holding branch, so the accompanying-values "
              "comparison never separated a per-branch rule from one derived "
              "from the emitted token; widen rand_param/MARKED.")
        return 1
    print("G-CONF OK: R/I shadow of buildMembershipClause agrees with the "
          "gold-patched KeyTransformIn.process_rhs over %d configs "
          "(native + %s; boundary + fuzz, seed=%d): EXACT per-slot token "
          "equality (count, order, and bytes) AND exact equality of the "
          "values travelling alongside the clause, on every configuration, no "
          "per-vendor downgrade, including the non-uniform branch where two "
          "slots of one clause carry different tokens; the modeled precondition "
          "holds at every input. %d inputs carried the substitution mark in a "
          "listed value's own text, %d of them on the value-holding branch — "
          "the class that separates the modeled per-branch rule from one read "
          "off the emitted token. %d out-of-scope (unenumerated-vendor) "
          "configurations asserted to raise and excluded. 0 disagreements."
          % (count, "/".join(ENUMERATED), SEED, marked, marked_holding, excl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
