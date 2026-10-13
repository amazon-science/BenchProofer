# refinement.md — sympy__sympy-14531

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `printTaggedPair` and `printLimit` `do` blocks, the
`taggedPair`/`taggedPairReg`/`limitTriple`/`limitTripleReg` deep models, and the
opaque `renderSub`) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a deep/opaque model validated == the real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**; the A-reference is
checked by **G-AX** (`axiom_check.py`).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). The gold patch edits
many `_print_X` arms of `StrPrinter`; the two modeled here — `_print_Relational`
(charmap arm) and `_print_Limit` (`dir == "+"` arm) — are precisely the two the
F2P tests (`test_python_relational`, `test_Rational`) exercise. The other arms
are the IDENTICAL transformation (`%s`/`str(sub)` → `self._print(sub)`) applied
to other heads; modeling these two pins the behavior the tests demand and the
remaining arms are the same refinement on different tags (mapping.md §1).

## 0. What the changed call actually changes (two legs, not one)

`str(sub)` → `self._print(sub)` swaps a THROWAWAY serializer for the ACTIVE one,
and the active one differs from a throwaway one in TWO respects, both observable
to the caller and one graded by each F2P test:

| leg | what the active serializer carries | modeled as | graded by |
|---|---|---|---|
| CONFIGURATION | `self._settings` (e.g. `sympy_integers`) | the `cfg : Bool` argument of `renderSub` | `test_Rational`: `sstr(Eq(x, Rational(2, 3)), sympy_integers=True) == "Eq(x, S(2)/3)"`, `sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) == "Limit(x, x, S(7)/2)"` |
| DECLARATION REGISTRY | `self.symbols` / `self.functions` on the `PythonPrinter` subclass, which the caller `python()` emits AHEAD of the composite | the `reg : List Char` argument of `renderSub` and its second result, threaded through each method's `mut reg` parameter | `test_python_relational`: `python(Eq(x, y)) == "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)"` |

A spec that models only the first leg is satisfied by an impl that renders the
sub-objects in the wrong ORDER, or on a fresh serializer of the right
configuration, and such an impl does NOT resolve — measured, see §E. Both legs
are therefore pinned, one `ensures` clause each.

## A. `_print_Relational` — the binary-tagged head (`sympy/printing/str.py:633`)

Gold hunk:
```
- return '%s(%s, %s)' % (charmap[expr.rel_op], expr.lhs, expr.rhs)
+ return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs),
+                        self._print(expr.rhs))
```

| # | Solution.lean impl op (`printTaggedPair`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `tag : List Char` | `charmap[expr.rel_op]` (e.g. `"Eq"`, `"Ne"`) | R | constant ASCII string ↔ `List Char` (mapping.md §2). G-CONF feeds the real charmap value. |
| A2 | params `a b : SubObj`, `cfg : Bool`, `mut reg : List Char` | `expr.lhs`, `expr.rhs`; the active printer's settings; the active printer's declaration registry | R | opaque sub-objects + the boolean configuration + the registry-as-declaration-text (mapping.md §2). `reg` is `mut` because the call being introduced MUTATES the active serializer. |
| A3 | `let ra := renderSub cfg reg a` | `self._print(expr.lhs)` | A-reference | ONE step of the ACTIVE serializer: `.1` is its return value, `.2` is the serializer's registry afterwards, both from the SAME call. Modeled opaquely, validated `== self._print` by G-AX (mapping.md §3.1). Discriminating content, leg 1: under `cfg=true` the text differs from `renderSub false` = the buggy `str(sub)`. |
| A4 | `reg := ra.2` | the side effect of that same `self._print` call on `self.symbols`/`self.functions` (`python.py:31-42`) | A-reference / I | the effect half of A3. In the model it is an explicit assignment because the effect is on the composite's own serializer; in the repo it is the same object being mutated. Discriminating content, leg 2: the buggy `str(sub)` has NO such effect on `self`. |
| A5 | `let rb := renderSub cfg reg b` (with `reg` already advanced) | `self._print(expr.rhs)`, evaluated AFTER the lhs call on the same `self` | A-reference | the second step starts from the registry the first left. Python forces the `%` operand tuple left to right, so this ordering is the gold behaviour, not a modeling choice (asserted by G-AX check 8). |
| A6 | `reg := rb.2` | the second call's effect on the same serializer | A-reference / I | the effect half of A5. |
| A7 | `tag ++ "(" ++ ra.1 ++ ", " ++ rb.1 ++ ")"` | the `'%s(%s, %s)'` format assembly | I | concrete string assembly: head, `(`, first, `, `, second, `)`. Transliterated and diffed by G-CONF. |

Post-images: A7 is `taggedPair cfg tag a b regOld` and the pair (A4, A6) is
`taggedPairReg cfg a b regOld` — the left-to-right two-step fold. G-AX check 8
asserts both against the real arm: the (text, registry) produced by taking the
steps in sequence on ONE printer equals the chained composition of single steps.

The pre-patch arm interpolated `expr.lhs`/`expr.rhs` via `%s` = `str(sub)`,
which builds a fresh default-settings `StrPrinter` with an EMPTY registry and
discards it; in model terms that is `renderSub false []` with the active `reg`
left untouched. `Solution_prepatch.lean`'s `printTaggedPair` reproduces exactly
that (`renderSub false [] a`, then `b` from the throwaway's registry, and `reg`
never assigned) and **fails all four obligations** (G-DIFF): the two `out`
clauses whenever `cfg = true` or the incoming registry is non-empty — the F2P
observation `Eq(x, S(2)/3)` vs `Eq(x, 2/3)` — and the two `reg` clauses
unconditionally (`⊢ regOld = (renderSub cfg (renderSub cfg regOld a).2 b).2`) —
the F2P observation `python(Eq(x, y))` losing both declaration lines.

## B. `_print_Limit` — the ternary head (`sympy/printing/str.py:219`)

Gold hunk (the `dir == "+"` arm):
```
- return "Limit(%s, %s, %s)" % (e, z, z0)
+ return "Limit(%s, %s, %s)" % tuple(map(self._print, (e, z, z0)))
```

| # | Solution.lean impl op (`printLimit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `e z z0 : SubObj`, `cfg : Bool`, `mut reg : List Char` | `e, z, z0 = expr.args` (the `dir == "+"` arm); the active printer's settings and registry | R | as A2 (mapping.md §2). |
| B2 | `renderSub cfg reg e`, then `renderSub cfg reg z` and `renderSub cfg reg z0` with `reg` advanced between them | `tuple(map(self._print, (e, z, z0)))` | A-reference | three steps of the ACTIVE serializer, IN ARGUMENT ORDER: `tuple(map(...))` forces the map left to right, so `z`'s step sees what `e`'s step left. Same opaque model as A3 (mapping.md §3.1); the left-to-right direction is asserted by G-AX check 8 rather than assumed. |
| B3 | `reg := re.2`, `reg := rz.2`, `reg := rz0.2` | the three calls' effects on the same serializer | A-reference / I | the effect halves of B2, in the same order. |
| B4 | `"Limit(" ++ re.1 ++ ", " ++ rz.1 ++ ", " ++ rz0.1 ++ ")"` | the `"Limit(%s, %s, %s)"` format assembly | I | concrete string assembly. G-CONF transliterates and diffs it. |

Post-images: B4 is `limitTriple cfg e z z0 regOld` and B3 is
`limitTripleReg cfg e z z0 regOld`, the three-step left-to-right fold.

The pre-patch arm interpolated `e, z, z0` via `%s` = `str(sub)` =
`renderSub false []`, with no effect on `self`. `Solution_prepatch.lean`'s
`printLimit` reproduces that and **fails both obligations** (G-DIFF): the F2P
observation `Limit(x, x, S(7)/2)` vs `Limit(x, x, 7/2)` on `out`, and the
untouched registry on `reg`. The `else` (non-`+` dir) arm carries a `dir` keyword
and is not exercised by the F2P tests; modeling the `+` arm pins the behavior the
tests demand (mapping.md §1).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — routing each
sub-object through the ACTIVE `self._print` instead of the throwaway
`str()`/`%s` — is captured by BOTH arguments flowing into `renderSub` at the
sub-object render sites: `cfg` (A3/A5/B2) for the configuration leg, and `reg`
plus the write-back (A4/A6/B3) for the registry leg. Neither leg needs a new kind
of step: the registry is a value parameter and a `mut` result, so the effect is
expressed in the same R vocabulary as the text (mapping.md §2, the
declaration-text carrier), and G-AX check 3 asserts that carrier is injective on
the real `(symbols, functions)` state, so nothing is lost in the encoding.

There is no consumed axiom about the function under change; the only modeled
callee (`renderSub`) is the UNCHANGED `Printer._print`, validated by G-AX. Note
what is deliberately NOT modeled: the real registry DEDUPLICATES (`if symbol not
in self.symbols`, `python.py:40-41`). The opaque step assumes nothing of the
kind, so the model is strictly WEAKER than the real callee on that point — the
sound direction — at the cost that the spec pins the reference's COMMITTED call
sequence (each sub-object stepped exactly once *by the composite's own
serializer* — i.e. every step whose result advances `reg`, or whose text is
emitted) rather than its observable-modulo-dedup behaviour. §E records the
measured consequence of that choice.

Stated precisely, because an earlier revision of this section overstated it: what
the two `ensures` pin is the pair of post-images `(out, reg)`, so they pin every
step the impl COMMITS — writes back into `reg`, or emits into `out` — and they
cannot pin an application of `renderSub` that does neither. That is not a gap in
the clauses but a fact about the carrier: such an application does not make a
different program at all (§F proves it, by `rfl`), and mapping.md §2.2 gives the
rule that turns it back into code — a step on a DISCARDED probe, whose behaviour
is gold's, measured. The composite assembly (A7/B4) is concrete (I),
transliterated by G-CONF.

## D. verify(Solution) ⇒ resolved

`printTaggedPair` / `printLimit` verify only if, for each sub-object,

1. it is rendered under the composite's OWN configuration `cfg` (A3/A5/B2) —
   else the first `ensures` fails;
2. it is stepped on the composite's OWN serializer, exactly once, in argument
   order, with the registry written back (A4/A6/B3) — else the second `ensures`
   fails, and (because a later sub-object's TEXT is pinned as the text produced
   FROM the registry the earlier steps left) usually the first as well;
3. the surrounding assembly is the exact format string (A7/B4).

The map is applied in the CODE direction by **mapping.md §2.2**, which is part of
this correspondence rather than an afterthought, because an impl region names
`renderSub` applications and the repo has method CALLS: a written-back result is
a live `self._print(s)` on the active printer (rows A3–A6, B2–B3); a result that
is never written back and never emitted is `self._print(s)` on a discarded PROBE
primed to the active printer's settings and a copy of its registry. The rule is
FORCED — the model's post-state for `reg` is the value the impl assigns, so an
application whose result is discarded asserts that the composite's own serializer
did not advance, and materializing it as a live call would materialize an effect
the impl does not have — and it is SOUND: G-AX check 10 asserts against the real
callee that a primed probe returns the live step's text exactly and leaves the
live `(symbols, functions)` untouched, and G-CONF's probe slice asserts the whole
arm materialized that way is byte-identical to gold's on text, registry, preamble
and end-to-end `python()` output. Without this rule "verify ⇒ resolved" is not
well posed for an impl containing such an application; with it, §F closes that
case by measurement.

By R (`str ↔ List Char`, opaque sub-objects, the boolean configuration, the
declaration-text registry) the verified output and effect equal the gold arm's
`'%s(%s, %s)' % (tag, self._print(lhs), self._print(rhs))` /
`"Limit(%s, %s, %s)" % tuple(map(self._print, (e,z,z0)))` on the tested inputs;
by G-AX the opaque `renderSub` equals one real `self._print` step on both
realizable slices (mapping.md §2.1), the configuration is genuinely observable
(`S(2)/3` ≠ `2/3`), the registry effect AND its order are genuinely observable
and reach the caller's output, and the two arms' folds are exactly the chained
single steps; by G-CONF the R/I transliteration of the assembly AND of the
registry fold agrees with `patch.diff`'s behavior on 3·10⁵ fuzzed comparisons,
including 401 end-to-end `python()` programs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: A-reference soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).

## E. Measured attack ledger — what the second `ensures` closed, and what it costs

This cell was recorded BROKEN on the `verify ⇒ correct` direction (verdict.md,
G-EQ): a rival that swapped the two sub-object renders verified against the
previous spec, and its faithful materialization did NOT resolve. The previous
spec modeled the changed callee as a PURE function of (configuration,
sub-object), so leg 2 of §0 was entirely invisible. The measurements:

| attack shape | verified against the PREVIOUS spec | its faithful patch resolves? | rejected by THIS spec |
|---|---|---|---|
| `atk_2_swap_rel` — render `rhs` then `lhs` | YES (the hole) | **NO** — F2P failure `['test_python_relational']`, P2P 84/84 | YES (both clauses; residual `(renderSub cfg (renderSub cfg regOld b).2 a).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2`) |
| `xtra_fresh_printer` — render both on a fresh printer carrying the same settings | YES (indistinguishable under the pure model) | **NO** — F2P failure `['test_python_relational']` | YES (`⊢ regOld = (renderSub cfg (renderSub cfg regOld a).2 b).2`) |
| `atk_4_dup_render` — render `lhs` twice | YES | yes (resolved=True) | YES |
| `atk_5_swap_limit` — reverse the three ternary renders | YES | yes (resolved=True) | YES |
| `atk_1_extra_step_b` — an extra `renderSub cfg reg b` named before the two steps, result NEVER written back | YES, and still does | see §F — depends entirely on which code it is refined to: the §2.2 materialization resolves=**True**, the auditor's live-call reading resolves=False | NO, and provably cannot be (§F) — shipped as the POSITIVE `pos-tagged-uncommitted-probe` |
| `atk_1d_extra_branch` — the same, with the extra step's text consumed as a branch condition over two identical arms | YES, and still does | §2.2 materialization resolves=**True** (measured, §F) | NO — same program as gold (`simp only [ite_self]`) |
| `weak-tagged-commit-extra-step` — the extra step WRITTEN BACK (`reg := pre.2`) | (not probed then) | **NO** — this is exactly `atk_1_extra_step_b.diff`, F2P failure `['test_python_relational']` | YES (second clause alone; `out` identical at the probed point) |
| `weak-tagged-reuse-probe-text` — the extra step discarded but its TEXT emitted in the second slot | (not probed then) | **NO** — this is exactly `atk_1c_extra_reuse.diff`, F2P failure `['test_python_relational']` | YES (first clause alone; registry identical to gold's) |
| `atk_10_limit_extra` — an extra discarded step on `z0` in the ternary arm | YES, and still does | yes (resolved=True) | NO — the ternary instance of the same boundary (§F) |
| `atk_1b_extra_used` — the extra step's text appended through `List.take 0` | NO (rejected: residual `... ++ List.take 0 (renderSub cfg regOld b).1 = ...`) | — | YES |
| `atk_9_echo` — return the `pure` post-images verbatim | YES (it is the cheapest impl) | yes (resolved=True) | verifies, and is shipped as the POSITIVE `pos-tagged-cheapest` |
| `gold_control` | — | yes (F2P `['test_python_relational','test_Rational']`) | verifies (it is gold) |

Two rows — `atk_4_dup_render` and `atk_5_swap_limit` — are recorded honestly:
their real counterparts DO resolve, so they are not verify-does-not-resolve
breaks, and the strengthened spec rejects them anyway. The reasons differ and both
are benign:

* `atk_4_dup_render` resolves because the real registry deduplicates (§C), a fact
  the opaque one-step model does not assume. The spec pins the reference's
  COMMITTED call sequence — each sub-object advancing the composite's registry
  exactly once, which is what
  `'%s(%s, %s)' % (charmap[...], self._print(lhs), self._print(rhs))` does — so
  the added obligation is one the gold patch satisfies (faithful), it is merely
  stronger than the suite can detect. (It does NOT pin the call MULTIPLICITY;
  §F.)
* `atk_5_swap_limit` resolves because the one place the suite exercises the
  ternary arm is `sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True)`, and
  the printer `sstr` builds carries no declaration registry at all — so the step
  order is unobservable there. The gold arm nonetheless renders in argument order
  (`tuple(map(self._print, (e, z, z0)))`, forced left to right), so again the
  obligation is one gold satisfies.

FAITHFULNESS DIRECTION. Every clause added is satisfied by the modeled reference
— the gold-patched arms — and that is checked mechanically, not argued: G-CONF
compares the strengthened `pure` region (both the assembly AND the registry fold)
against the real patched `_print_Relational` / `_print_Limit` with the gold patch
applied, over 4·10⁵ comparisons on four slices, and reports zero disagreements.
The battery (`properties.py`) additionally ships five positive controls and an
admissibility case showing correct reshapes of the impl still verify, so the
strengthening constrains the BEHAVIOUR and not the shape of the code.

The strengthening was also probed in the other direction before landing: six
wrong impls were built against it and all six were rejected with a semantic
residual goal about `renderSub` (the two step-order swaps, the throwaway
serializer, the duplicated step, the dropped effect, the dropped configuration),
and the reject lane of `properties.py` now carries all seven of the effect-family
shapes — including `weak-tagged-swap-steps`, the first recorded break, and the
two extra-step shapes of §F — each with a witness that discriminates the rival
from gold. The previous battery instead shipped the swap shape as a POSITIVE
control (`pos-tagged-reorder-lets`, "pure `let`s of independent expressions
commute"), which is why that hole survived a green G-PBT; the steps are not
independent once the registry is threaded, and the case has moved lanes.

## F. The extra-step boundary — proved mechanically, not argued

The SECOND recorded `verify ⇒ correct` break against this cell (verdict.md,
G-EQ, measured 2026-08-16T03:39) was `atk_1_extra_step_b`: gold's impl with one
extra `renderSub` application named ahead of it, whose result is never written
back to `reg` and never emitted into `out`.

```lean
    let pre := renderSub cfg reg b     -- named; .2 never written back; .1 never emitted
    let ra := renderSub cfg reg a
    reg := ra.2
    let rb := renderSub cfg reg b
    reg := rb.2
    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
```

The auditor materialized `pre` as a LIVE `self._print(expr.rhs)` on the active
printer, which registers `y` before `x`, so `python(Eq(x, y))` emits the
declarations in the wrong order and `test_python_relational` fails
(`atk_1_extra_step_b.diff`, resolved=FALSE). This section records what was
measured about that. The short form: the *impl* is not a spec weakness (F1, F2)
and the *materialization the auditor chose* is the refinement of a DIFFERENT impl,
which the spec rejects (F3, F4). A later G-EQ pass reproduced both halves
independently, including the resolve split, from its own scratch (F5).

### F1. The rival is not a different program, so no postcondition can reject it

The Velvet carrier has no state monad (`abbrev VelvetM α := NonDetT DivM α`); a
`mut` parameter is compiled into the RETURN TYPE, and the method's denotation is
a function from the inputs to `NonDetT DivM (out × reg)`. An extra `let` binding a
pure value that nothing downstream uses is therefore erased definitionally, not
merely "unobservable in the postcondition". Measured, in a standalone file
(`~/audit_14531v_results/work/probe_call/t2_denote.lean`, real verifier, EXIT=0):

```lean
example (cfg : Bool) (tag : List Char) (a b : SubObj) (reg : List Char) :
    rivalTP cfg tag a b reg = goldTP cfg tag a b reg := rfl

example (cfg : Bool) (tag : List Char) (a b : SubObj) (reg : List Char) :
    rivalBranchTP cfg tag a b reg = goldTP cfg tag a b reg := by
  unfold rivalBranchTP goldTP
  simp only [ite_self]
```

`rivalTP` is `atk_1_extra_step_b`'s impl verbatim and `rivalBranchTP` is
`atk_1d_extra_branch`'s (the `ite_self` shape, where the extra step's TEXT is
genuinely consumed as a branch condition over two identical arms). Both equal
gold **as terms**. The same argument closes the data-dependent shape a later
auditor raised (`atk_3_partial_domain`: `if reg = [] then <extra step; gold> else
<gold>`) — the extra `let` is erased in the `then` arm, so the `if` is
`ite (reg = []) gold gold` and `ite_self` finishes it. Two methods with the same denotation satisfy exactly the same
set of postconditions; gold must satisfy this spec (positive control,
`pos-control.lean` EXIT=0, and G-VERIFY); therefore every strengthening of
`ensures` that keeps gold verifying keeps these two verifying. This is a
mechanical impossibility result about the whole space of `ensures` clauses, not an
observation about the two clauses that are there.

The one escape hatch a state-threading DSL would offer — expose the intermediate
registry to a CALLER and constrain the call sequence there — does not exist in
this backend either. Measured (`t1_thread.lean`, EXIT=1): a caller doing
`let a ← incr reg; let b ← incr reg` gets `a : ℕ × ℕ` (the callee's `(out, reg)`
pair returned as a value) and its own `reg` binder is NOT advanced, so the second
call reads `regOld` again and the caller's obligation `reg = regOld + 2` fails
with residual `⊢ regOld = regOld + 2`. A callee's registry effect is a returned
value, never applied to the caller's binder, so no caller-level obligation can
observe an extra intermediate step either.

The remaining way to "reject" the shape would be to add an observable the
consumer does not have — a step COUNTER in the signature. That is exactly the
unfaithful direction: nothing in the repo observes how many `self._print` calls an
arm makes (the registry deduplicates, §C), and a spec pinning call multiplicity
would reject correct code — `atk_10_limit_extra.diff` (an extra discarded step in
the ternary arm) and the F2-measured materialization below both RESOLVE. So a
counter would trade this cell's `verify ⇒ correct` for `correct ⇒ verify`, not
repair it.

### F2. The impl's refinement RESOLVES, under a rule that is stated and checked

Because F1 forbids closing the shape in the spec, the defect is located in the
REFINEMENT MAP: the map said what every `renderSub` VALUE means and never said
what an APPLICATION of it means, so an auditor was free to read a discarded
application as a live call. mapping.md §2.2 now states the rule (written back → a
live `self._print` on the active printer; never written back → one `self._print`
on a PROBE, a copy of the active printer carrying its settings and a copy of its
registry, discarded), it is FORCED (an application whose result is discarded
asserts that the composite's serializer did not advance, so materializing it live
would materialize an effect the impl does not have, and would make the map
non-monotone — two impls with one denotation refined into two arms with different
behaviour), and it is checked in three places:

* **G-AX check 10** — against the real callee at base_commit, over 5000 fuzzed
  `(registry, sub-object)` pairs on the `PythonPrinter` slice plus a `StrPrinter`
  configuration leg: a primed probe returns the live step's text EXACTLY, leaves
  the live `(symbols, functions)` untouched, and itself ends in the state the live
  step would have produced. Measured: exit 0.
* **G-CONF probe slice (D)** — the composite arm materialized that way, with the
  extra observation in BOTH shapes (dead, and branch-consumed), compared against
  the gold arm on text, registry and declaration preamble on every fuzzed input,
  and end-to-end through `python(expr)` with those arms monkeypatched onto
  `StrPrinter._print_Relational`. Measured: exit 0, `450929 comparisons, 0
  disagreements (seed 14531)`, `436` end-to-end programs byte-identical to gold's.
* **the official harness** — the materialization built as a real patch against
  `base_commit` (`git apply --check` clean) and graded by `run_resolve`:

  | patch | shape | verdict |
  |---|---|---|
  | `pa.diff` (137 lines) | `atk_1_extra_step_b` materialized per §2.2 rule (2) — the arm plus one discarded probe step | **resolved=True**, completed=True [224s], F2P success `['test_python_relational','test_Rational']`, failure `[]`, P2P 84/84 |
  | `pd.diff` (143 lines) | `atk_1d_extra_branch` materialized the same way (the branch-consumed `ite_self` shape) | **resolved=True**, completed=True [119s], F2P success `['test_python_relational','test_Rational']`, failure `[]`, P2P 84/84 |
  | `pp.diff` (138 lines) | `atk_3_partial_domain` materialized the same way — the probe step taken only when the registry is empty (`if not getattr(self, 'symbols', ()) and not getattr(self, 'functions', ())`) | **resolved=True**, completed=True [225s], F2P success `['test_python_relational','test_Rational']`, failure `[]`, P2P 84/84 |

  Both are in `~/audit_14531v_results/work/mat/` with the full report JSON in
  `resolve.log`. So the impl that verifies DOES have a resolving refinement, and
  `verify ⇒ correct` holds for it under the stated map.

Note the probe is not exotic code: `conformance_check.py`'s `py_step` — the shadow
step G-CONF has always diffed against the patched arms — is exactly this
construction, and the pre-patch `str(sub)` of §A/§B is its special case at the
default configuration and the empty registry (mapping.md §2, last two rows).

### F3. The two ways to make the extra step OBSERVABLE are rejected

The boundary is bracketed from both sides by the battery, so the new obligation is
witnessed by G-PBT and not only by the verifier:

| `properties.py` case | shape | expect | measured out-of-band |
|---|---|---|---|
| `pos-tagged-uncommitted-probe` | the `atk_1_extra_step_b` impl verbatim, plus (in the elided tactic body) a `have hprog` proving by `simp` that the extracted program's result IS gold's pair at every input | verify | verifies, 11s |
| `weak-tagged-commit-extra-step` | one line more: `reg := pre.2` — the extra step is COMMITTED | reject | rejected; witness rival=1 gold=0 probe=consistent, 13s |
| `weak-tagged-partial-commit-extra-step` | that commit confined to the `reg = []` slice, gold elsewhere — the partial-domain form of `atk_3_partial_domain` | reject | rejected; witness rival=1 gold=0 probe=consistent, 21s |
| `weak-tagged-reuse-probe-text` | the extra step stays discarded but its TEXT is emitted in the second slot | reject | rejected; witness rival=1 gold=0 probe=consistent, 15s |

`weak-tagged-commit-extra-step` refutes on the SECOND clause alone (its five pins
make `out` identical to gold's and only the out-registry differ: a three-step fold
`b`,`a`,`b` where the spec pins `a`,`b`); `weak-tagged-partial-commit-extra-step`
does the same at a point INSIDE its guarded slice, so the clause is not vacuous on
exactly the slice `python(Eq(x, y))` occupies; `weak-tagged-reuse-probe-text`
refutes on the FIRST alone (gold's registry exactly, but the second segment's text
produced from the composite's INCOMING registry where the spec pins the text
produced from the registry `a`'s step left). Together they say: the moment a
discarded application affects either post-image, the spec sees it.

### F4. Why each of the auditor's three readings is non-conformant

verdict.md materialized the one atk_1 impl three ways and measured all three
resolved=FALSE. Under §2.2 each is the refinement of a DIFFERENT impl, and the
spec rejects all three of those:

| recorded diff | what it does | the impl it actually refines | spec verdict on that impl |
|---|---|---|---|
| `atk_1_extra_step_b.diff` | `self._print(expr.rhs)` LIVE before the arm's own calls | `let pre := renderSub cfg reg b; reg := pre.2; <gold>` | REJECTED (`weak-tagged-commit-extra-step`) |
| `atk_1d_extra_branch.diff` | the same live call, its text used as a branch condition | as above (the branch is `ite_self`, so it changes nothing) | REJECTED (same case) |
| `atk_1c_extra_reuse.diff` | `_pre = self._print(expr.rhs)` and `_pre` interpolated into the SECOND slot | `... return tag ++ "(" ++ ra.1 ++ ", " ++ pre.1 ++ ")"` | REJECTED (`weak-tagged-reuse-probe-text`) |
| `atk_3_partial_domain.diff` (a later G-EQ pass) | the live call confined to the empty-registry slice | `if reg = [] then (let pre := ...; reg := pre.2; <gold>) else <gold>` | REJECTED (`weak-tagged-partial-commit-extra-step`) |

The third row carries a term-level error worth recording, because it is the reason
verdict.md concluded "no reading of atk_1 resolves; this is not a materialization
artifact". Its justification was that "`pre` and `rb` are the same model term
`renderSub cfg reg b` at reg=regOld". They are not: `pre` is
`renderSub cfg regOld b` and `rb` is `renderSub cfg (renderSub cfg regOld a).2 b`
— applications of one opaque function at DIFFERENT registries, hence different
terms, and the whole point of threading the registry through the step (§0 leg 2)
is that they may differ. Substituting one for the other yields a different impl,
and that impl is the rejected `weak-tagged-reuse-probe-text`.

### F5. Independent corroboration — a second reviewer reproduced both halves

The claim of §F is not this bundle's word for it. A later G-EQ pass, working from
its own scratch, re-derived both halves:

* **The impossibility (F1).** It wrote its own strengthened candidate
  (`Solution_v2.lean`) and re-ran the whole family against it. Its
  `v2_atk_A_probe_first` (the dead extra step), `v2_atk_B_probe_branch` (the
  `ite_self` shape), `v2_atk_C_partial` (the data-dependent shape) and
  `v2_atk_E_limit_probe` (the same boundary at the ternary site) all VERIFY,
  EXIT=0 — the shape survived a second, independent attempt to exclude it, which
  is what F1 predicts of a rival that is the same term as gold.
* **The discrimination (F3).** Against that same candidate its
  `v2_atk_F_reuse_text` fails on `ensures_2: out = taggedPair cfg tag a b regOld`,
  and `v2_atk_G_swap`, `v2_atk_H_dup_wb`, `v2_atk_I_dropcfg`, `v2_atk_J_fresh` and
  `v2_prepatch` all fail on `ensures_1: reg = taggedPairReg cfg a b regOld`, while
  `v2_pos_control` verifies. The two clauses are doing work; it is only the
  discarded step they cannot see.
* **The materialization rule (F2), on the reviewer's own diffs.** The same pass
  then materialized A, B and C per mapping.md §2.2 — its diffs cite the rule by
  number and build the probe the way `conformance_check.py`'s `probe_of` does
  (`self.__class__.__new__`, `__dict__.update`, a copied `_settings`, and list
  copies of `symbols`/`functions`) — and its OWN resolve harness measured
  **resolved=True, completed=True** for all three. Its earlier, naive
  materializations of the identical three shapes, which took the extra step LIVE
  on `self`, measured **resolved=False, completed=True**. So the resolve/no-resolve
  split tracks the materialization rule and not the impl, which is exactly the
  location claim of §F2, reproduced end to end by a party that started out
  reporting the shape as a spec break.
* Its other verifying shapes are not holes either, by its own harness:
  `atk_4_echo` resolved=True, `atk_5_limit_extra_z0` resolved=True,
  `atk_9_extra_step_after` resolved=True, and three further PLACEMENTS of the
  discarded step — `v2_atk_K_split_proj` (the two projections taken from separate
  applications), `v2_atk_L_probe_mid` (the extra step between the two committed
  ones) and `v2_atk_M_nested_probe` (a probe inside a probe) — each EXIT=0 and each
  resolved=True. Every shape that got past the two clauses also passed the
  harness, which is `verify ⇒ correct` on the whole family it explored.

### F6. What this section does NOT claim

It does not claim the two `ensures` pin the number of `self._print` calls; they
pin the pair of post-images, which is all a consumer of these arms can read
(§C, corrected). It does not claim a discarded application is impossible to write
in the repo — it is ordinary code, and the probe form is what makes it faithful.
And it does not claim the ternary site is different: `atk_10_limit_extra` is the
same boundary at `printLimit` and its patch resolves (resolved=True, F2P both,
P2P 84/84), recorded in §E, so the two sites agree.
