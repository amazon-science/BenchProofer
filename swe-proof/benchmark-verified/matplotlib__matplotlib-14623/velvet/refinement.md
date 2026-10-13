# refinement.md — matplotlib__matplotlib-14623

Operation-by-operation correspondence between `Solution.lean`'s impl regions and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (the proof uses this axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I.

**The gold patch is TWO coordinated operations, and both are modeled**, so there
are two changed-op sections and two `:|` callee stubs:

| § | modeled changed operation | repo site | its callee stub | its prepatch twin |
|---|---|---|---|---|
| A | `commitLimits` — caller half | the limit-commit block, 5 textually identical sites | `normalizeRange` (axiom `normalize`) | `Solution_prepatch.lean` |
| B | `defaultMemberAdjust` — callee half | `Locator.nonsingular`, `lib/matplotlib/ticker.py:1523-1525` | `expandRange` (axiom `expandAscending`) | `Solution_prepatch2.lean` |

Each twin carries gold's *other* half, so G-DIFF certifies each half separately.
§B records why the callee half has to be modeled — and that an earlier revision of
this document asserted the opposite, which is the hole the audit found.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to the
gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## 0. The carrier, and the LAYERING the two operations sit in

**Carrier.** An axis limit endpoint is modeled by the opaque `axiom Endpoint : Type`
(`Solution.lean:27`) carrying nothing but `instEndpointLinearOrder : LinearOrder
Endpoint` (`:33`), plus one distinguished element `originEndpoint` (`:48`) so that
a sign test is *sayable* rather than unsayable. It is deliberately NOT a numeric
type: both modeled blocks only ever compare two endpoints, hand endpoints to a
callee, and report two of the endpoints they were given, so a carrier with
arithmetic would grant an implementation operations the real code never performs.
mapping.md §2 carries the bijection (a finite IEEE-754 `float`, viewed through `<`
alone, ↔ an `Endpoint`).

**Layering.** The two modeled operations are **not** independent in the repo: the
callee chain `commitLimits` consults is a *family* of `nonsingular` members, and
the member modeled in §B is one of those members (mapping.md §3.3). The spec
therefore declares them in two levels —

| level | declaration | `Solution.lean` |
|---|---|---|
| member level, callee | `method expandRange` (`:|` stub, the shared widener) | `:143` |
| member level, operation | `method defaultMemberAdjust` (modeled changed op #2) | `:160` |
| setter level, vocabulary | `axiom normalize`; `committedLimits` + its two `@[grind]` lemmas | `:212`, `:220` |
| setter level, callee | `method normalizeRange` (`:|` stub, the normalizer chain) | `:236` |
| setter level, operation | `method commitLimits` (modeled changed op #1) | `:263` |

— and the `LAYERING` block at `:111-138` records that this order is **normative**,
because a declaration can only mention what is declared above it. That is what
forbids a member implementation from consulting the chain, and the fence covers
the chain's WHOLE vocabulary, not just the route that looks like a call: the
imperative stub `normalizeRange`, the pure `normalize` its answer is read
through, and the `committedLimits` written in terms of that are all declared
BELOW the member. They have to be. The axiom and the stub denote the SAME real
callee — mapping.md §3.1 maps both to the same two Python lines — so a level that
must not reach it must not be able to name it either way. Refined per mapping.md
§1/§3.1 any of those mentions is `Locator.nonsingular` calling
`self.axis.get_major_locator().nonsingular`, and on the linear default path
(`AutoLocator` → `MaxNLocator` → `Locator`, with neither subclass overriding the
method — the very fact §B relies on) that re-enters the method being defined and
never returns. Declaration order is part of the frozen spec view (only `impl`
regions and `prove_correct` bodies are elided from it), so this is a constraint an
implementation cannot restore. The moved declarations sit BETWEEN the two levels,
outside every marker region: `markers.py` treats the `axioms` and `pure` regions
as singletons, so there is nowhere else to put them — and being outside a region
costs them nothing, because the spec view collapses only `impl` regions and
elides only `prove_correct` bodies.

### 0.1 The two audit findings the layering answers

**Round 1 — the imperative route.** An earlier revision declared the chain stub first and the member last, so the
member's `do` block could bind `normalizeRange`. G-EQ's
`atk_12_member_probes_chain` exploited exactly that: it keeps gold's sort and
gold's `return e` and adds one discarded bind, `let _probe ← normalizeRange a b`.
It is `same_spec` with `Solution.lean` and it VERIFIES — a discarded bind of a `:|`
stub whose `ensures` pins a total pure function is semantically invisible, so
P1–P4 still hold of the reported pair — and yet its faithful refinement does
**not** resolve: 0/1 F2P and 50/400 P2P, because the refined probe is the
unbounded self-recursion just described (verdict.md, attack 23; the unguarded
variant, with no `if self.axis is not None`, behaves identically, so the guard is
not what does the damage).

**Round 2 — the pure route, and why fencing the stub alone was not enough.** The
revision that moved only `normalizeRange` left the pure axiom `normalize` — and
`committedLimits`, written in terms of it — in scope at the member's level, and
the next G-EQ round walked through the gap. `atk_01_member_axiom_arg_probe` keeps
gold's sort and gold's `return e` and adds, inside the member,

```
+    let _junk ← expandRange (normalize e0 e1).1 (normalize e0 e1).2
```

`atk_02_member_pure_helper_arg_probe` does the same through `committedLimits e0
e1`. Both are `same_spec`, both VERIFY, and the first was measured at 0/1 F2P
(`test_inverted_limits`) and 50/400 P2P over three harness attempts, against a
gold control of 1/1 and 400/400 — the same unbounded self-recursion as round 1,
reached by a different name (verdict.md, attacks 1-2).

The premise the earlier prose rested on — that reading a bare `axiom` in a term
position is not a call, so only the `:|` stub needed fencing — is FALSE under this
bundle's own A-legs. A3 and mapping.md §3.1 map the axiom and the stub to the
SAME two Python lines, and in the code under specification there is no way to
learn what that callee reports without running it, so a refinement of either
mention invokes it. The sentence is deleted rather than defended, and the fence
now covers the whole vocabulary. Measured on the shipped order: each of the four
chain-reaching probes — via `normalize`, via `committedLimits`, via
`normalizeRange`, via `commitLimits` — fails to elaborate with `Unknown
identifier`, while a discarded duplicate `expandRange a b` probe, whose
refinement is a redundant call to the widener the member really does consult,
still verifies. The fence blocks the routes into the chain, not probes as such.

Three things are worth stating plainly about the repair. First, it weakens
nothing: not one `ensures` changed, and the rival is not made *false* but made
**unsayable** — which is the honest encoding of "no such call graph exists in the
code under specification". Second, it is not enforceable by a
clause. The freedom being abused is the invisibility of callee *invocations* —
their number, their arguments, their nesting — and no `ensures` written over the
returned pair can observe any of that. Scope is the only instrument the model has,
and declaration order is that instrument. G-PBT cannot carry a regression case
for it either: on this backend an `expect="reject"` case must ship a witness that
discriminates the rival from the frozen solution, and this rival returns exactly
what gold returns, so no such witness exists. What carries the constraint is the
frozen declaration order itself, together with the `LAYERING` block that states
it is load-bearing.

Third, the move cost the battery exactly one case, and that case was REPLACED,
not dropped. `reject-member-echo-sibling` had the member answer with
`committedLimits e0 e1` — a name the completed fence removes from the member's
level, so the case's module no longer elaborates, and a module that does not
elaborate demonstrates nothing about the clauses (on this backend its witness
cannot build either, which is a MALFORMED case rather than a passing one). The
same ORACLE ECHO rival is therefore stated one level up as
`reject-echo-sibling-expression`, where both reference expressions genuinely are
in scope: the setter consults the chain, throws its answer away, and commits
`defaultMemberPair lo hi` instead. Same hazard, same discriminating fact
(`normalize v v ≠ expandAscending v v`, realisable per `axiom_check.py`), same
total: 22 G-PBT cases before the move and 22 after.

## A. The limit-commit site — five textually-identical functions

The gold patch applies the **same** edit at five call sites: `set_xlim` /
`set_ylim` (`axes/_base.py`, base_commit lines `3267-3268` / `3647-3648`) and
`set_xlim3d` / `set_ylim3d` / `set_zlim3d` (`mplot3d/axes3d.py`, `626-627` /
`684-685` / `742-743`). Each gains:

```
+ swapped = lo > hi
  lo, hi = self.<axis>.get_major_locator().nonsingular(lo, hi)
  lo, hi = self.<axis>.limit_range_for_scale(lo, hi)
+ if swapped:
+     lo, hi = hi, lo
```

(`lo,hi` standing for `left,right` / `bottom,top`.) All five sites are the same
operation under the type bijection, so ONE `method commitLimits` models them all,
and G-CONF exercises all five end-to-end.

**No precondition (`pre-conditions` region is EMPTY).** The modeled block is
reached with every pair the carrier admits. The previous revision of this bundle
carried `require 0 < lo ∧ 0 < hi`, justified by the log-scale non-positive guard;
that justification does not survive contact with the source. The guard is
`if self.get_yscale() == 'log': …` (`axes/_base.py:3629-3641`, and `:3250-3262`
for x) — it fires **only on a log axis**, so on linear/symlog/logit a
non-positive endpoint reaches the block untouched; and the three mplot3d setters
have **no guard at all** (`axes3d.py:589-643` contains no `<= 0` test, so the
block is reached straight from `_validate_converted_limits`). The F2P test's own
pre-existing legs push `(4, -5)` and `(5, -3)` through the **linear** path. A
positivity precondition therefore excluded real inputs — including the test's —
and left the operation unconstrained exactly there (mapping.md §2). Widening the
domain to the whole carrier is a strict strengthening: the six clauses below now
have to hold on requests the old spec said nothing about.

| # | Solution.lean impl op (`commitLimits`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `lo hi : Endpoint` (`Solution.lean:263`) | the `left,right` / `bottom,top` floats reaching the block (`_base.py:3267`, `:3647`; `axes3d.py:626`, `684`, `742`) | R | finite `float` ↔ the opaque order-only `Endpoint` (`<` on the float ↔ `<` on the carrier); `_validate_converted_limits` has already rejected non-finite values upstream, and no arithmetic is applied to an endpoint inside the block, so the embedding is exact — and the carrier cannot even express an operation the block does not perform (mapping.md §2). |
| A2 | `let swapped := lo > hi` (`:288`) | `swapped = left > right` / `bottom > top` (the added capture) | I | identical boolean comparison; `>` on finite float ↔ `>` on `Endpoint`. Read **before** the callee: the spec comment at `:286-287` and the clause set both key on the REQUESTED pair, which is the content of the fix. |
| A3 | `let n ← normalizeRange lo hi` (`:289`) | `nonsingular(...)` then `limit_range_for_scale(...)` | A-consumed | the callee chain, modeled by the bare `normalize` axiom; `normalizeRange` is its `:|` stub. The proof consumes **only** that it is a function of the two requested endpoints — no value and no order (mapping.md §3.1-3.2). |
| A4 | `let out := if swapped then (n.2, n.1) else (n.1, n.2)` (`:291`) | `if swapped: left, right = right, left` (the added restore) | I | identical conditional exchange; tuple `.1/.2` ↔ `[0]/[1]`, `if`-swap ↔ `if`-swap. |
| A5 | `return out : Endpoint × Endpoint` (`:292`) | the committed pair, written to `viewLim.interval*` and returned (`_base.py:3270`+`3284`, `:3650`+`3664`; `axes3d.py:628`+`643`, `686`+`701`, `744`+`759`) | R | the committed pair is the observable; the view assignment and the function's return value carry exactly this pair, which is what the F2P test reads back via `get_ylim()`. |

### A.1 What each clause is for, and what makes it true of the real code

| clause | statement | why it is TRUE post-patch | what it refutes |
|---|---|---|---|
| Q1 (`:267`) | `out = committedLimits lo hi` | `committedLimits` is literally A2+A3+A4 in pure form; the patched block computes exactly that at all five sites | any rival that returns some other function of `(lo, hi, n)` — measured against real output at 146871 G-CONF observations |
| Q2 (`:271`) | `lo > hi → out = ((normalize lo hi).2, (normalize lo hi).1)` | the `if swapped:` branch, `_base.py` post-patch `3269-3270` | dropping the restore (prepatch); gating the restore on anything other than `lo > hi` |
| Q3 (`:272`) | `lo ≤ hi → out = normalize lo hi` | the fall-through: `swapped` is false, so the committed pair is the chain's, in the chain's order | swapping when the request did not ask for it (`reject-always-swap`, `reject-cmp-lt`, `reject-cmp-ge`) |
| Q4 (`:278`) | `n.1 ≤ n.2 → lo > hi → out.2 ≤ out.1` | when the chain reported ascending, exchanging its endpoints yields descending | the prepatch on the F2P input, and any rival that keeps the chain's order on a descending request |
| Q5 (`:279`) | `n.1 ≤ n.2 → lo < hi → out.1 ≤ out.2` | an ascending request takes the fall-through, so the ascending report is committed as-is | a rival that swaps on ascending requests (the P2P regression direction) |
| Q6 (`:283`) | `n.1 < n.2 → ((lo > hi) ↔ out.2 < out.1)` | with a strictly ordered report the committed order is descending precisely on the `swapped` branch | the ⇐ direction: a rival that ALSO commits descending for some non-descending request (this is the clause that kills `reject-cmp-ge` at `lo = hi` and `reject-cmp-lt` outright) |

The **antecedents in Q4/Q5/Q6 are the repair**. They are not a narrowing: they
condition on an **observable of this very call** (the order the callee reported)
rather than removing inputs from the domain. Every request stays in-domain and is
still pinned exactly by Q1/Q2/Q3; Q4/Q5/Q6 add the order consequence on the
sub-domain where "orientation" is meaningful at all. Asserting them
unconditionally would be **false of the real patched code**: on a date axis
(`dates.py:1218-1229`, `DateLocator.nonsingular` does not sort) the chain reports
a descending request descending, the patch exchanges it, and the committed pair is
ASCENDING. G-CONF hard-asserts that this counterexample exists, so the
conditioning cannot quietly become gratuitous.

### A.2 The prepatch twin for this half

`Solution_prepatch.lean` keeps gold's `defaultMemberAdjust` (§B) and drops A2/A4 —
its `commitLimits` impl is

```lean
let n ← normalizeRange lo hi
let out := (n.1, n.2)
```

— and **fails** (verifier exit 1) against the frozen spec: Q2 is violated for
`lo > hi` (it commits `(n.1, n.2)`, the spec demands `(n.2, n.1)`), and so is Q4
whenever the chain reported ascending. Measured: the branch the proof script
splits on is no longer there, so `split` fails outright and four goals are left
open — `ensures_5` (Q2), `⊢ (x.1, x.2) = ((normalize lo hi).2, (normalize lo
hi).1)` under `lo > hi`; `ensures_3` (Q4); `ensures_6` (Q1); and `ensures_1`
(Q6). That is exactly the F2P scenario:
`ax.set_yscale("log"); ax.set_ylim(10, 1)` where `LogLocator.nonsingular`
(`ticker.py:2382-2383`) sorts `(10, 1)` to `(1, 10)` and, pre-patch, nothing
swapped back — the axis silently came out ascending. Post-patch,
`get_ylim() == (10, 1)`, measured end-to-end at all five sites (G-CONF).

## B. The `Locator.nonsingular` site — the SECOND modeled operation

Gold hunk (`ticker.py:1523-1525`):

```
- """Modify the endpoints of a range as needed to avoid singularities."""
- return mtransforms.nonsingular(v0, v1, increasing=False, expander=.05)
+ """Expand a range as needed to avoid singularities."""
+ return mtransforms.nonsingular(v0, v1, expander=.05)
```

(`increasing` defaults to `True`; `mtransforms.nonsingular` sorts its arguments
internally at `transforms.py:2807-2809` and un-sorts them again at `:2840-2841`
**only** when `increasing=False` was requested — so dropping the flag is exactly
"stop reinstating the received order".)

**This section previously argued the opposite of what follows.** It recorded that
the hunk "needs no clause", gets "no separate prepatch", and that "the same commit
is correct on either side of it". That was the second hole the audit found
(`atk_17_callee_unchanged`): a refinement implementing site A verbatim while
leaving `lib/matplotlib/ticker.py` at `base_commit` satisfied Q1–Q6 and did **not**
resolve the instance. Two claims in the old argument are false.

* *"Invisible on the F2P path."* `LogLocator` (`ticker.py:2378`), `LogitLocator`
  (`:2622`) and `DateLocator` (`dates.py:1218`) do override `nonsingular`, but the
  F2P test also drives a **linear** axis, whose major locator chain is
  `AutoLocator` (`:2653`) → `MaxNLocator` (`:1882`) → `Locator` (`:1467`) and
  **neither subclass defines `nonsingular`**. The edited base method is the member
  reached there.
* *"The same commit is correct on either side of it."* Each half performs one
  endpoint exchange on a reversed request, so under **both** or under **neither**
  they compose to the identity, but under **exactly one** a net exchange survives.
  Measured on a linear default-locator axis with the F2P test's own pre-existing
  legs (`conformance_check.py::check_halves_independent`, a HARD assertion):

  | request | gold | caller half only | callee half only | base_commit |
  |---|---|---|---|---|
  | `(4.0, -5.0)` | `(4.0, -5.0)` | `(-5.0, 4.0)` | `(-5.0, 4.0)` | `(4.0, -5.0)` |
  | `(5.0, -3.0)` | `(5.0, -3.0)` | `(-3.0, 5.0)` | `(-3.0, 5.0)` | `(5.0, -3.0)` |
  | `(10.0, 1.0)` | `(10.0, 1.0)` | `(1.0, 10.0)` | `(1.0, 10.0)` | `(10.0, 1.0)` |

So the hunk **is** an independently observable changed behaviour and is modeled as
its own operation, `method defaultMemberAdjust` (`Solution.lean:160`), with its own
`:|` callee stub `expandRange` (`:143`) for the unchanged widener.

| # | Solution.lean impl op (`defaultMemberAdjust`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `e0 e1 : Endpoint` (`Solution.lean:160`) | the `v0, v1` floats reaching `Locator.nonsingular` (`ticker.py:1523`) | R | finite `float` ↔ the opaque order-only `Endpoint`; the method applies no arithmetic to an endpoint itself, so the embedding is exact (mapping.md §2). The model's binders are `e0`/`e1` and not the repo's parameter names: the correspondence a reader may rely on is the one this row asserts, not one a name hints at. |
| B2 | `let reversed := e1 < e0` (`:182`) | the sort test the widener performs on the member's behalf once `increasing` is left at its default (`transforms.py:2807`, `if vmax < vmin: vmin, vmax = vmax, vmin`) | I | identical comparison; `<` on finite float ↔ `<` on `Endpoint`. Lifted into the caller position on purpose: *which pair the widener is applied to* is the observable content of the change, and naming it here is what lets P2/P3 pin the widener's arguments instead of assuming something about the widener. The lift is **sound because the widener is symmetric** — it sorts internally and, post-patch, never un-sorts (`transforms.py:2807-2809`, `:2840-2841` unreached), so `expandAscending (sorted pair) = expandAscending e0 e1` and the factored model denotes the same function as the one-line method. That symmetry is not assumed: G-AX hard-asserts it, and hard-asserts the composed identity `Locator.nonsingular(v0, v1) = expandAscending (min v0 v1) (max v0 v1)` at every probe (MEMBER SHADOW). |
| B3 | `let a := if reversed then e1 else e0` / `let b := if reversed then e0 else e1` (`:183-184`) | the sorted `(vmin, vmax)` the widener works on (`transforms.py:2807-2809`) | I | identical select of two already-present values. |
| B4 | `let e ← expandRange a b` (`:185`) | `mtransforms.nonsingular(…, expander=.05)`'s domain adjustment (`transforms.py:2810-2839`) | A-consumed | the unchanged widener, modeled by the bare `expandAscending` axiom; `expandRange` is its `:|` stub. The proof consumes **only** that it is a function of its two arguments — no value, no order (mapping.md §3.4). |
| B5 | `return e` (`:186`) | `return mtransforms.nonsingular(v0, v1, expander=.05)` — the adjusted pair returned **as is** | I | this is the whole hunk: the deleted `increasing=False` is precisely the step that would have re-oriented `e` back to the received order (`transforms.py:2840-2841`), so *not* re-orienting it is `return e`. |

### B.1 What each clause is for, and what makes it true of the real code

| clause | statement | why it is TRUE post-patch | what it refutes |
|---|---|---|---|
| P1 (`:162`) | `out = defaultMemberPair e0 e1` | `defaultMemberPair` is literally B2+B3+B4+B5 in pure form | any rival returning some other function of `(e0, e1, e)`; measured against the real member at 6029 G-CONF observations |
| P2 (`:166`) | `e1 < e0 → out = expandAscending e1 e0` | on a reversed request the widener is applied to `(v1, v0)` and its answer is reported unchanged | `reject-member-restores-order` (the base_commit member, which reinstates the received order) and `reject-member-swap-always` |
| P3 (`:168`) | `¬ (e1 < e0) → out = expandAscending e0 e1` | the fall-through: an ordered or degenerate pair is adjusted in place | `reject-member-degenerate-raw` (a rival that special-cases `e0 = e1` and skips the widener) |
| P4 (`:176`) | `(defaultMemberPair e0 e1).1 ≤ (defaultMemberPair e0 e1).2 → out.1 ≤ out.2` | whenever the adjusted interval is itself ordered, what the member reports is ordered too — **whichever** way round its arguments arrived | the base_commit member on a reversed request, and any rival that reports descending for some request; this is the ORDER form of the same content, and it is the property the caller-side orientation authority (site A) relies on |

P4 is the analogue of Q4/Q5/Q6 and is conditioned the same way and for the same
reason: whether the *widener's* interval is ordered is an observable the member is
not entitled to assume (nothing in the axiom says the widener orders its answer),
so P4 takes it as a hypothesis about this call rather than asserting it. No input
leaves the domain — P1/P2/P3 pin every request unconditionally.

### B.2 The second prepatch twin

`Solution_prepatch2.lean` carries **gold's** `commitLimits` and **base_commit's**
member — its `defaultMemberAdjust` impl reinstates the received order:

```lean
let e ← expandRange a b
let out := if reversed then (e.2, e.1) else (e.1, e.2)
return out
```

It **fails** (verifier exit 1) against the frozen spec, with `ensures_4` (P1),
`ensures_3` (P2) and `ensures_1` (P4) unsolved — e.g.
`⊢ (if e1 < e0 then (x.2, x.1) else (x.1, x.2)) = defaultMemberPair e0 e1`.
`Solution_prepatch.lean` is the mirror image (gold's member, base_commit's commit
block) and fails on Q2/Q4. Both are `same_spec` with `Solution.lean`, so G-DIFF
now certifies that **each half of the change is independently refuted**: neither
can be dropped while the other is kept.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. **Both** operations that genuinely changed are modeled
**concretely**: A2/A4 are **I** (the `do` block literally captures `swapped` and
conditionally exchanges) and B2/B3/B5 are **I** (the block literally sorts and
returns the widener's answer unchanged). Neither half is hidden behind an axiom
about the function under change. The two consumed axioms cover **callees only** —
the per-scale normalizer chain and the unchanged shared widener — and both are
bare function types, granting their callees total freedom over values and over
order, so no part of the change is smuggled into an assumption. In particular
`expandAscending` is deliberately *not* assumed to order its answer; P4 conditions
on that instead.

One thing the model does **not** leave free is the CALL GRAPH. The two operations
are declared in two levels and an operation can bind only the stubs above it (§0),
so the member cannot consult the chain it is itself a member of. That is a SCOPE
constraint, not an assumption about a callee: it removes an implementation the repo
cannot execute, rather than granting the model a fact nobody measured.

## D. verify(Solution) ⇒ resolved

`commitLimits` verifies only if the committed pair is the callee's pair
transposed exactly on `lo > hi` (Q1/Q2/Q3) and, whenever the callee reported an
ordered pair, only if the committed order matches the requested one in both
directions (Q4/Q5/Q6). `defaultMemberAdjust` verifies only if the member reports
the widener's answer on the **sorted** pair, un-re-oriented (P1/P2/P3), and hence
ordered whenever the widener's own answer is (P4). By R (`finite float ↔ Endpoint`,
tuple ↔ pair, no arithmetic on endpoints in either block) the two verified
operations equal the five gold `set_*lim*` commit blocks and the gold
`Locator.nonsingular` on every finite request — which is the whole gold patch.
Evidence:

* **G-AX** — both bare axioms are sound for their real callees. `normalize`: 9
  members of the (scale × major locator) family, 36432 observations, on both
  trees; and the order the family reports is measured to differ **between members
  at the same request**, so no order assumption is being smuggled in.
  `expandAscending`: the boundary set plus 4000 fuzzed pairs, total and
  deterministic. The probe additionally hard-asserts the three facts the second
  operation's model rests on — the hunk is **observable** (post vs base_commit
  disagree at 4/4 reversed probes), the widener is **symmetric** (which is what
  makes the caller-side sort in B2 faithful, and what makes one rival family
  honestly droppable), and the composed member equals
  sort-then-widen-then-report — plus the realisability of every conditioning
  hypothesis both batteries' witnesses use.
* **G-CONF** — the R/I transliteration of the `commitLimits` block agrees with the
  real patched code on 146871 observations, 19305 of them **end-to-end against the
  five patched setters themselves**; all six `ensures` hold of matplotlib's own
  committed pair at every one of those; the F2P leg (log axis, `(10, 1)` commits
  `(10, 1)`) and the regression legs (`(4, -5)`, `(5, -3)` verbatim on a linear
  axis) are pinned at all five sites; each of the 11 rivals is measured to
  disagree with the real code and each of the 3 positives to agree everywhere. The
  `defaultMemberAdjust` block agrees with the **real patched
  `ticker.Locator.nonsingular`** on 6029 observations with all four `ensures`
  holding of the real member's own output, its 4 rivals discriminated and its 2
  positives agreeing. And `check_halves_independent` **hard-asserts** the §B table:
  each half of the change is load-bearing on the F2P test's own pre-existing legs.
* **G-DIFF** — **both** prepatch twins fail the frozen spec (§A.2, §B.2), and both
  are `same_spec` with `Solution.lean`, so neither half can be dropped.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly two: axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ + G-CONF). Note what changed about the second: the
one claim this document previously made *only* in prose — that the `ticker.py`
hunk was not independently observable — turned out to be false, so the successor
claim is carried by an executable assertion in `conformance_check.py` instead of
by a paragraph.
