# RELAXED_LEAKAGE — django__django-13346 (velvet)

This file is the bundle's claim that the public `problem_statement` and the gold
edit disagree, so that a spec faithful to the patched code cannot avoid naming
the discriminator. It is a claim to CHECK, not a disposition to inherit: every
number below was measured, and each measurement is given with the command that
reproduces it. The relaxation is recorded as `meta.json relaxed_leakage: true`
(that record and this file are the whole disposition). The mechanical lexical
screen finds nothing — `G-LEAK … "spec view clean", failures: []` — because the
spec view names no repo path, symbol, vendor or format; the leak this file is
about is SEMANTIC.

It describes `Solution.lean` at
`sha256 c5f3b49098b079c18095e7b43704450342edc3568f32a3fe0655d574eeaff081`
(spec-view region hash `76822671673d4aeec14be3f9a3a60f7d2980d3a937433312e4765aad27439e7c`,
`meta.json gates.G-HYGIENE.data.region_hashes.spec_view`). A previous revision of
this file described an EARLIER spec — one uniform alternate token, one output
component — and §3.2/§3.3 below record the measurements that made that spec
unshippable and this file stale; the facet list in §2 is the one the bundle now
ships.

## 1. The problem_statement ↔ gold mismatch

`problem_statement` is a pure **symptom report**: `our_field__key__in=[0]` returns
`0` rows where `our_field__key=0` returns `312`, plus "I would expect that both
filters would give me the same queryset". `hints_text` adds only more symptom (a
one-element list is enough; a maintainer's non-reproducing test). Neither states a
mechanism.

Token scan over the frozen row (my own count, not inherited):

    python - <<'PY'
    import json
    d=json.load(open('benchmark-verified/django__django-13346/instance.json'))
    for t in ["native","has_native","extract","JSON_EXTRACT","JSON_VALUE","wrap",
              "placeholder","%s","process_rhs","rhs","func","KeyTransformIn",
              "register_lookup","token","template","substitut","stored","encod",
              "scalar","bind","capability"]:
        print(t, d['problem_statement'].lower().count(t.lower()),
                 d['hints_text'].lower().count(t.lower()),
                 d['patch'].lower().count(t.lower()))
    PY

Every one of those tokens counts **0 in `problem_statement`** and **0 in
`hints_text`**. The ones the gold patch does use it uses freely — `rhs` 12,
`func` 10, `process_rhs` 2, `%s` 4, `JSON_EXTRACT` 2, `JSON_VALUE` 1,
`has_native` 1, `KeyTransformIn` 2 — and the rest (`token`, `template`,
`substitut`, `placeholder`, `stored`, `scalar`, `bind`, `capability`) are the
mechanism's vocabulary in any wording, absent from the public text as well as
from the patch's own identifiers. Stated the other way, so the claim
is not overstated: what the public text DOES give is that the failure is
backend-dependent — its first line names MySQL, Oracle and SQLite, which are
exactly the non-native-JSON backends of that release. A reader can therefore
suspect a capability split from the public text alone. What no public sentence
gives is anything at the level the spec has to speak at: that the right-hand side
of the membership comparison is built out of per-slot operand tokens at all, that
one branch substitutes a different token per listed value, or that one branch
stops handing the listed values over separately.

## 2. What the spec view discloses (the facet the relaxation covers)

The whole disclosure, in the spec view's own abstract vocabulary:

* `native : Bool` — a capability flag that selects between two token families.
* `bareTok : List Char` — the plain per-slot operand token.
* `wrapOf : Int → List Char` — the alternate token family, as a map from ONE
  listed value to that slot's token, so two slots of one clause need not agree;
  with `require ∀ v ∈ vals, wrapOf v ≠ bareTok`.
* `wrapHoldsValue : Bool` — a branch-level flag for the alternate family.
* the result is the PAIR `(out.1, out.2)`: `out.1 = clauseTokens native bareTok
  wrapOf vals` (one token per listed value, in order, each from that slot's own
  value) and `out.2 = clauseSuppliedValues native wrapHoldsValue vals` (all the
  listed values or none, following the branch).

Not disclosed anywhere in the spec view: the changed file
(`django/db/models/fields/json.py`), the `KeyTransformIn` / `process_rhs` symbols,
`has_native_json_field`, JSON at all, any vendor name, the per-vendor wrapper
strings, and the `rhs = rhs % func` substitution. Those live in `mapping.md` and
`conformance_check.py`, which are not part of the spec view
(`swebench_unified.markers.spec_view`, printed by the command in §4).

## 3. Why each disclosed facet is forced

The test that matters for a facet is not "does the spec still reject the
pre-patch twin without it" — a spec can reject the twin and still be FALSE of the
patched code, or still admit an implementation that breaks the instance. Each
facet below is held in place by one of those two, and the third column says which.

### 3.1 `native` — forced by twin discrimination

The pre-patch code emits the plain token for every slot on every backend; the
patched code emits it only when the capability holds. Recorded: `G-DIFF pass`
(`Solution_prepatch.lean: verification failed`) and `G-GOLD pass` on a pair whose
spec region is byte-identical (`markers.same_spec`). The failing goal is the token
clause itself, `result_1 = clauseTokens native bareTok wrapOf vals`. Without a
capability gate in the spec the twin satisfies it, so this facet is unavoidable
for any spec that captures the fix at all.

### 3.2 `wrapOf` per VALUE, not one uniform token — forced by truth about the patched code

The alternate token on the value-holding arm is built out of the listed value
itself, so it varies from slot to slot. Measured by driving the real patched
callee (worktree at `base_commit` with `patch.diff` applied; the hunk is
`django/db/models/fields/json.py:381-402` post-patch), `__in=[0, 7]` on that
non-native arm:

    rhs        = (JSON_VALUE('{"value": 0}', '$.value'), JSON_VALUE('{"value": 7}', '$.value'))
    rhs_params = ()

The two slots carry DIFFERENT tokens for two different listed values (and
different again for a list-valued element, which reaches `JSON_QUERY`). A spec
with a single uniform alternate token `wrapTok` — the facet the earlier revision
of this file licensed — is therefore not merely weaker: it is FALSE of the patched
code, because no instantiation of one token reproduces that output. Mechanized:

    -- with slotTokU/clauseTokU the uniform-token pure defs, and the two token
    -- byte-strings above as realTok0 / realTok7
    theorem uniform_cannot_match_real (bareTok : List Char) :
        ∀ wrapTok : List Char,
          clauseTokU false bareTok wrapTok [0, 7] ≠ [realTok0, realTok7] := by
      intro w h
      simp [clauseTokU, slotTokU] at h
      have : realTok0 = realTok7 := by rw [← h.1, ← h.2]
      exact absurd this (by decide)

`scripts/lean_verify.sh` on that file exits 0 — the refutation elaborates. So the
value-dependent map is what a faithful spec must say, and `G-CONF` compares it
byte for byte per slot on every enumerated branch (120031 configurations,
`exit 0`), including the branch whose slots are not uniform.

### 3.3 The second component and `wrapHoldsValue` — forced by strength AND by truth

Measured on the same real patched callee, listed values `[0, 7]`, one row per arm:

    native (postgresql)      rhs_params = ['0', '7']
    non-native sqlite        rhs_params = ['0', '7']   rhs = (JSON_EXTRACT(%s, '$'), JSON_EXTRACT(%s, '$'))
    non-native mariadb       rhs_params = ['0', '7']
    non-native mysql         rhs_params = ['0', '7']
    non-native oracle        rhs_params = ()           rhs = (JSON_VALUE('{"value": 0}', ...), ...)

So neither constant is true of the patched code: "always forward" is false of the
value-holding arm and "always clear" is false of the arm the instance's own test
runs on. The component is a two-way branch, which is what `wrapHoldsValue`
carries. That the branch is read off the ARM and never off the emitted token bytes
is the distinction `mapping.md` §2.1 records and `conformance_check.py` fuzzes for
(10374 of its inputs carried the substitution mark in a listed value's own text on
the value-holding branch).

The obligation is also load-bearing against a wrong implementation, which is the
part a twin-discrimination test cannot see. Drop the second `ensures` from the
shipped spec and give the method the body that clears the values on every arm
(`return (result, [])`):

    ensures deleted   →  scripts/lean_verify.sh  EXIT=0   (the wrong impl VERIFIES)
    shipped spec      →  scripts/lean_verify.sh  EXIT=1
        error: unsolved goals, case «ensures_1: out.2 = clauseSuppliedValues native wrapHoldsValue vals»
        ⊢ (if native = true then vals else if wrapHoldsValue = true then [] else vals) = []

Reproduce by copying `Solution.lean` twice and applying exactly those two edits
(the copies are not shipped in the bundle: `G-INTEGRITY` allows no extra bundle
files). That admitted implementation is not a harmless one — on the arm the
instance's failing test actually runs on, each emitted token keeps an inner
placeholder that a forwarded value must fill:

    sqlite3: "SELECT 1 WHERE JSON_EXTRACT(?, '$') IN (JSON_EXTRACT(?, '$'))"
      params ['0','0'] → ok, rows=[(1,)]
      params []        → ProgrammingError: Incorrect number of bindings supplied.
                         The current statement uses 2, and there are 0 supplied.

So a spec that dropped this component would admit an implementation that cannot
execute the query the instance is about, while still rejecting the pre-patch twin.

## 4. Requirements check against the records this bundle now carries

1. **Core is sound.** `G-VERIFY pass` (verified in 9.2s); `G-DIFF pass`
   (prepatch fails on the token clause) with `same_spec = True`, so the twin test
   is a real spec-discrimination test; `G-GOLD pass`; `G-EQ pass` (17 admissible
   attacks re-run of 17 submitted, none breaks the spec, positive control
   verifies); `G-MUT pass` (killed 14/14); `G-PBT SOUND` (14 spec cases behaved as
   expected); `G-CONF pass` (`exit 0`, 120031 configurations over native +
   sqlite/mysql/mariadb/oracle, EXACT per-slot token equality and exact equality
   of the accompanying values, no per-vendor downgrade); `G-RESOLVE pass`
   (`patch.diff` is the gold row, harness reports `resolved`); `G-AX skip` — the
   accurate label, from `meta.json` (`no axiom_check.py (no axioms in bundle)`):
   the bundle declares no `axiom` and no deep-model reference, and `bareTok` /
   `wrapOf` / `wrapHoldsValue` are ordinary input parameters rather than contracts
   about an outside callee, so nothing about the changed operation is hidden
   behind an assumption — it is spelled out as `slotToken` / `clauseTokens` /
   `clauseSuppliedValues`. There is likewise no ungrounded oracle for an
   implementation to echo: both components are concrete total functions of
   `(native, bareTok, wrapOf, wrapHoldsValue, vals)` — of each listed value's
   identity, not merely of `vals.length`.
2. **The leak is semantic and unavoidable**, per §1 (the mechanism vocabulary is
   absent from the public text) and §3 (each disclosed facet is held in place by
   truth about the patched code or by strength against a wrong implementation, so
   there is no narrower spec that is still faithful). The only
   `problem_statement`-derivable property is the semantic "both filters return the
   same rows", which this token-shape abstraction cannot express and which does
   not discriminate the pre-patch plain-token bug.
3. **Recorded in-bundle**: this file plus `meta.json relaxed_leakage: true`.

## 5. What this file does not claim

* It does not claim the spec view is unhelpful to a solver. A reader who has both
  the public statement and the spec view can infer the DIRECTION of the fix
  (capability-gated per-slot token substitution on the membership right-hand
  side). That inference is the accepted cost of a faithful spec here, and it is
  the whole content of this relaxation.
* It does not claim the §3.2/§3.3 facets are free. They are additional
  disclosure over the uniform-token facet the earlier revision described — but
  they refine the SAME discriminator rather than introducing a new one: they name
  no further file, symbol, feature flag, vendor or format, and (§3) neither can be
  removed while leaving a spec that is true of the patched code and false of the
  wrong implementations.
* It does not restate the model's scope boundaries. Those are in `mapping.md`
  §2.1 (unenumerated non-native vendor, the empty clause, expression elements,
  and the subquery right-hand side), each with its own measurement.
