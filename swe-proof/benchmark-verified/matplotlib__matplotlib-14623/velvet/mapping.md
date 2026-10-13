# mapping.md — matplotlib__matplotlib-14623

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d65c9ca20ddf81ef91199e6d819f9d3506ef477c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the axiomatized callee.

Every line number below was read out of the instance worktree with
`inspect.getsourcelines` at `base_commit` (or, where marked *post-patch*, with
`patch.diff` applied), not from the diff header.

Repo files under change — the gold patch touches three files, and its content is
**two coordinated operations**: a caller-side one with five behaviourally
identical call sites, and a callee-side one with a single site. **Both are
modeled** (§3.3 is the record of why the callee-side one has to be, and of the
earlier revision's error in claiming it did not).

| repo file | changed function(s) | the changed block @ base_commit | modeled as |
|---|---|---|---|
| `lib/matplotlib/axes/_base.py` | `Axes.set_xlim`, `Axes.set_ylim` | `3267-3268` / `3647-3648` (the normalize chain the capture/restore is added around) | `commitLimits` |
| `lib/mpl_toolkits/mplot3d/axes3d.py` | `Axes3D.set_xlim3d`, `set_ylim3d`, `set_zlim3d` | `626-627` / `684-685` / `742-743` | `commitLimits` (same block) |
| `lib/matplotlib/ticker.py` | `Locator.nonsingular` | `1523-1525` | `defaultMemberAdjust` |

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `commitLimits (lo hi : Endpoint)` (`Solution.lean:263`) | the limit-commit block shared **verbatim** by `set_xlim` (`axes/_base.py:3267-3270`), `set_ylim` (`:3647-3650`), `set_xlim3d` (`mplot3d/axes3d.py:626-628`), `set_ylim3d` (`:684-686`), `set_zlim3d` (`:742-744`) | modeled changed operation #1 (caller half): capture the requested orientation, normalize, commit in the requested orientation |
| `normalize` *(axiom — A-consumed, `Solution.lean:212`)* | `self.<axis>.get_major_locator().nonsingular(lo, hi)` **then** `self.<axis>.limit_range_for_scale(lo, hi)`, composed | the callee chain the setter consults; a FAMILY, one member per (scale × major locator) |
| `normalizeRange` *(`:|` stub method, `Solution.lean:236`)* | the same callee chain, reached imperatively | sound-by-construction wrapper exposing `normalize` to the `do` block; declared with the axiom at the SETTER's level, below the member — §3.5 |
| `committedLimits (lo hi : Endpoint)` (`Solution.lean:220`) | the post-patch value of `(left, right)` / `(bottom, top)` committed to `viewLim.interval*` and returned (`axes/_base.py:3270`+`3284`, `:3650`+`3664`; `axes3d.py:628`+`643`, `686`+`701`, `744`+`759`) | pure spec: the orientation-preserving commit |
| `defaultMemberAdjust (e0 e1 : Endpoint)` (`Solution.lean:160`) | `Locator.nonsingular` — the **base** default normalizer member (`lib/matplotlib/ticker.py:1523-1525`; the gold patch rewrites `:1524-1525`) | modeled changed operation #2 (callee half): sort the requested pair, widen the ascending interval, report **that** |
| `expandAscending` *(axiom — A-consumed, `Solution.lean:65`)* | `mtransforms.nonsingular(a, b, expander=.05)` — `lib/matplotlib/transforms.py:2791-2842`, **unchanged** by the gold patch | the shared range widener operation #2 applies to its two sorted arguments |
| `expandRange` *(`:|` stub method, `Solution.lean:143`)* | the same widener, reached imperatively | sound-by-construction wrapper exposing `expandAscending` to the `do` block |
| `defaultMemberPair (e0 e1 : Endpoint)` (`Solution.lean:80`) | the post-patch return value of `Locator.nonsingular` (`ticker.py:1525`) | pure spec: sort-then-widen-then-report-as-is |
| `Endpoint` *(axiom — the carrier, `Solution.lean:27`)* | an axis limit endpoint: a Python `float` (`left`/`right`/`bottom`/`top` at the five setter sites, `v0`/`v1` at `ticker.py:1523`) | the carrier, opaque and order-only — §2 |
| `instEndpointLinearOrder` *(axiom, `Solution.lean:33`)* | `<` / `>` on finite floats | the ONLY structure the carrier carries; what both operations branch on and what the orientation clauses speak about |
| `originEndpoint` *(axiom, `Solution.lean:48`)* | the literal `0` an endpoint's SIGN is tested against (`axes/_base.py:3250-3262` for x, `:3629-3641` for y) | one distinguished endpoint, so that a sign-gated rival is FALSE rather than unsayable (`reject-positivity-gate`) |

**There are five `axiom` declarations. Three are the CARRIER**
(`Endpoint`, `instEndpointLinearOrder`, `originEndpoint`): they introduce no
behaviour, they are the subject of §2 rather than of the callee provenance in
§3, and they are deliberately weaker than a numeric type. **The remaining two
are the consumed callee axioms, and both are bare function types**
(`axiom normalize : Endpoint → Endpoint → Endpoint × Endpoint`,
`axiom expandAscending : Endpoint → Endpoint → Endpoint × Endpoint`). Each of
those asserts that its callee is a **total function of its two arguments** and
**nothing else** — in particular
nothing about the values it returns and nothing about the **order** it returns
them in. §3.2 is the record of why an order assumption on `normalize` would be
false; §3.4 is the record of what `expandAscending` deliberately leaves free, and
of the one measured fact about it (symmetry) that **bounds** the falsification
battery.

The pre-patch repo construct the change adds (refinement audit only, not in the
consumer spec view): **(caller half)** the missing `swapped = <lo> > <hi>`
capture before the chain and the `if swapped: <lo>, <hi> = <hi>, <lo>` restore
after it, at all five sites; **(callee half)** the `Locator.nonsingular` switch
from `increasing=False` to the default `increasing=True`, which removes the
callee-side re-orientation so that the new caller-side restore is the single
orientation authority. The two halves are **coordinated, and each is
independently observable** — each performs one endpoint exchange, so reverting
exactly one of them leaves a net exchange and the committed interval comes out
reversed (§3.3, measured as a hard assertion in `conformance_check.py`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| an axis limit endpoint (`left`/`right`/`bottom`/`top`, a Python `float`) | `Endpoint` (opaque, `LinearOrder` only) | a finite IEEE-754 `float` ↔ an `Endpoint`, carrying `<` on the float to `<` on the carrier and carrying **nothing else**. The modeled behaviour of **both** operations is **order-only plus identity**: one comparison, a select/exchange of two already-received values, and equality with the pair a callee returned. Neither modeled block performs arithmetic on an endpoint — all widening arithmetic lives inside the two axiomatized callees — so the carrier is deliberately arithmetic-free: it cannot even *express* an operation the real blocks do not perform, and no rounding question arises because no rounding step is modeled (CLAUDE.md float rule, satisfied by construction rather than by exactness) |
| the limit pair returned by the chain / the widener / committed to the view | `Endpoint × Endpoint` | `(a, b)` (Python 2-tuple) ↔ `(a, b) : Endpoint × Endpoint`; `.1`/`.2` ↔ `[0]`/`[1]` |
| `swapped = lo > hi` (a Python `bool`) | `lo > hi : Prop` | `>` on finite float ↔ `>` on `Endpoint`: identical truth value |
| `v1 < v0` — the sort test inside `mtransforms.nonsingular` that operation #2 is specified to have performed on its behalf (`transforms.py:2807`, `if vmax < vmin: vmin, vmax = vmax, vmin`) | `e1 < e0 : Prop` | `<` on finite float ↔ `<` on `Endpoint`: identical truth value |

**Domain.** For **both** operations the carrier is the whole of `Endpoint × Endpoint` and
there is **no precondition**: requests of either sign, in either order,
degenerate (`lo = hi` / `e0 = e1`) included. For operation #2 that is forced the
same way — `Locator.nonsingular` is a public method every locator inherits and it
is called with whatever pair the axis holds, including a reversed one (which is
the only interesting case). For operation #1 the total domain is a deliberate
widening over the previous revision of this bundle, which carried
`require 0 < lo` / `require 0 < hi`. That precondition was unfaithful twice over:

* The real block receives non-positive requests. The log-scale non-positive guard
  (`axes/_base.py:3250-3262` for x, `:3629-3641` for y) fires **only** when
  `self.get_<x|y>scale() == 'log'`; on a linear, symlog or logit axis a
  negative or zero endpoint reaches the block untouched. Measured end-to-end on
  the patched tree: `set_ylim(4, -5)` on a linear axis returns `(4.0, -5.0)` and
  `set_ylim(0, 0)` returns `(-0.05, 0.05)`.
* The three mplot3d setters have **no such guard at all** — `set_xlim3d` goes
  straight from `_validate_converted_limits` to the commit block
  (`axes3d.py:589-643`, no `<= 0` test anywhere in the function), so even on a
  log-scaled 3D axis the block is reached with a non-positive endpoint.
* And the F2P test's own pre-existing legs pass `(4, -5)` and `(5, -3)` — one
  endpoint negative — through `set_xlim`/`set_ylim` on a **linear** axis
  (`lib/matplotlib/tests/test_axes.py::test_inverted_limits`). The old
  precondition excluded exactly those inputs, which is how a positivity-gated
  rival could satisfy the old spec while failing the tests.

NaN never enters: `_validate_converted_limits` rejects a non-finite
REQUESTED limit upstream of the block (`float`/`np.float64` NaN and ±inf alike,
with `ValueError`), the chain was measured never to return one, and nothing in
either modeled block manufactures a value at all. ±inf needs no
exclusion, and this is one of the things the opaque carrier buys: the chain CAN
return `inf` on a degenerate extremal request (measured:
`set_ylim(DBL_MAX, DBL_MAX)` commits `(1.7078e308, inf)`), and since an
`Endpoint` is only ever order-compared, that is just one more endpoint —
Q1–Q6 were verified to hold at 60 such non-finite commits, 0 violations
(G-PANEL-2). A numeric carrier would have had to exclude the case or defend
it; this one does neither.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `normalize` ↔ the locator-normalize chain (A-consumed)

**Callee, verbatim:**

```python
lo, hi = axis.get_major_locator().nonsingular(lo, hi)   # _base.py:3647 / 3267
lo, hi = axis.limit_range_for_scale(lo, hi)             # _base.py:3648 / 3268
```

This is a **family**: `get_major_locator()` returns whatever locator the axis
carries and `limit_range_for_scale` dispatches on the axis's scale, so the
composed chain is one function per (scale × major locator) pair. All members are
reached by the *same* commit block. `axiom_check.py` instantiates nine of them
(linear/`AutoLocator`, log/`LogLocator`, symlog/`SymmetricalLogLocator`,
logit/`LogitLocator`, log/`FixedLocator`, linear/`AutoDateLocator`,
`MultipleLocator`, `MaxNLocator`, `NullLocator`).

What the bare axiom asserts, and what G-AX establishes:

* **totality** — the chain answers for every pair the carrier admits, always with
  two endpoints (a log axis fed a non-positive endpoint clamps it to the
  scale's positive floor and warns, `scale.py:428-429`; it does not fail). They
  are finite everywhere except the degenerate extremal request of §2, which the
  order-only carrier models without a special case;
* **functionality / determinism** — the answer depends on the two arguments and
  nothing else: repeat-stable on the same axis, stable when unrelated requests
  are interleaved (no hidden locator state), and identical on a freshly built,
  identically configured axis.

Measured: 9 members × (24 boundary + 4000 fuzzed requests, either sign, either
order, degenerate included) = 36432 observations, zero violations, on both the
base and the patched tree.

### 3.2 Why there is NO `normalize_ascending` axiom any more (load-bearing)

The previous revision of this bundle also assumed

> `normalize_ascending`: the chain returns its two endpoints in ascending order

on strictly-positive distinct endpoints. **That is false of the real callee
family, and it is the reason this bundle needed repair.** The order a member
reports is a property of the member, not of the chain:

| member | `nonsingular` sorts? | source @ base_commit |
|---|---|---|
| `LogLocator` | yes | `ticker.py:2382-2383` — `if vmin > vmax: vmin, vmax = vmax, vmin` |
| `LogitLocator` | yes | `ticker.py:2627-2628` — same two lines |
| base `Locator` (linear default path) | **post-patch** yes | `ticker.py:1525` — `mtransforms.nonsingular(v0, v1, expander=.05)`; `increasing` defaults to `True`, which sorts. At base_commit the same line passes `increasing=False`, which does **not** |
| `matplotlib.dates.DateLocator` | **no** | `dates.py:1218-1229` — the whole body is the degenerate-range widening; there is no `vmin > vmax` test on either tree |

So on a date axis a descending request is handed straight back descending. Both
orders occur **at the same request**, measured on the patched tree:
`normalize(10, 1) = (1.0, 10.0)` for linear/`AutoLocator` but
`normalize(10, 1) = (10.0, 1.0)` for linear/`AutoDateLocator`
(`axiom_check.py`, ORDER CENSUS — a hard assertion, so the refutation cannot
silently lapse).

The consequence for the spec is the whole point of the repair. The reported order
is an **observable**, so instead of *assuming* it (unsound) or *excluding* the
inputs where the assumption fails (a narrowing, which is what the old
`require 0 < lo`/`0 < hi` did), the orientation clauses take it as a
**hypothesis about the pair returned on this call**:

```lean
ensures (normalize lo hi).1 ≤ (normalize lo hi).2 → (lo > hi) → out.2 ≤ out.1   -- Q4
ensures (normalize lo hi).1 ≤ (normalize lo hi).2 → (lo < hi) → out.1 ≤ out.2   -- Q5
ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1) -- Q6
```

and the pair's *identity* is pinned unconditionally over the whole carrier
(Q1/Q2/Q3), which is what actually constrains the operation. G-CONF asserts, as a
hard check, that at least one member of the family **refutes** the unconditional
form of Q4 on real matplotlib output (measured: `Axes.set_xlim` on a date axis,
request `(10, 1)`, normalizer reports `(10.0, 1.0)`, patched code commits
`(1.0, 10.0)` — *ascending*), so "the conditioning is necessary" is a standing
measurement rather than a convenience.

### 3.3 Why `Locator.nonsingular` IS a second modeled operation (load-bearing)

The gold patch's `ticker.py` hunk edits the **base** `Locator.nonsingular`
(`ticker.py:1523-1525`) from `increasing=False` to the default. **The previous
revision of this bundle recorded, here, that the hunk therefore needed no clause,
no do-block operation and no separate prepatch. That was wrong, and it is the
second hole the audit found** (`atk_17_callee_unchanged`): a refinement that
implements the commit block verbatim and leaves `lib/matplotlib/ticker.py` at
`base_commit` satisfied every clause of the old spec and did **not** resolve the
instance. Two steps of the old argument fail.

1. **The hunk is on the failing test's own path, not only off it.** It is true
   that `LogLocator` (`ticker.py:2378`), `LogitLocator` (`:2622`) and
   `matplotlib.dates.DateLocator` (`dates.py:1218`) override `nonsingular` and
   never reach the base method. But the F2P test also drives a **linear** axis,
   whose major locator is `AutoLocator` (`ticker.py:2653`) → `MaxNLocator`
   (`:1882`) → `Locator` (`:1467`), and **neither subclass defines
   `nonsingular`**, so the base method at `:1523` *is* the member reached there.
   Verified textually in the instance worktree and end-to-end by the table below.
2. **The two halves are coordinated, so "the spec asserts nothing about which
   order a member reports" does not make the hunk invisible.** Each half performs
   exactly one endpoint exchange on a reversed request. Under both halves the two
   exchanges compose to the identity on the *reported* orientation and the
   requested order survives; under **neither** half they also compose to the
   identity (which is why base_commit passes the linear legs); but under
   **exactly one** half a single exchange survives and the committed interval
   comes out reversed. Measured, as a hard assertion in `conformance_check.py`
   (`check_halves_independent`), on a linear default-locator axis:

   | request | gold (both halves) | caller half only | callee half only | base_commit (neither) |
   |---|---|---|---|---|
   | `(4.0, -5.0)` | `(4.0, -5.0)` | `(-5.0, 4.0)` | `(-5.0, 4.0)` | `(4.0, -5.0)` |
   | `(5.0, -3.0)` | `(5.0, -3.0)` | `(-3.0, 5.0)` | `(-3.0, 5.0)` | `(5.0, -3.0)` |
   | `(10.0, 1.0)` | `(10.0, 1.0)` | `(1.0, 10.0)` | `(1.0, 10.0)` | `(10.0, 1.0)` |

   The three requests are the F2P test's own **pre-existing** legs, so "either
   half alone" breaks tests that already passed. That is exactly what an
   unmodeled, independently-observable half licenses.

So the hunk is modeled as its own operation `defaultMemberAdjust`
(`Solution.lean:160`) with its own clause block (P1–P4) and its own prepatch twin
`Solution_prepatch2.lean` (gold's commit block + base_commit's member), and
G-DIFF now requires **each** twin to fail. The claim that used to live in this
section as prose is now an executable assertion instead: if the halves ever stop
being independently observable, G-CONF fails rather than a document going quietly
stale.

Because operation #2 is *inside* what §3.1 treats as the `normalize` callee
family, `axiom_check.py` runs on the **patched** tree (`ax_apply_gold: true`):
validating at base_commit would validate a different function from the one the
patched caller consults. Unlike in the previous revision this setting **is** now
load-bearing, because G-AX additionally checks the *member shadow* — that
`Locator.nonsingular(v0, v1)` equals `expandAscending (min v0 v1) (max v0 v1)`,
which is true post-patch and false at base_commit. It has a second consequence,
for the model's call graph rather than for its values, and §3.5 is the record of
it.

### 3.4 `expandAscending` ↔ the shared range widener (A-consumed)

**Callee, verbatim** (`ticker.py:1525`, post-patch):

```python
return mtransforms.nonsingular(v0, v1, expander=.05)
```

`mtransforms.nonsingular` (`lib/matplotlib/transforms.py:2791-2842`) is **not
touched by the gold patch**. It is a single function, not a family, so the axiom
is instantiated once. What the bare axiom asserts, and G-AX establishes over the
24-point boundary set plus 4000 fuzzed pairs (either sign, either order,
degenerate, subnormal, `1e±300`):

* **totality** — never raises; every answer is a pair of finite endpoints;
* **functionality / determinism** — repeat-stable, and unchanged by interleaved
  unrelated widener and member calls (no hidden state).

Nothing about the returned **values** is assumed, and in particular the axiom is
*not* what operation #2 is specified against: P1–P4 pin **which arguments** the
widener is applied to (the sorted pair) and **which order** its answer is
reported in (as reported — not re-oriented). Both of those are the content of the
change; neither is assumed here.

One further fact about the widener is **measured, and it does two jobs**: it is
**symmetric**. It sorts internally
(`transforms.py:2807-2809`, `if vmax < vmin: vmin, vmax = vmax, vmin`) and,
post-patch, the `increasing` un-sort at `:2840-2841` is never requested, so
`expandAscending a b = expandAscending b a` at every probe pair (hard assertion,
`check_widener_symmetric`).

**Job one: it is what makes the factored model of operation #2 faithful.** The
real method is one line, `mtransforms.nonsingular(v0, v1, expander=.05)`, and the
sort happens *inside* the callee; the model instead sorts in the caller and applies
`expandAscending` to the sorted pair (refinement.md B2). Those two denote the same
function exactly because the widener is symmetric. The factorization is what makes
the change *sayable* — P2/P3 pin which arguments the widener is given — so its
soundness condition is asserted rather than assumed, together with the composed
identity `Locator.nonsingular(v0, v1) = expandAscending (min v0 v1) (max v0 v1)`
at every probe (`check_hunk_observable`, MEMBER SHADOW).

**Job two: it bounds the falsification battery.** A whole family of otherwise
attractive rivals for operation #2 — *sort the wrong way round*, *sort
descending*, *gate the sort* — is refutable **only** from the hypothesis
`expandAscending 10 1 ≠ expandAscending 1 10`, which this measurement shows to be
**false of the real callee**. Shipping such a rival would be a forged refutation:
provable in Lean because the axiom is free, but resting on an input the carrier
never realises. Those rivals are therefore deliberately **not** shipped
(`properties.py`, ATTACK FAMILIES / NOT SHIPPED), the honest coverage of that
freedom being P2/P3 (which name the widener's arguments outright) plus G-CONF
executing operation #2 against the real patched member. G-AX asserts the symmetry
so that the omission cannot silently become dishonest if the callee ever changes.

### 3.5 Why the two operations are declared in LAYERS (load-bearing)

§3.3 states — and G-AX's `ax_apply_gold: true` depends on — the fact that modeled
operation #2 is itself a MEMBER of the callee family axiom #1 abstracts. That fact
has a consequence for the model's CALL GRAPH which an earlier revision left
unstated, and G-EQ broke the bundle on it twice: first through the imperative
stub (`atk_12_member_probes_chain`, verdict.md attack 23) and then, once the stub
alone had been fenced, through the PURE axiom and the pure helper written in
terms of it (`atk_01_member_axiom_arg_probe`, `atk_02_member_pure_helper_arg_probe`,
verdict.md attacks 1-2). refinement.md §0.1 carries the full record of both.

A bare pure axiom says nothing about how many times, with what arguments, or from
where its callee is invoked, so a discarded `let _probe ← normalizeRange a b`
inside operation #2's `do` block is invisible to every clause: P1–P4 speak only
about the pair the operation reports, and the probe changes none of it. Refined
per §1/§3.1 that bind is `Locator.nonsingular` calling
`self.axis.get_major_locator().nonsingular` (`Locator` inherits `self.axis` from
`TickHelper`, `ticker.py:220-224`), and on the linear default path
`AutoLocator` → `MaxNLocator` → `Locator` overrides `nonsingular` nowhere
(§3.3 step 1), so the bind re-enters the very method being defined: unbounded
self-recursion, measured as 0/1 F2P and 50/400 P2P on the faithful patch.

No `ensures` can forbid it, because what has to be forbidden is a CALL, not a
value. So the spec forbids it by SCOPE — and the scope has to cover the chain's
whole VOCABULARY, because the pure axiom and the `:|` stub are two NAMES for one
real callee (§3.1 maps both to `get_major_locator().nonsingular` then
`limit_range_for_scale`). Fencing only the stub is not a fence: the second attack
round reached the same recursion through the term `(normalize e0 e1)`, and
through `committedLimits e0 e1`, which is defined by it. There is no reading of
this model on which mentioning the axiom is cheaper than binding the stub —
nothing in the code under specification can learn what the chain reports without
running it.

So the member's level (`expandRange`, then `defaultMemberAdjust`) is declared
ABOVE everything the setter's level owns: the `normalize` axiom, the
`committedLimits` def and its two `@[grind]` lemmas, the `normalizeRange` stub,
and `commitLimits` itself. A declaration can only mention names already declared,
so NONE of those four is in scope inside `defaultMemberAdjust`. The `LAYERING`
block at `Solution.lean:111-138` says so in the spec text itself, and declaration
order is part of the frozen spec view — `same_spec` collapses `impl` regions and
elides `prove_correct` bodies, nothing else — so a rival cannot reorder the file
and remain same-spec. The two moved blocks sit between the levels, outside any
marker region, which is where they have to sit (`markers.py` allows one `axioms`
and one `pure` region per file) and which leaves them just as frozen.

Measured, on the shipped order: `Solution.lean` verifies (exit 0), and every
chain-reaching probe inside the member fails to elaborate — `Unknown identifier
'normalize'`, `'committedLimits'`, `'normalizeRange'`, `'commitLimits'` — while a
discarded duplicate `expandRange a b` probe still verifies, which is correct: a
redundant call to the widener the member really does consult terminates, and the
fence is aimed at the chain, not at probes.

The direction of the layering is forced, not chosen. The setter really does consult
the chain, so the chain's vocabulary must be visible to `commitLimits`; the member
really consults only the widener, so `expandRange` must be visible to
`defaultMemberAdjust`. Exactly one of the two orders satisfies both, and it is the
one shipped.

One battery consequence, recorded here because it is a consequence of the layering
and not of the clauses: the member level can no longer WRITE a rival that answers
with the setter's reference expression, so the ORACLE ECHO rival that used to be
stated there (`reject-member-echo-sibling`) is stated at the setter's level
instead (`reject-echo-sibling-expression`, which commits `defaultMemberPair lo hi`
after consulting and discarding the chain). Same hazard, same discriminating fact,
and the level at which both reference expressions are actually in scope.

## 4. G-CONF: the shadow, the oracle and the seed

`conformance_check.py` seeds `random.Random(14623)`. The **shadow** is the
`commitLimits` `do` block transliterated to Python with `normalize` left as the
**real** matplotlib chain (A-tagged → run the real callee). It is diffed against
two oracles:

* **ORACLE-A, end-to-end**: the five real patched setters themselves, each of
  which returns the pair it committed (`_base.py:3284`, `:3664`;
  `axes3d.py:643`, `701`, `759`). Everything upstream of the modeled block
  (`_process_unit_info`, `_validate_converted_limits`, the `None`-defaulting, and
  at the 2D sites the log guard of `_base.py:3250-3262`/`3629-3641`) is
  transliterated as `upstream_request` so the comparison happens at the block's
  real entry pair rather than by dropping awkward inputs.
* **ORACLE-B, the block** transliterated verbatim from the patched source, which
  carries the ≥10⁵-input volume.

Measured: 146871 observations (19305 of them end-to-end against the five patched
setters), 9 members, 0 disagreements; all six `ensures` evaluated against
matplotlib's own committed pair at every end-to-end observation, 0 violations.

For **operation #2** the shadow is the `defaultMemberAdjust` `do` block
transliterated to Python with `expandAscending` left as the **real**
`mtransforms.nonsingular(a, b, expander=.05)`, and the oracle is the **real
patched `ticker.Locator.nonsingular`** itself (no transliterated stand-in is
needed: the method is one line). Measured: 6029 observations (the boundary set
plus 6000 fuzzed pairs), 0 disagreements, and all four `ensures` (P1–P4)
evaluated against the real member's own output at every one of them, 0
violations. Its 4 rivals are each shown to disagree with the real member
somewhere in the swept domain and its 2 positives to agree with it everywhere,
which is what makes G-PBT's "unprovable against the spec" verdict on those rivals
a statement about matplotlib rather than about Lean.

Finally `check_halves_independent` composes the two operations on a real linear
default-locator axis in all four half-combinations and **hard-asserts** the table
in §3.3. That assertion, not a paragraph, is now what carries the claim that both
halves of the change are load-bearing.
