# refinement.md — django__django-9296

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`enumeratePages` `do` block, the deep `pageSeq` model, and the opaque `pageOf`
reference) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses the
axiom's `ensures`, **A-reference** where a deep/opaque model is validated == the
real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The iteration site — `Paginator.__iter__` (`django/core/paginator.py:37`)

Gold hunk:
```
+ def __iter__(self):
+     for page_number in self.page_range:
+         yield self.page(page_number)
```

| # | Solution.lean impl op (`enumeratePages`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `pageRange : List PageIdx` | `self.page_range` (the loop iterable) | R | `range(1, num_pages+1)` ↔ `List PageIdx`, materialized in order (mapping.md §2). Well-typed because `list(page_range) == [1 … num_pages]`, i.e. every element carries the membership `PageIdx` demands — asserted by axiom_check.py, and the reason the refinement needs no side condition here. G-CONF bridges by materializing the real `page_range`. |
| A2 | the backward `while` walks `pageRange` in order, building `result` | `for page_number in self.page_range:` | I | the loop visits each index once, left-to-right (the backward fold prepends, so the materialized `result` is in original order). Concrete control flow, transliterated by G-CONF statement for statement. |
| A2' | `let p := pageRange[i - 1]?`, then `(p.map pageOf).toList` | (no counterpart — Python's `for` cannot read out of range) | R | the read is an `Option` rather than a total index because `PageIdx` has **no `Inhabited` instance**, so `pageRange[i - 1]!` does not elaborate (measured: `failed to synthesize Inhabited PageIdx`). Under the loop invariant `0 ≤ i ≤ pageRange.length` with `i > 0` the index is always in range, so the `none` branch is unreachable and `(p.map pageOf).toList` is the singleton `[pageOf pageRange[i-1]]` — exactly one `page` call per iteration, matching the `for`. G-CONF carries the same `Option` shape in its shadow. |
| A2'' | the counter arithmetic `i := pageRange.length`, `i - 1`, `i := i - 1`, and the guard `i > 0` | the `for` loop's own iteration (no explicit counter) | R | these are `Nat` operations, **not** integer operations: `Nat.sub` truncates at 0. They are realized per mapping.md §2.1 (`a - b` → `a - b if b <= a else 0`), which is what G-CONF's shadow executes (`nat_sub`). Realizing them with Python's signed `-` would be a change of algebra, not a refinement — see §B''. |
| A2''' | any other arithmetic a verified impl performs — an `Int` computed from a sub-view (`pageOf p` is a `List Int`), an `Int` division or remainder, a `.toNat`, a coercion into a fixed-width or `Float` type, or a closed literal expression in any type | (no counterpart — the gold `for` computes nothing but the iteration) | R | realized per mapping.md §2.1's two RULES, not per operator spelling: a CLOSED sub-expression is realized by the value Lean evaluates it to (R0), and an OPEN one by a total Python function extensionally equal to the Lean operation (R1). `Int` is a third algebra — Euclidean and total, so `(1 : Int) % (-2) = 1` where Python answers `-1`, and `a / 0 = 0` where Python raises. Fixed-width types wrap, `Float` answers `±inf`/`nan`. See §B'''. And a COMPOSITE is realized from its OWN defining equation, never by chaining the rows of its parts through an intermediate Python cannot represent (R2): `(List.range n).length` realizes as `n`, not as `len(list(range(n)))`, because Lean's `List.length` is unbounded where CPython bounds every container and every `len` by `ssize_t`. See §B''''. |
| A3 | `pageOf p` for each index `p` | `self.page(page_number)` | A-reference | `page` is **unchanged** by the patch; `__iter__` only calls it. Modeled as the opaque map `pageOf : PageIdx → List Int` — never pinned to a value, the proof relies only on the SAME map applied to every index. Its argument type is the accessor's real DOMAIN (`1 ≤ n ≤ num_pages`, exactly the integers `validate_number` accepts), so the model is total where `page` returns and inexpressible where `page` raises `EmptyPage`. G-AX validates `pageOf == real page` (determinism + independence + the domain, both directions). mapping.md §3.1. |
| A4 | `result := pageOf p :: result`; `out = pageSeq pageRange` | `yield self.page(page_number)` (generator emits each page in order) | I | the spec pins `out` to the ordered family `pageSeq pageRange` = `[pageOf p for p in pageRange]`; the generator yields exactly that sequence, in that order. The fold ops (`::`, the loop) are concrete (I); the equality of the materialized generator to this family is the A-reference (A3). |

Discriminating content of the change — the object becomes iterable and iteration
produces *one sub-view per index in order* — lives in `out = pageSeq pageRange`.
Pre-patch the object exposes **no** iteration protocol, so `list(iter(...))` would
fail (`TypeError`); the faithful skeleton of "nothing is produced" is the empty
result `[]`, which **fails** `out = pageSeq pageRange` whenever `pageRange` is
non-empty (G-DIFF: the discriminating goal `pageSeq pageRange = []`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the iteration
protocol — is modeled **deeply** (the spelled-out fold `pageSeq` over the opaque
per-index accessor `pageOf`), not hidden behind a contract about the function
under change. The only A leg, `pageOf` (A-reference), covers an **unchanged**
callee (`Paginator.page`) and is validated executably by G-AX, never consumed as
an `ensures`. There is no consumed axiom.

## B'. The accessor's domain is carried, not totalized

`Paginator.page` is a **partial** operation on the integers: `validate_number`
raises `EmptyPage` for every `n < 1` and every `n > num_pages`
(`django/core/paginator.py:37`), so `dom(page) == [1 … num_pages] ==
list(page_range)` exactly — measured in both directions by axiom_check.py
property (c). The model carries that domain in the index type
(`PageIdx = {n : Nat // 1 ≤ n ∧ n ≤ numPages}`) instead of extending the accessor
to answer everywhere.

**Why this matters for `verify ⇒ resolved`, and not merely for elegance.** An
earlier revision of this bundle modeled the accessor as a total
`pageOf : Nat → List Int`. A value-only postcondition (`out = pageSeq pageRange`)
constrains only the returned value, so under a total accessor an implementation
could apply it at an index the object does not name, **discard** the result, and
still verify — while its faithful Python counterpart raises `EmptyPage` at that
call and does not resolve the target test. That is the hole recorded against this
cell (G-EQ / G-PANEL-1, 2026-08-16: the attack variant verified; its counterpart
failed FAIL_TO_PASS 1/1 with PASS_TO_PASS 20/20 still passing), and totality drift
of a partial callee is its whole content: not a missing clause, but an operation
the model let the impl perform for free.

The carrier closes it by making the off-domain application **ill-typed**, which is
strictly stronger than leaving it unadmitted — measured, one build each:

* `pageOf ⟨1, …⟩` at an index built from the *argument*'s length rather than the
  object's count fails with `omega could not prove the goal: a possible
  counterexample may satisfy the constraints … where a := ↑pageRange.length,
  b := ↑numPages`. The bound belongs to the OBJECT, so no length of the input can
  discharge it. (`numPages` is `opaque` for exactly this reason: a definition
  readable off the argument would be widened by a longer argument.)
* discharging that membership with `sorry` is the only remaining route, and it
  exits 3 — banned by G-HYGIENE and by the G-PBT witness screen.
* the sibling drift, a **total** out-of-range list read producing a junk index,
  is unavailable too: `pageRange[pageRange.length]!` fails with `failed to
  synthesize Inhabited PageIdx`, as do `.head!`, `default` and
  `Classical.arbitrary`; `#synth Nonempty PageIdx` fails likewise. The ABSENCE of
  an `Inhabited PageIdx` instance is load-bearing and must not be added: an index
  can only be received from the caller or built from the object's own count under
  a proof.

**The restriction is the accessor's real domain, not an over-restriction** — also
measured, and shipped as battery cases rather than asserted:

* `pos-control-in-domain-selection` (G-PBT) applies the accessor at an index it
  *proves* the object names, discards the result, and **verifies**. So extra
  accessor applications are not what the carrier forbids; off-domain ones are.
* `admiss-accessor-domain-carried` (G-PBT) discharges, in-region,
  `∀ p : PageIdx, 1 ≤ p.val ∧ p.val ≤ numPages` — every index any implementation
  of this method can name is one the real accessor admits. Live: the same assert
  claiming `2 ≤ p.val` fails with a type mismatch naming the carrier's real bound.
* three structurally different faithful implementations verify (the frozen
  backward loop, a forward loop with a `take i` invariant, and the loop-free
  closed form), so nothing about a legitimate traversal is being rejected.

**What still gets through the type, and is rejected by the clause instead.** The
carrier removes the *unguarded* off-domain call; a variant may still ask for a
different named index, or guard the call and fall back when the index is not
named. Both survivors are shipped as G-PBT reject cases with machine-checked
refutation witnesses — `partial-domain-shifted-index` (the recorded attack in its
expressible form: ask for the index one past each one requested, empty sub-view
when the object does not name it) and `value-indexed-by-position` (index by
position rather than by value). The first one's faithful counterpart does **not**
resolve: on the target test's 2-sub-view fixture the first pulled sub-view is the
second one, so the first subtest fails. So the class is closed on both sides —
inexpressible where it was unguarded, refuted where it is guarded.

## B''. `Nat` arithmetic is realized, not reinterpreted

**The recorded defect** (G-EQ / G-PANEL-1, 2026-08-16 — the SECOND finding
against this cell, a different dimension from §B'). Two implementations of this
method verify, and the Python counterparts submitted with them do not resolve:

* **`atk_15`** prefixes the impl with
  `let _z : Nat := pageRange.length / (pageRange.length - pageRange.length)` and
  starts the counter at `pageRange.length + _z`. In `Nat`, `n - n` is `0` and
  `n / 0` is `0`, so `_z = 0` and the traversal is the frozen one: it VERIFIES,
  and correctly. Its counterpart wrote
  `len(self.page_range) // (len(self.page_range) - len(self.page_range))`, which
  raises `ZeroDivisionError`. Harness: `resolved=false, completed=true`,
  FAIL_TO_PASS 0/1 (`test_paginator_iteration`), PASS_TO_PASS 20/20 passing.
* **`atk_13`** prefixes a second loop, `k := pageRange.length + 1;
  while k ≠ 0 … k := k - 2`, whose measure `k` provably reaches `0` because `Nat`
  subtraction saturates — from an odd start the step floors at `0` instead of
  passing it. It VERIFIES under `TotalCorrectness`, and correctly. Its
  counterpart wrote `k = k - 2` on a Python `int` and counted `1, -1, -3, …`
  forever. Harness: `resolved=false, completed=false, "Test timed out after 3600
  seconds"`. A gold control resolved in the same batch.

**The defect is not a missing clause, and that is measured rather than argued.**
Both shapes were rebuilt with bare `Nat` LITERALS in place of every spec symbol —
`let _z : Nat := 5 / (5 - 5)` (exit 0) and `let mut k : Nat := 7` with the same
countdown loop (exit 0). Both still verify, and neither mentions one symbol of
this specification: not `pageRange`, not `numPages`, not `pageOf`, not `out`. A
postcondition is a predicate on the inputs and the output, so no clause that can
be added to the spec region distinguishes a module containing such a prologue
from one that does not — and no clause could constrain the local in any case,
whose value is discarded or provably neutral. Strengthening the spec is therefore
not merely insufficient against this class; it is inexpressible. What both
counterparts do share is a step in the other direction, and it is a step this
document is responsible for: each translated a Lean `Nat` operation into the
same-looking Python `int` operator.

**Those are different algebras.** Lean's `Nat` is total, and total by
SATURATION: `a - b` floors at `0`, `a / 0` is `0`, `a % 0` is `a`. Python's `int`
subtraction is signed and Python's `//` and `%` raise on a zero divisor. So `-` ↔
`-` and `/` ↔ `//` is not a refinement of the type abstraction at all; it is a
silent change of algebra, under which an expression that is *defined* on the Lean
side becomes one that raises, and a loop that is *proven to terminate* on the
Lean side becomes one that diverges. The earlier revision of mapping.md §2 said
only that "`Nat`/`List` indexing is total and sound", which asserted the
conclusion and licensed exactly that reading. **mapping.md §2.1 now fixes the
realization of every `Nat` operation** (`a - b` → `a - b if b <= a else 0`,
`a / b` → `a // b if b != 0 else 0`, `a % b` → `a % b if b != 0 else a`; `+`, `*`,
`^` and the comparisons are the same functions on both sides and realize as
themselves), and states the two consequences that make the leg load-bearing:
definedness transfers, and the `TotalCorrectness` termination proof transfers —
the latter *only* because the realized step performs the same saturating
arithmetic. This paragraph is about `Nat` and it is scoped to `Nat`: for why that
scoping was itself the next defect, and for the general law that replaced it, see
§B'''.

Realization is a translation, not a licence to omit. Each `Nat` operation is
realized by its total counterpart; nothing is deleted. And the A-tagged leg is
untouched: an application of `pageOf` (A3) is realized as a real call to
`Paginator.page` and may never be elided or replaced by a model, which is what
keeps §B''s closure of the accessor class in force. This section changes nothing
about §B'.

**Measured: under the corrected realization both counterparts resolve.** Both
patches are the attacks' own patches with only the two arithmetic realizations
substituted — `max(0, _n - _n)` for the `Nat` subtraction and a zero-divisor
guard for the `Nat` division in `atk_15`, `max(0, k - 2)` for the `Nat`
subtraction in `atk_13` — run through the Docker correctness oracle
(`swebench_unified.harness.run_resolve`, one attempt each, this bundle's frozen
instance record):

| patch | `resolved` | `completed` | FAIL_TO_PASS | PASS_TO_PASS |
|---|---|---|---|---|
| gold (control) | **true** | true | 1/1 | 20/20 |
| `atk_15` realized per §2.1 | **true** | true | 1/1 | 20/20 |
| `atk_13` realized per §2.1 | **true** | true | 1/1 | 20/20 |

So the verified modules were right and their submitted patches were
mistranslations: correcting the map, not the spec, is what closes the class.

**Where the teeth are.** The correction is executable on both sides and shipped
as cases, not asserted here:

* `conformance_check.py` defines `nat_sub`/`nat_div`/`nat_mod`, performs every
  `Nat` operation in its shadow through them (the impl's `i - 1` and `i := i - 1`
  included), and `check_nat_algebra` measures them exhaustively on `[0,96)²`
  against four `Nat` laws — plus non-vacuity checks that they really differ from
  Python's own `-` and `//`. Run by G-CONF, in-container, every re-gate.
* `admiss-nat-semantics-carried` (G-PBT) discharges the SAME four laws in-region,
  with the frozen impl and the frozen proof body byte-for-byte. Live against
  three negative controls, each leaving the false claim as the residual goal; the
  sharpest drops the hypothesis from `b ≤ a → (a-b)+b = a`, which fails precisely
  *because* the subtraction truncates.
* `pos-control-dead-nat-arith` and `pos-control-dead-saturating-loop` (G-PBT) are
  the two attack shapes themselves, as POSITIVES — they verify, and they must, so
  the battery itself records that the failure of the submitted counterparts is
  attributable to the translation and not to the spec.
* `truncated-arith-drop-last` (G-PBT) is a reject rival that routes its bug
  *through* the saturating subtraction: its bound `pageRange.length - 1` is
  correct on the empty run only because `Nat.sub` truncates there. So the algebra
  is exercised in the reject lane too.

**What is not closed, stated plainly.** The realization fixes what each operation
MEANS, not what it COSTS. A counterpart that is semantically identical but
astronomically slower would still exhaust the harness's wall clock and be recorded
as `completed=false`. That is a cost dimension, orthogonal to definedness, and it
is not one this map (or any refinement map in this corpus) claims a bound on: the
same latitude exists for the gold patch. Nothing above weakens on it — `atk_13`'s
divergence was a definedness failure, not a cost one, and it is closed — but a
`verify ⇒ resolved` claim in this bundle is a claim about behaviour, not about
running time.

> **Correction (§B'''', 2026-08-16).** This paragraph originally named its
> "classic shape" as *a `Nat` computed by materializing a huge `List.range`*, and
> that example was WRONG — it was a definedness failure filed as a cost one. The
> fourth recorded finding submitted exactly that shape, and the counterpart's
> `len(list(range(2 ** 64)))` does not run slowly: it raises `OverflowError`
> immediately (~1e-5 s, measured), because CPython bounds every container and
> every `len` by `ssize_t`. §B'''' records the finding and closes it with rule R2.
> The cost caveat above stands as stated — with no worked example, because the one
> it had turned out to belong to the definedness class this map does close.

> **Second correction (§B''''', 2026-08-16).** The caveat above is now SPLIT, and
> most of it is closed. "Astronomically slower" conflates two things: a program
> that returns the right answer late, and a program that does not return at all.
> The fifth recorded finding submitted the second — a loop annotated
> `done_with k = 0` whose schedule is `2 ^ (64 + n)` iterations — and a `while` that
> runs `2^64` times is not a slow total function, it is not a function (measured:
> `completed=false` after 3 708–3 795 s, against 118.2 s for the frozen control in
> the same batch). R1's own criterion therefore convicts the transliteration, and
> §B''''' closes that half with rule R3: an annotated STATEMENT is realized by its
> DENOTATION. What survives of this paragraph is genuine cost only — a realization
> that computes the right value by a worse algorithm (a quadratic `insert(0, …)`
> where Lean's `::` is O(1), say) — and there the latitude really is symmetric with
> the gold patch.

## B'''. The realization is a LAW over every type, not a table for one

**The recorded defect** (G-EQ / G-PANEL-1, 2026-08-16 — the THIRD finding against
this cell, and the same defect as §B'' one type over). §B'' closed the arithmetic
class for Lean `Nat`. mapping.md §2.1's table was headed "| Lean `Nat` operation |
Python realization |", its teeth were `nat_sub`/`nat_div`/`nat_mod` and
`check_nat_algebra`, and this document generalized the remainder with the phrase
"the rest identity". Lean `Int` is a THIRD algebra, it is spec-visible
(`pageOf : PageIdx → List Int`, `out : List (List Int)`), and nothing on either
side of the bundle exercised it. Three implementations verify — all three exit 0,
all three same-spec — and the faithful Python counterparts submitted with them do
not resolve:

* **`atk_1` (definedness).** Prologue
  `let _z : Nat := ((pageRange.length : Int) / 0).toNat`, counter
  `pageRange.length + _z`. In `Int`, division by zero answers `0`, so `_z = 0` and
  the traversal is the frozen one: it verifies, and correctly. Its counterpart
  wrote `int(len(page_range)) // 0`, which raises `ZeroDivisionError`. This is the
  EXACT shape §B'' claimed to close, written one type over, and the row that closed
  it (`a / b` → `a // b if b != 0 else 0`) did not reach it because the row was
  `Nat`-only. Harness: `resolved=false, completed=true`, FAIL_TO_PASS 0/1
  (`test_paginator_iteration`), PASS_TO_PASS 20/20 passing.
* **`atk_2` (convention — the sharpest of the three).** Prologue
  `let d : Nat := ((1 : Int) % (-2)).toNat`, counter
  `pageRange.length + d - 1`. Lean's `Int.emod` is the NON-NEGATIVE-remainder
  convention, so `1 % -2 = 1`, `d = 1`, the bound is `length + 1 - 1 = length`, and
  the traversal is again the frozen one: verifies, correctly. Python's `%` is
  FLOORED, so `1 % -2 == -1`, `d` realizes to `0`, the bound becomes `length - 1`,
  and the LAST sub-view is dropped — the F2P test's second `next()` raises
  `StopIteration`. Harness: `resolved=false, completed=true`, F2P 0/1, P2P 20/20.
  **Nothing is partial anywhere in this one**: both operands are total in both
  languages and no zero divisor occurs, so §B''s zero-divisor guards could not
  have caught it even had they been typed generically. It is a pure disagreement
  about which of two integer division conventions the `%` character denotes.
* **`atk_4` (the value is consumed by CONTROL FLOW).** The loop body becomes
  `if ((1 : Int) % (-2)) < 0 then result := result else result := … ++ result`.
  In Lean `1 < 0` is false, so the prepend always happens: verifies, correctly. In
  Python `-1 < 0` is true, the guard flips, and the iterator yields nothing at all.
  Harness: `resolved=false, completed=true`, F2P 0/1, P2P 20/20.

Controls in the same batch: `ctl_frozen` and `gold` both `resolved=true`, 1/1,
20/20. So the three are discriminated against an honest counterpart, not against a
broken harness.

**Why this is a map defect and not a missing clause — and why the previous
statement of that argument was too weak.** §B'' argued that no clause can
constrain a local whose value is discarded. `atk_4` refutes that framing: its
value is not discarded, it decides a branch, and a branch decides the output. The
argument that actually holds is about CLOSEDNESS, and it was measured here the
same way §B'' measured its own: the discriminating prologues were rebuilt with
bare `Int` literals and nothing else — `let d : Nat := ((1 : Int) % (-2)).toNat`
mentions `Int`, two numerals and `toNat`, and not one symbol of this
specification: not `pageRange`, not `numPages`, not `pageOf`, not `out`. Both the
literal-only rebuild and the auditor's own version verify (exit 0). A
postcondition is a predicate on the inputs and the output; a closed term denotes
the same value in every module; so no clause addable to the spec region can
distinguish a module containing such a prologue from one that does not. That is
inexpressibility, and it does not depend on where the value flows afterwards.

**What was corrected, and it is not another row.** Adding `Int` rows would have
left the same defect available in the next type — the auditor could have written
`(200 : UInt8) + 100` instead, and that shape verifies too (measured, exit 0).
mapping.md §2.1 is therefore now a LAW with an instance table under it:

* **R0** — a closed sub-expression is realized by the value Lean evaluates it to.
  This kills the entire literal-prologue family at once, in every type, present or
  future, because the realization of `((1 : Int) % (-2))` is `1` and not whatever
  those characters mean to Python.
* **R1** — an open term is realized by a TOTAL Python function extensionally equal
  to the Lean operation under the §2 bijection, derived from Lean's defining
  equations. A Python operator may be used only where it *is* that function.
* **Coverage** — full tables for the algebras an impl of this method can reach
  (`Nat` saturating, `Int` Euclidean and total, fixed-width modular, `Float` IEEE
  and non-raising), plus the explicit obligation that an operation with no row is
  not licensed to reuse its Python spelling: R1 already fixes it, and the row is
  added by transcribing Lean's equations. That obligation is what makes §C a claim
  about every impl rather than about the impls already attacked.

**Measured: under the corrected realization all three counterparts resolve.** Each
patch is the attack's own patch with only the arithmetic realization substituted
per §2.1 — `int_ediv(len(page_range), 0)` for `atk_1`, `int_emod(1, -2)` for
`atk_2` and `atk_4` — run through the Docker correctness oracle
(`swebench_unified.harness.run_resolve`, one attempt each, this bundle's frozen
instance record):

| patch | `resolved` | `completed` | FAIL_TO_PASS | PASS_TO_PASS |
|---|---|---|---|---|
| gold (control) | **true** | true | 1/1 | 20/20 |
| `atk_1` realized per §2.1 | **true** | true | 1/1 | 20/20 |
| `atk_2` realized per §2.1 | **true** | true | 1/1 | 20/20 |
| `atk_4` realized per §2.1 | **true** | true | 1/1 | 20/20 |

As in §B'', the verified modules were right and their submitted patches were
mistranslations. Correcting the map — not the spec — is what closes the class.

**Where the teeth are.** As before, executable on both sides and shipped as cases:

* `conformance_check.py` now defines the whole realization library —
  `int_ediv`/`int_emod`/`int_tdiv`/`int_tmod`/`int_fdiv`/`int_fmod`/`int_to_nat`,
  `uint_wrap`/`uint_div`/`uint_mod`, `float_div`/`float_to_uint64` — and measures
  it in three new blocks. `check_int_algebra` checks the Euclidean identity and
  `0 ≤ a % b < |b|` exhaustively on `[-48,48)²`, the four convention fixtures
  (`1 % -2 = 1`, `7 / -2 = -3`, `-7 / -2 = 4`, `-7 % -2 = 1`) against Python's
  differing answers, and totality at every zero divisor; `check_uint_algebra` and
  `check_float_algebra` check the measured Lean values for the modular and IEEE
  legs. Every block asserts NON-VACUITY: that the realization differs from
  Python's operator exactly where Lean does, and that Python's operator still
  raises. Run by G-CONF, in-container, every re-gate.
* `admiss-int-semantics-carried` (G-PBT) discharges the same six `Int` equations
  IN-REGION, with the frozen impl and the frozen proof body byte-for-byte. Live
  against five negative controls, each claiming Python's answer instead
  (`(1 : Int) % (-2) = -1`, `(7 : Int) / (-2) = -4`, `(-7 : Int) / (-2) = 3`,
  `(-7 : Int) % (-2) = -1`, and `∀ a : Int, a % 0 = 0`); each leaves the false
  claim as the residual goal.
* `pos-control-dead-int-arith`, `pos-control-emod-convention` and
  `pos-control-emod-guarded-branch` (G-PBT) are the three attack shapes
  themselves, as POSITIVES — they verify, and they must, so the battery records
  that the failure of the submitted counterparts is attributable to the
  translation and not to the spec. The third one carries the guard, so the
  control-flow route is in the battery too.
* `pos-control-fixed-width-wraparound` (G-PBT) is the shape NOT submitted: the
  same trick in `UInt8` (`((200 : UInt8) + 100).toNat - 43`, which is `1` in Lean
  and `257` under Python's unbounded `+`). It verifies. It is shipped so the next
  type over is already covered by a case rather than by a promise.
* `emod-convention-drop-last-two` (G-PBT) is a reject rival that routes its bug
  THROUGH `Int.emod`: it drops `((5 : Int) % (-3)).toNat = 2` trailing sub-views,
  a bound no `Nat` operation computes. So the `Int` algebra is exercised in the
  reject lane too, with a machine-checked refutation witness at `[⟨2,_⟩, ⟨3,_⟩]`.

**What is not closed, stated plainly.**

1. The cost caveat of §B'' stands, narrowed twice since: the realization fixes what
   each operation MEANS, not what it COSTS, and a counterpart that computes the right
   value by a worse algorithm would still be recorded `completed=false`. The same
   latitude exists for the gold patch. (Two things once filed here have been moved
   out. Its WORKED EXAMPLE was withdrawn — the huge-`List.range` shape §B'' named is
   a definedness failure, closed by §B''''s R2. And the "astronomically slower"
   reading was split — a loop that runs `2^64` times is not a slow function but no
   function at all, closed by §B'''''s R3. What is left is genuine cost.)
2. The `Float` leg of §2.1 is **measured unreachable**, and is tabled anyway. No
   impl of this method can offset its counter through a `Float` round trip and
   still verify: the frozen invariant `i ≤ pageRange.length` cannot be discharged,
   because Lean's `Float` operations are `@[extern]` and do not reduce (the probe
   fails with the invariant unsolved, not with a wrong value). So that row group
   has no positive control and cannot have one. It is fixed regardless, because a
   leg that is unreachable today is not the same thing as a leg the map may
   translate by spelling — and R0 covers the closed `Float` terms in any case.
3. R0 and R1 are obligations on a HUMAN translator, discharged mechanically only
   where a case or a check exercises them. The four algebra tables are pinned by
   `check_*_algebra` and by the two `admiss-*-semantics-carried` cases; a type
   reached by some future impl that no row and no check covers would rest on R1
   alone until its row is transcribed. That is why the coverage obligation is
   written into the map as an obligation rather than left implicit in a table.

## B''''. Realization does not distribute over composition

**The recorded defect** (G-EQ / G-PANEL-1, 2026-08-16 — the FOURTH finding against
this cell). §B''' generalized the arithmetic class from a table into two rules and
claimed the coverage obligation made §C "a claim about every impl rather than about
the impls already attacked". The fourth finding reopened the class **without
leaving the types already tabled**, and that is the whole point of it: it did not
need a fifth algebra, it needed two rows the map already carried, chained.

`List.range n` and `List.replicate n a` are total for every `n : Nat`, and
`List.length : List α → Nat` is total and **unbounded**. CPython bounds every
container *and* every `len` by `ssize_t`. Measured on this host
(`sys.maxsize == 2**63 - 1`):

| expression | result |
|---|---|
| `len(range(2**62))` | `4611686018427387904` |
| `len(range(2**63))` | `OverflowError: Python int too large to convert to C ssize_t` |
| `len(range(2**64))` | `OverflowError` (same) |
| `len(list(range(2**66)))` | `OverflowError` (same) |

So `(List.range n).length` answers `n` on all of `Nat`, while
`len(list(range(n)))` answers `n` on `[0, 2**63)` and RAISES above it. Four
distinct implementations exploit that, all four exit 0 (`scripts/lean_verify.sh`,
900 s cap), all four same-spec:

* **`atk_range_mul0`** — prologue
  `let _z : Nat := 0 * (List.range (2 ^ (64 + pageRange.length))).length`, counter
  `pageRange.length + _z`. In Lean `0 * k = 0` for every `k` (`Nat.zero_mul`), so
  `_z = 0` and the traversal is byte-for-byte the frozen one: it verifies, and
  correctly. Harness: `resolved=false, completed=true`, FAIL_TO_PASS 0/1
  (`test_paginator_iteration`), PASS_TO_PASS 20/20 passing.
* **`atk_range_mul0b`** — the same with the factors swapped (`… .length * 0`,
  `Nat.mul_zero`). Same outcome: F2P 0/1, P2P 20/20, `completed=true`.
* **`atk_repl_mul0`** — the same through a DIFFERENT constructor,
  `(List.replicate (2 ^ (64 + pageRange.length)) (0 : Int)).length * 0`. So it is
  not one library function's problem. F2P 0/1, P2P 20/20, `completed=true`.
* **`atk_range_ctrl`** — the value consumed by CONTROL FLOW rather than discarded:
  `if (List.range N).length * 0 > 0 then result := result else <prepend>`. The Lean
  guard is false, so the prepend always happens and the impl is the frozen one;
  the counterpart never even evaluated the guard, because the `len(list(…))` inside
  it raised first. F2P 0/1, P2P 20/20, `completed=true`.

Controls in the same batch: `ctl_frozen` (the reviewer's own faithful §2.1
realization of the FROZEN impl — same `_nat_sub` prelude, same `Option`-shaped
read, same backward fold) `resolved=true`, and a re-encode of §B'''s `atk_2`
(`Int.emod`) `resolved=true`, reproducing §B'''s own measurement. Each attack patch
is a minimal delta from `ctl_frozen` (one prologue line plus `+ _z` on the bound;
or exactly the one guarded assignment). So the four failures are attributable to
the unbounded constructors and not to the counterpart's Python.

**This is DEFINEDNESS, and §B'' had it filed as COST.** §B''s "what is not closed"
paragraph named its worked example of the cost dimension as *a `Nat` computed by
materializing a huge `List.range`*, and item 1 of §B'''s residuals carried it
forward. That was a misclassification, and the finding is what exposed it:
`len(list(range(2 ** 64)))` does not run slowly, it raises in ~1e-5 s (measured).
The shape §B'' declared out of scope was inside the class §B''/§B''' claim to
close, and it is now closed here. The cost caveat itself survives — it is just
carried without a worked example, and both places are corrected in place rather
than quietly rewritten.

**Why this is a map defect and not a missing clause — and both earlier statements
of that argument are now refuted by this bundle's own battery.**

* §B'' argued that no clause can constrain a local whose value is DISCARDED.
  `atk_4` refuted that in §B''' (its value decides a branch), and it is shipped as
  `pos-control-emod-guarded-branch`.
* §B''' argued CLOSEDNESS: a closed term denotes the same value in every module, so
  no addable clause distinguishes a module containing one. That is refuted HERE, by
  measurement rather than by argument: the closed variant
  `let _z : Nat := 0 * (List.range (2 ^ 70)).length` does **not** verify. It TIMES
  OUT at 900 s (rc=124), because the elaborator tries to evaluate the range. The
  shapes that do verify are precisely the OPEN ones (the exponent mentions
  `pageRange.length`), so closedness is not what licenses this family and cannot be
  what excuses it.

The argument that survives all four findings is neither, and it is no longer a
paragraph: it is a machine-checked battery case, `admiss-postcondition-single-valued`
(G-PBT, frozen impl and frozen proof body byte-for-byte, the claim added as an
IN-REGION `assert` — a same-spec variant may not declare new theorems, so the
obligation is discharged inside the context the method is verified in). This spec's
only obligation is `out = pageSeq pageRange`. That clause DETERMINES `out` from the
input, so

    assert (with_name_prefix `sv
      ((∀ pr : List PageIdx, ∃ o : List (List Int),
          o = pageSeq pr ∧ ∀ o' : List (List Int), o' = pageSeq pr → o' = o) ∧
       (∀ (pr : List PageIdx) (o1 o2 : List (List Int)),
          o1 = pageSeq pr → o2 = pageSeq pr → o1 = o2)))

is discharged — exit 0, measured. (The `∃!` notation is spelled out because this
bundle's tactic is measured NOT to discharge it while the unfolded form is; the
content is identical.) Therefore any two verifying implementations agree at every
input: the frozen impl and all nine arithmetic/container positive controls compute
the SAME FUNCTION. A postcondition is a predicate over the inputs and the output;
this one already pins the output uniquely; so the obligation is **maximally strong
on its observable interface**, and no strengthening of the spec region can reject
any of these shapes without also rejecting gold. Live against four negative
controls, one build each, each leaving the false claim as its residual goal:
existence denied (`∀ pr o, o ≠ pageSeq pr`), agreement denied (`… → o1 ≠ o2`),
agreement stated without its hypotheses (`∀ pr o1 o2, o1 = o2`), and uniqueness
overstated (`∀ o', o' = o`). That holds whatever the prologue looks like, wherever
its value flows, and whether it is closed or open — which is why it is the argument
this bundle now rests on, and why every residual `verify ⇒ resolved` gap here is a
refinement-map gap **by construction** rather than by preference.

**What was corrected: rule R2, and again it is not a row.** Adding a
`List.range`/`List.replicate` row would have left the same defect available in the
next constructor (`Array.mkArray`, `String.mk`, a nested `++`, `List.iota`, …). The
defect is not in any row; it is in the assumption that realization DISTRIBUTES OVER
COMPOSITION. The reviewer's counterpart was assembled entirely out of rows §2.1
already carried — `xs.length → len(xs)`, `Nat` `*` → `*`, `Nat` `+` → `+`,
`Nat` `^` → `**` — with `List.range` transcribed from Lean's defining equation
exactly as R1 instructs. Every row was faithful and the composite was not, because
the INTERMEDIATE (`list(range(n))`, a materialized 2^64-element list) leaves what
Python can represent even though the endpoints do not. mapping.md §2.1 therefore
gained:

* **R2** — a composite is realized from ITS OWN defining equation, not by chaining
  the rows of its parts, whenever an intermediate would leave what Python can
  represent. Its one-line form in this bundle: **realize the length, not the list.**
  Lean supplies the equations, each `simp`-discharged (measured): `List.length_range`
  (`(List.range n).length = n`), `List.length_replicate`, and the derived lengths of
  `map` (`= xs.length`), `take` (`= min k xs.length`), `drop` (`= xs.length - k`,
  saturating) and `++` (`= xs.length + ys.length`).

R1 was also sharpened in place to say that extensionality demands the same
FUNCTION, not the same evaluation STRATEGY, and to state the `ssize_t` bound
explicitly; and the `List` row group went from 3 rows to 7, with `xs.length →
len(xs)` now carrying the side condition *where `xs` is a materialized list*, plus
lazy rows (`range(n)`, `itertools.repeat(a, n)`) for the cases where a container
really is wanted.

**Measured: under the corrected realization all three distinct counterparts
resolve.** Each patch is the attack's own patch with only the length realization
substituted per R2 — `_z = 0 * (2 ** (64 + _n))` for `atk_range_mul0`,
`_z = (2 ** (64 + _n)) * 0` for `atk_repl_mul0`, and the guard
`(2 ** (64 + _n)) * 0 > 0` for `atk_range_ctrl`, where `_n = len(self.page_range)`
— run through the Docker correctness oracle
(`swebench_unified.harness.run_resolve`, this bundle's frozen instance record):

| patch | `resolved` | `completed` | FAIL_TO_PASS | PASS_TO_PASS |
|---|---|---|---|---|
| gold (control) | **true** | true | 1/1 | 20/20 |
| `atk_range_mul0` realized per R2 | **true** | true | 1/1 | 20/20 |
| `atk_repl_mul0` realized per R2 | **true** | true | 1/1 | 20/20 |
| `atk_range_ctrl` realized per R2 | **true** | true | 1/1 | 20/20 |

(`atk_range_mul0b` is `atk_range_mul0` with the factors swapped and realizes to the
same Python, so it is covered by the first row rather than measured twice.)

As in §B'' and §B''', the verified modules were right and their submitted patches
were mistranslations. Correcting the map — not the spec — is what closes the class.

**Where the teeth are.** Executable on both sides and shipped as cases:

* `conformance_check.py` gains the derived-length library
  (`range_length`, `replicate_length`, `map_length`, `take_length`, `drop_length`,
  `append_length`) and `check_container_realization`, which measures (a) that each
  one AGREES with materialization wherever materialization is possible
  (`n ∈ {0,1,2,7,64,513}`, plus `drop_length(999, xs) == 0` where `len(xs) - 999`
  is `-962`), and (b) that each one stays TOTAL at `n = 2**63`, `2**64`, `2**66`
  while BOTH materializing routes (`len(range(n))`, `len(list(range(n)))`) are
  measured to raise `OverflowError` — the block FAILS if a future CPython stops
  raising, so the non-vacuity is checked rather than assumed. It also asserts
  `sys.maxsize == 2**63 - 1`. Run by G-CONF, in-container, every re-gate, and it
  prints the bound it measured.
* `admiss-derived-length-carried` (G-PBT) discharges the five length equations
  IN-REGION, with the frozen impl and the frozen proof body byte-for-byte — the
  Lean half of exactly what `check_container_realization` measures on the Python
  half. Live against three negative controls (e.g. `(List.range n).length = n + 1`),
  each leaving the false claim as the residual goal.
* `pos-control-dead-range-materialization`, `pos-control-replicate-materialization`
  and `pos-control-range-guarded-branch` (G-PBT) are three of the four attack shapes
  themselves, as POSITIVES — they verify, and they must, so the battery itself
  records that the failure of the submitted counterparts is attributable to the
  translation and not to the spec. The third carries the guard, so the control-flow
  route is in the battery for this round too.
* `derived-length-drop-last-three` (G-PBT) is a reject rival that routes its bug
  THROUGH a derived length: its bound drops
  `(List.replicate 3 (0 : Int)).length = 3` trailing sub-views, a width no `Nat` or
  `Int` operation in this battery computes. It is refuted at a NEW point, the
  three-index run `[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩]` — at every two-index run it and
  `emod-convention-drop-last-two` both return `[]`, so no shorter point separates
  them, and `partial-domain-drop-first`'s three-index run starts at index 1. So the
  derived-length algebra is exercised in the reject lane, at a point shared with no
  other rival.
* `admiss-postcondition-single-valued` (G-PBT) is the class-level statement above,
  as an in-region obligation. It is what makes a fifth round answerable by a proof
  instead of by a fifth table.

**What is not closed, stated plainly.**

1. The cost caveat of §B'' stands, now without its (withdrawn) worked example: the
   realization fixes what each operation MEANS, not what it COSTS. The same
   latitude exists for the gold patch. (§B''''' narrows this once more: the part of
   "astronomically slower" that is really a non-terminating schedule is closed by R3.)
2. The `Float` leg of §2.1 is still **measured unreachable** and tabled anyway
   (§B''' item 2, unchanged): no impl can offset its counter through a `Float`
   round trip and still discharge `i ≤ pageRange.length`, because Lean's `Float`
   operations are `@[extern]` and do not reduce. No positive control exists for it
   and none can.
3. R0, R1 and R2 remain obligations on a HUMAN translator, discharged mechanically
   only where a case or a check exercises them. What R2 changes is the SHAPE of the
   residual: it is no longer "which types are tabled" (a list that a fifth finding
   can extend) but "does any composite realize through an intermediate Python
   cannot represent" (a side condition stated once, over all composites). Six
   `check_*` blocks and five `admiss-*-carried`/`single-valued` cases pin what is
   currently reachable; a composite reached by some future impl that no equation and
   no check covers would rest on R2 alone until its defining equation is
   transcribed.
4. The verifier's own limits are not a spec property, and one shows up here: the
   CLOSED variant of this family does not verify because it TIMES OUT, not because
   any obligation rejects it. A future Lean with a faster `List.range` elaborator
   might admit it. That changes nothing about `verify ⇒ resolved` — the shape is
   correct and its R2 realization resolves — but it is why the argument above is
   single-valuedness and not closedness.

## B'''''. A STATEMENT is realized by its denotation, not by its schedule

**The recorded defect** (G-EQ / G-PANEL-1, 2026-08-16 — the FIFTH finding against
this cell): *BROKEN (verify⇒correct): `atk_7.lean` verifies but its patch does not
resolve.* §B'''' had answered the fourth round by moving the class from a table of
types to a rule about COMPOSITION, and rested the whole section on single-valuedness.
The fifth finding stayed inside the tabled types **and** inside R2's premises, and
went one level up the syntax: not an expression at all, but a LOOP — a statement
whose post-state Lean proves outright and whose schedule no counterpart can run.

Five shapes, all exit 0 under `scripts/lean_verify.sh` (900 s cap), all same-spec
(spec region byte-for-byte, only the impl region and the tactic body differ), each
reconstructed here byte-for-byte from the frozen anchors before being reasoned about
(`built_atk_*`, rc=0, ~5 s each):

* **`atk_1_cost_countdown`** — prologue `let mut k : Nat := 2 ^ (64 + pageRange.length)`
  followed by `while k > 0 invariant True done_with k = 0 decreasing k do k := k - 1`,
  then the frozen traversal unchanged. Every value here is a 20-byte integer and
  every operation is tabled; what is astronomical is the ITERATION COUNT.
* **`atk_2_defined_countdown`** — the same with `k := 2 ^ (2 ^ (64 + pageRange.length))`.
  Now the initialiser is also unrepresentable, so this one is definedness AND schedule.
* **`atk_3_ctrlflow_cost`** — the countdown's exit value decides the traversal's body:
  `if k > 0 then result := result else <prepend>`. `done_with k = 0` makes the guard
  the constant `False`, so the prepend always runs. (The control-flow route, again:
  §B''' and §B'''' each needed it, because "the value is discarded" is not the excuse.)
* **`atk_7_single_loop_cost`** — the recorded one, and the sharpest: NO second loop.
  One loop, counter initialised to `pageRange.length + 2 ^ (64 + pageRange.length)`,
  carrying only `invariant result = pageSeq (pageRange.drop i)`. The `2^64+` iterations
  above the list length are discharged inside the proof by the carrier itself —
  `pageRange[i - 1]? = none` (`List.getElem?_eq_none`) and
  `pageRange.drop i = []` (`List.drop_eq_nil_of_le`) — so they PROVABLY do nothing.
  There is no prologue to point at: the widening is on the traversal's own counter.
* **`atk_9_guard_defined`** — the body guard is `2 ^ (2 ^ (64 + pageRange.length)) > 0`,
  discharged by `Nat.two_pow_pos`: a proposition whose truth never needs the value.

Submitted as patches by transliterating the schedule, all five behave the same way,
and the controls in the same batch separate the finding from the harness:

| patch | `resolved` | `completed` | wall | note |
|---|---|---|---|---|
| `gold` (control) | **true** | true | 90.9 s | resolved |
| `ctl_frozen` (the faithful §2.1 realization of the FROZEN impl) | **true** | true | 118.2 s | resolved |
| `atk_1_cost_countdown` transliterated | false | **false** | 3 723.6 s | no report — `EvaluationError` |
| `atk_2_defined_countdown` transliterated | false | **false** | 3 729.2 s | no report — `EvaluationError` |
| `atk_3_ctrlflow_cost` transliterated | false | **false** | 3 794.9 s | no report — `EvaluationError` |
| `atk_7_single_loop_cost` transliterated | false | **false** | 3 708.4 s | no report — `EvaluationError` |
| `atk_9_guard_defined` transliterated | false | **false** | 3 710.8 s | no report — `EvaluationError` |

**Why this is neither the cost caveat nor R2.** `completed=false` is exactly what
§B''s cost paragraph predicted, so the first reading is "that caveat, once more" —
and that reading is wrong, in the same way §B''s worked example was wrong. Two of the
five (`atk_2`, `atk_9`) are DEFINEDNESS: CPython cannot build
`2 ** (2 ** (64 + n))` at all (`2 ** (2 ** 64)` → `MemoryError` after ~15 s under a
2 GiB cap; `2 ** 2**31` spends 13 s building a 256 MiB integer — measured), which is
§B''''s class, one row deeper. The other three are neither: every value in them is an
integer Python holds comfortably and every operation is tabled with a faithful row.
What cannot be translated is the SCHEDULE — `2 ^ (64 + n)` iterations of a `while`.
And a `while` that runs `2^64` times is not a slow total function; R1 already demands
"a TOTAL Python function extensionally equal to the Lean one", and a program that does
not return is not one. So the naive transliteration was never a realization, and the
measurement above is its refutation rather than a bound on running time.

**And the map had a real defect this family exposed.** mapping.md §2.1's `Nat` row
read `a ^ b → a ** b`, unconditionally. It cannot be unconditional: CPython BUILDS the
integer, so above what memory holds the "realization" raises instead of answering —
precisely the flaw R2 had already been forced to fix for `xs.length → len(xs)`. The
row is therefore now side-conditioned (*where the value is one Python can hold*),
with R2 applying above the bound, and the propositional case is called out because it
is the one the attacks use: `0 < 2 ^ m` is the constant `True` that `Nat.two_pow_pos`
proves, and its realization is that constant, never `2 ** m > 0`. Measured at the
bound: `2 ** (2 ^ 64)` needs 2 305 843 009 213 693 953 bytes by arithmetic (`2^64 + 1`
significant bits) and is measured to raise `MemoryError` in a memory-capped child.

**And once that row was wrong, three more of the same kind were.** The defect is
not "the `Nat` exponent row"; it is any row whose Python spelling RAISES where the
Lean operation ANSWERS, which is R1's totality criterion and nothing new. So the
remaining rows were swept for it rather than left for a sixth finding to bring
back, and three failed. Measured in a child capped at 2 GiB:

| Lean, total | the row's old spelling | measured |
|---|---|---|
| `(a : Int) ^ (n : Nat)` | `a ** n` | `(-2) ** (2 ^ 66)` → `MemoryError`, 20.8 s |
| `List.replicate n a`, traversed | `itertools.repeat(a, n)` | `itertools.repeat(7, 2 ^ 63)` → `OverflowError` (the COUNT is `ssize_t`), 0.000 s |
| `Nat.toFloat`, `Float` power | `float(n)`, `a ** b` | `float(2 ^ 1024)` → `OverflowError`; `2.0 ** 2000` → `OverflowError: Numerical result out of range` |

The repairs are the same three moves this document has already made: a side
condition where CPython must hold a value (`int_pow`, refusing above the bound so
that R2 is entered deliberately rather than by accident), a replacement where the
bound is on a COUNT rather than a value (`repeat_total` drops the count above
`2^63` and returns the unbounded `itertools.repeat(a)` — every prefix a terminating
consumer reads is identical, and supplement 2 is what makes the consumer
terminate), and a saturating helper where Lean is IEEE and Python is not
(`nat_to_float`, `float_pow`, next to the `float_div`/`float_to_uint64` this map
already carried for the same reason). `range` is deliberately NOT on the list:
`range(2 ^ 66)` and iterating it both work (measured), and only `len` of it raises,
which is §B''''s row. None of these three is reachable by a verifying impl of THIS
method that anyone has exhibited — the `Float` leg is measured unreachable
outright (§B''' item 2) — and they are fixed anyway, for the reason §B''' gave the
first time: a leg that is unreachable today is not the same thing as a leg the map
may translate by spelling.

**And the escape clause needed one worked instance.** Both `^` rows now end "above
the bound, R2 applies — realize the expression that CONSUMES the power from its own
defining equation", and a clause that is only ever cited is indistinguishable from a
clause that cannot be followed. So the map now carries the first consuming form
worked out: `(a ^ b) % m`, whose own defining equation is `Nat.pow_mod` and whose
realization is CPython's THREE-argument `pow(a, b, |m|)` — it reduces at every
squaring, so it never builds `a ^ b`. Measured: `pow(2, 2^66, 7) = 2` in under a
microsecond, where `(2 ** 2^66) % 7` must first build the intermediate the row
refuses. Both `%` conventions ride along and are checked on the whole small grid
against `int_pow` then `int_emod`: `m = 0` is `n % 0 = n`, which three-argument
`pow` rejects with `ValueError` (so that case is the two-argument form under the
original side condition), and a negative modulus is `Int.emod`, never negative,
where Python's `pow` follows its floored `%` into `(m, 0]`. This one is a
PRE-EMPTION, not a recorded finding: no exhibited attack has used it, and it is
here because R2's clause should be demonstrably followable before an attack tests
whether it is. It costs one helper and eleven lines of measurement
(`check_total_spellings`, block (d)).

It gets no battery case, and that is an argument rather than a gap. A pos-control
must be a CORRECT impl, so a LIVE modular power inside one has to be provably
harmless to the output — and every provably harmless value of this shape is
provably CONSTANT (`(2 ^ k) % 1 = 0`, `(2 ^ k) % 2 = 0` for `k > 0`), which R1's
constant clause already covers and which `pos-control-two-pow-guard` already
carries. A non-constant modular power that left the impl correct would have to be
unread, and then it is R4's dead binding, which
`pos-control-dead-pow-local` carries. So this row is in the same position as the
two `Float` rows of §B''' item 2: measured unreachable by a verifying impl of this
method, and repaired anyway, because a leg that is unreachable today is not a leg
the map may translate by spelling.

**What was added: rule R3, and again it is not a row.** A row per loop construct would
leave the next construct (a `repeat`, a nested loop, a recursive `partial def`) open.
The defect is in the assumption that a STATEMENT is realized by transcribing its
STEPS. mapping.md §2.1 therefore gained:

* **R3** — an annotated STATEMENT is realized by its DENOTATION: the post-state its
  `invariant` and `done_with` clauses determine, which is exactly what the verifier
  proved and exactly what the rest of the program can observe. Never by its schedule.
  *Side condition (determinacy):* R3 applies precisely when `I ∧ done_with`
  determines the post-state from the entry state — `done_with k = 0` does (post-state
  `k = 0`), and `invariant result = pageSeq (pageRange.drop i)` with `done_with i = 0`
  does (post-state `result = pageSeq pageRange`, whatever `i` started at). Where the
  annotation does NOT determine the post-state, R3 says nothing and the translator
  must transcribe the loop.

R3 cannot be used to launder a wrong loop into gold. The denotation is what Lean
PROVED, not what the translator wants: a loop that computes something else has a
different `I ∧ done_with`, and if that determines a post-state other than
`out = pageSeq pageRange` the module does not verify in the first place. Conversely
where it does verify, single-valuedness (§B'''', `admiss-postcondition-single-valued`)
says every verifying impl computes the same function, so "the denotation" and "gold's
function" are the same object rather than two things a translator chooses between.

**Measured: under R3 all five counterparts resolve.** Each patch is the attack's own
patch with only the annotated statement replaced by its denotation — `k = 0` for the
countdowns, the constant guard for `atk_3`/`atk_9`, and the plain traversal for
`atk_7`'s widened loop — run through the Docker correctness oracle
(`swebench_unified.harness.run_resolve`, this bundle's frozen instance record),
strictly one at a time (the harness serializes per instance):

| patch | `resolved` | `completed` | wall |
|---|---|---|---|
| `atk_1_cost_countdown` realized per R3 | **true** | true | 97.0 s |
| `atk_2_defined_countdown` realized per R2+R3 | **true** | true | 99.4 s |
| `atk_3_ctrlflow_cost` realized per R3 | **true** | true | 80.1 s |
| `atk_7_single_loop_cost` realized per R3 | **true** | true | 85.1 s |
| `atk_9_guard_defined` realized per R1 (constant) | **true** | true | 83.7 s |

As in §B'', §B''' and §B'''', the verified modules were right and their submitted
patches were mistranslations. `atk_9` needed no new rule at all: R1's "where a Lean
sub-term is provably a constant, the realization is that constant" already covers a
guard `Nat.two_pow_pos` discharges — it is listed here because it is the shape that
made the `^` row's missing side condition visible.

**Where the teeth are.** Executable on both sides and shipped as cases:

* `conformance_check.py` gains `countdown_denotation`/`countdown_schedule`,
  `guarded_collect_denotation`/`guarded_collect_schedule`, `two_pow_positive`,
  `pow_bytes_needed`/`measure_pow_refusal` and **`check_loop_realization`**, which
  measures (a) that the countdown's denotation equals what the REAL loop computes for
  every start below 1024, with the step count asserted so a vacuous loop cannot pass;
  (b) that the guarded backward collect — the Python image of `atk_7`, where the
  `i ≤ n` test stands for the `Option`-shaped read returning `none` — agrees from
  `n`, from the algebraically widened `n + 0 · 2^64`, and denotes the same list when
  started at `n + 2^64`, where 100 000 steps are measured not to reach the data at
  all; (c) that from `k = 2^64` the schedule has NOT finished after 1 000 000 steps
  (`2^64 - 10^6` still to go) while the denotation answers `0` in constant time; and
  (d) the `^` row at its side condition — agreement for `b ≤ 16`, the exabyte
  arithmetic bound, a measured refusal to build the value, and `0 < 2 ^ n` as the
  constant. It FAILS if a future CPython builds that integer, so the non-vacuity is
  checked rather than assumed. Run by G-CONF, in-container, every re-gate.
* `conformance_check.py` also gains **`check_total_spellings`**, the sweep for the three
  sibling rows: it asserts that `repeat_total(7, 2 ^ 63)` yields (and that the bare
  `itertools.repeat(7, 2 ^ 63)` it replaces raises `OverflowError`), that `int_pow`
  agrees with `**` on small arguments and REFUSES above its stated bound rather than
  allocating, and that `nat_to_float(2 ^ 1024)` and `float_pow(2.0, 2000)` saturate to
  `inf` where bare `float()`/`**` raise — with `float(2 ^ 1023) =
  8.98846567431158e+307` as the last row that must NOT saturate, so the boundary is
  pinned from both sides. Its block (d) adds the CONSUMED power that works R2's own
  escape clause: `pow_mod` against `int_pow`-then-`int_emod` on the whole small grid
  including the zero and negative moduli, then `(2 ^ 2^66) % 7 = 2` in under a second
  above the bound the two-argument form is measured to refuse. It is a seventh G-CONF
  block, measured `(63, 66, 1024, 2)`.
* **`admiss-loop-denotation-carried`** (G-PBT) discharges the Lean half IN-REGION with
  the frozen impl byte-for-byte: `∀ n : Nat, 0 < 2 ^ n` (the `atk_9` guard), the
  countdown's determinacy (`k = 0 → k' = 0 → k = k'`), and the traversal's determinacy
  (`r = pageSeq (pr.drop i) → i = 0 → r' = pageSeq (pr.drop i') → i' = 0 → r = r'`) —
  i.e. R3's side condition itself, for exactly the two annotations this family uses.
  Live against three negative controls (`∃ n, ¬ 0 < 2 ^ n`; the countdown's
  determinacy denied; the traversal's determinacy stated without its hypotheses), one
  build each. This case carries its own tactic body because `loom_solve` does not
  discharge the assert and the frozen body then misses its `i` — measured, rc=1, which
  is why the shape used is `all_goals first | exact ⟨…⟩ | (rw [pageSeq_drop_step …];
  simp_all)`, the same shape `atk_9`'s own proof needed.
* `pos-control-cost-countdown`, `pos-control-cost-countdown-huge`,
  `pos-control-cost-guarded-body`, `pos-control-widened-counter` and
  `pos-control-two-pow-guard` (G-PBT) are the five attack shapes THEMSELVES as
  positives, each byte-identical to a probe verified here. They verify, and they must:
  the battery records that the submitted counterparts failed by translation and not by
  the spec.
* `pow-bound-drop-last-four` (G-PBT) is a reject rival that routes its bug through the
  `^` row: its bound drops `2 ^ 2 = 4` trailing sub-views, a width no other operation
  in this battery computes. It is refuted at a NEW point, the four-index run
  `[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩, ⟨5,_⟩]` under `hn : 5 ≤ numPages` — every shorter run makes it
  and `derived-length-drop-last-three` both return `[]`. So the exponent row is
  exercised in the reject lane, at a point shared with no other rival.
* Three existing reject witnesses (`order-reversed`, `partial-domain-shifted-index`,
  `value-indexed-by-position`) had their tails wrapped in `try (…)` so that the
  GOLD-side residual is `⊢ False` (signature tier `reduced`) instead of a binder
  complaint (tier `shape`). The refutation is unchanged — the rival side still exits 0
  and the forgery still inverts — and it is recorded here because it is a change to
  frozen-looking text with a reason: a `shape`-tier gold signature is indistinguishable
  from a witness that never engaged the claim.

**What is not closed, stated plainly.**

1. Genuine COST remains open, and is now the only thing left of §B''s caveat: a
   realization may compute the right value by a worse algorithm. The same latitude
   exists for the gold patch. What is closed is everything that was really definedness
   (R2) or really a schedule (R3).
2. R3 rests on its side condition, and the side condition is a property of the
   ANNOTATION, not of the loop: an impl whose `I ∧ done_with` leaves the post-state
   underdetermined is not covered, and its translator must transcribe the loop. This
   is mechanically pinned only for the two annotation shapes
   `admiss-loop-denotation-carried` discharges.
3. A verifier limit showed up here too, and it is not a spec property (compare §B''''
   item 4): `atk_8_single_loop_defined`, a sixth shape in this family, is REJECTED with
   rc=134 `Stack overflow detected. Aborting.` — the elaborator refusing, not an
   obligation rejecting. Likewise the CLOSED variant of §B''''s family still times out
   at 900 s. Neither changes `verify ⇒ resolved`; both are why this document's
   class-level argument is single-valuedness rather than any statement about what the
   verifier happens to accept.

## B''''''. A BINDING is realized by its denotation too

The sixth gap of the same class, exhibited by the round-6 G-EQ pass (2026-08-16,
its `atk_pow_dead`). Where the previous five were RECORDED findings, this one has
to be sourced precisely, because the round-6 record does not contain it: that
role was killed at its 14400s cap and its recorded detail is
`eq: INCONCLUSIVE — the audit role did not run (RuntimeError: agent CLI timed out
after 14400s (killed)); only 0 admissible attacks of 0 submitted`, which is an
infrastructure artifact and says nothing about this spec. The attack itself was
measured, in the role's own scratch and in the process table: its `results.txt`
recorded `exit=0` for `atk_pow_dead`, its materialized patch carried
`_z = 2 ** (2 ** (64 + len(page_range)))` (read out of the running container's
`/tmp/patch.diff`), and that resolve was still burning 99% CPU 56 minutes in when
the role's budget ran out. The cap and the hole are the same event: `run_resolve`
defaults to `timeout=3600, retries=2`, so ONE patch CPython cannot execute costs
3 × (3600 + 600) = 12 600s of a 14 400s role. Closing the hole is therefore also
what stops manufacturing the INCONCLUSIVE.

It is one line, and it is the shape R3 leaves standing, because a `let` is not an
annotated statement:

```
let _z : Nat := 2 ^ (2 ^ (64 + pageRange.length))
```

Everything else in the module is the frozen impl, byte for byte. It VERIFIES
(measured: `exit=0`), and it must — `_z` is never read, so no predicate over
`pageRange` and `out` can see it, which is the same argument
`pos-control-dead-nat-arith` has carried since §B''. What the attack materialized
was `_z = 2 ** (2 ** (64 + len(page_range)))` inside `__iter__`, and that is not a
slow program: CPython is measured to refuse the integer outright (2 305 843 009
213 693 953 bytes by arithmetic at the smallest input, `MemoryError` in a
memory-capped child), so every iteration of a `Paginator` raises and the patch
does not resolve.

**Why the previous five rules do not cover it.** R0 needs a closed term (this one
mentions `pageRange`). R1 asks for a total Python function equal to the Lean
operation, and `**` is not one at this magnitude — which is exactly why §B'''''
side-conditioned the `^` row to values Python can hold. R2 realizes a composite
from its own defining equation, and there is no composite here: nothing CONSUMES
the power, so there is no equation to realize. R3 is about annotated statements,
and a `let` carries no invariant. So the map, read strictly, offered only
transcription — and the auditor read it strictly and correctly. Its own words, in
the attack file: *"the map leaves exactly one route: transcribe
`2 ** (2 ** (64 + n))`, which CPython cannot build."* The one sentence §2.1 did
have about dead locals ("a realized DEAD local computes the same value … so
neither a discarded local nor a consumed guard can diverge") was an argument that
realizing one is harmless, not a rule about what its realization IS, and read as a
rule it says the opposite of what is needed.

**The rule, R4.** A binding is a statement, so R3's principle applies to it: it is
realized by its denotation. Every Velvet expression is pure and every Lean
function is total, so a `let` whose variable nothing READS cannot change the
returned value and cannot fail; its denotation is the identity on the state, and
its realization is the empty statement. The value need not be built.

**Its side condition, and why the rule is not a licence to delete work.** "Nothing
reads it" is syntactic, so it is DECIDED and not claimed: `impl_reads_binding` in
conformance_check.py counts reads of the binder in the impl region, skipping
comments, the binding's own line, and annotation lines — an `invariant` mentioning
the local is a proof obligation, and by R3 the realized patch contains no proof
obligations, so a local read only there is still runtime-dead. Three fixtures pin
all three answers, measured: the attack's own impl → 0; the same impl with
`return result.take z` → 1; the impl whose local appears only in
`invariant i ≤ z` → 0, while a naive whole-text count finds the mention, so the
annotation stripping is load-bearing. Where the count is not zero R4 gives
nothing and R0–R2 realize the bound term; for the live fixture that difference is
measured as a genuinely different output list. Note also what R4 does NOT need:
the frozen postcondition is single-valued (`admiss-postcondition-single-valued`),
so an impl carrying a dead binding computes gold's function, and dropping the
binding cannot change which function is realized — only whether the realization
returns at all.

**Where the teeth are.** Executable, in the block G-CONF runs every re-gate:

* `conformance_check.py` gains `impl_reads_binding`, `dead_local_denotation`,
  `dead_local_schedule`, `live_local_denotation` and
  **`check_dead_binding_realization`**, which measures (a) the deadness decision on
  the three fixtures above; (b) agreement between the transliteration and the
  denotation at an exponent CPython can hold, with the useless integer's bit
  length asserted so the schedule is known to have really run; (c) the refusal at
  the attack's own exponent against a denotation that answers in microseconds; and
  (d) non-vacuity — dropping the LIVE binding changes the value. Measured:
  `(1, 2305843009213693953, 'MemoryError', 4e-06)`. It is the eighth `check_*`
  block, and like the others it FAILS if a future CPython builds the integer.
* the battery ships BOTH halves of the decision R4 turns on.
  **`pos-control-dead-pow-local`** is the attack's impl region as a positive — the
  frozen impl plus that one `let`, code for code, its comment block aside: it must
  verify, so the record shows the SPEC accepts it and the failure can only have
  been the translation. **`live-local-drop-last`** is a REJECT rival
  that carries a wrong bound in a LIVE local (`let z := pageRange.length - 5`, read
  at the return): it is refuted — and the same module with that local DROPPED is
  `pos-control-closed-form`, which verifies. That pair is the side condition itself,
  in Lean: applying R4 to a live binding would turn a rejected impl into gold, which
  is why deadness is decided and not assumed. All four builds measured, one at a
  time: the positive VERIFIES (rc=0, 7s); the rival is REJECTED (rc=1, 5s); its
  witness HOLDS of the rival (rc=0, 5s), so the rejection is attributable to the
  spec and not to a tactic gap; and the same witness FAILS against the reference
  impl (rc=1, 8s) with residual `hn : 6 ≤ numPages ⊢ False` — signature tier
  `reduced`, i.e. the kernel evaluated the claim rather than getting stuck. Its
  refutation point is the five-index run, which no other rival separates: at four
  indices this rival and `pow-bound-drop-last-four` both return `[]`.
* and the OFFICIAL ORACLE, on the attack's own patch. The claim R4 makes is not
  that the attack is harmless but that its faithful realization RESOLVES, so that
  claim was run: the round-6 attack module transliterated per this map with the
  dead `let` dropped — one line different from what the role submitted, everything
  else including the `_nat_sub`-realized traversal identical — is
  `resolved=true, completed=true, applied=true, F2P 1/1, P2P 20/20` in **53.1
  seconds** through `harness.run_resolve` (2026-08-16). The role's own version of
  the same module never completed a single resolve in 4 200s. That pair is the
  repair, measured end to end: same spec, same verifying impl, same harness, and
  the only variable is whether the map says what to do with a binding nothing
  reads.

**What is not closed, stated plainly.**

1. R4's side condition is decided on the IMPL TEXT. A translator that lies about
   the text is outside every rule in this document, as it always was; what changed
   is that the honest translator now has a procedure and a reviewer now has a
   counter to run.
2. Genuine COST is still open, unchanged from §B''''' item 1 — and R4 narrows it
   from the other side: a computation nothing observes is not cost, it is a no-op.
3. The dead binding here is pure `Nat` arithmetic. A dead binding whose term is
   itself a statement (a nested loop, say) is covered by R3 first and then R4, and
   that composition is argued rather than measured: no attack has exhibited one.

## C. verify(Solution) ⇒ resolved

`enumeratePages` verifies only if its output equals `pageSeq pageRange` — the
ordered, length-preserving per-index expansion of the index sequence through the
SAME accessor `pageOf` (A3/A4). By R (`page_range ↔ List PageIdx`, `Page ↔
list(page)`) the verified iterator equals `[self.page(n) for n in
self.page_range]` materialized in order — exactly what the gold generator yields;
by G-AX the opaque `pageOf` equals the real `Paginator.page` (A-reference:
deterministic, order-independent, and defined on exactly `[1 … num_pages]`); by
G-CONF the R/I transliteration of the fold — including the `Option`-shaped read,
the carrier membership, and the arithmetic realization of mapping.md §2.1 —
agrees with `patch.diff`'s `list(iter(paginator))` on the fuzzed configurations.

Seven things the value clause alone does **not** give, supplied here:

1. **No hidden failure mode.** A verified impl performs no accessor application
   the real object would refuse, because it cannot express one (§B'). This is what
   makes the modeled operation total without totalizing a partial callee, and it is
   the step the earlier revision was missing: there, "verifies" left room for a
   discarded off-domain call that raises at run time.
2. **No terminating-by-assumption impl.** The bundle sets
   `loom.semantics.termination "total"` **and** `open TotalCorrectness` (the `open`
   is what selects the semantics — both namespaces define
   `WPGen.forWithInvariantLoop` and the later `open` wins, so setting the option
   while opening `PartialCorrectness` would leave the measure decorative). Every
   loop therefore carries `measure b' < measure b`, and a diverging impl cannot
   satisfy the postcondition vacuously. Measured on this cell: the frozen impl
   verifies with its measure `i`, and the same impl with its `i := i - 1` step and
   measure removed is rejected with `Decreasing annotations are required in total
   correctness semantics`.
3. **No arithmetic that only Lean can evaluate.** Every `Nat` operation a verified
   impl performs is realized by mapping.md §2.1's total counterpart, not by the
   same-looking Python operator. So an expression the verifier accepted as
   *defined* is defined in the counterpart too (no `ZeroDivisionError`, no
   negative index), and — the sharper half — the termination the verifier PROVED
   under supplement 2 transfers, because the realized step walks the same
   descending `Nat` sequence. This is the leg the second recorded G-EQ finding
   broke, and §B'' records it: `Nat` division and truncated subtraction are total
   functions that Python's `//` and `-` do not implement, so reading one as the
   other is a change of algebra, and a measure that provably reaches `0` in Lean
   can run away forever in a counterpart that swapped the algebra underneath it.
4. **And no arithmetic in any OTHER type either.** Supplement 3 is about `Nat`,
   and a claim scoped to one type is not a claim about a verified impl — the third
   recorded G-EQ finding wrote the identical trick in `Int`, whose `/` and `%` are
   Euclidean and total where Python's are floored and partial, and it broke this
   section three ways: by definedness (`(n : Int) / 0`), by convention with nothing
   partial anywhere (`(1 : Int) % (-2) = 1`, not `-1`), and by flipping a BRANCH so
   the iterator emitted nothing. §2.1 is therefore now two rules over all types —
   a closed term realizes as the value Lean gives it (R0), an open one as a total
   function equal to the Lean operation (R1) — with tables for `Nat`, `Int`,
   fixed-width and `Float`, and an explicit obligation to transcribe a row rather
   than reuse a Python spelling for anything not yet tabled. That is what makes
   this section a claim about EVERY verified impl and not about the ones already
   attacked; §B''' records the finding, the measurement that all three counterparts
   resolve once realized correctly, and what remains open.
5. **And no COMPOSITE that only Lean can hold in memory.** Supplements 3 and 4 are
   about operations; supplement 5 is about their composition, which is not the same
   claim — the fourth recorded G-EQ finding needed no new type at all. It chained
   `List.range n → range(n)` with `xs.length → len(xs)`, two rows §2.1 already
   carried and both faithful, into `len(list(range(n)))`, which raises
   `OverflowError` for every `n ≥ 2^63` because CPython bounds every container and
   every `len` by `ssize_t` while Lean's `List.length` is unbounded. The endpoints
   were representable and the INTERMEDIATE was not. §2.1 therefore now carries R2 —
   a composite is realized from its own defining equation, never by chaining rows
   through an intermediate Python cannot represent; *realize the length, not the
   list* — with Lean's own length equations for `range`, `replicate`, `map`, `take`,
   `drop` and `++`, `check_container_realization` measuring the Python half
   (including that the materializing routes really do raise), and
   `admiss-derived-length-carried` pinning the Lean half in-region. §B'''' records
   the finding, the four verifying shapes, the measurement that all three
   distinct counterparts resolve under R2, and what remains open.
6. **And no SCHEDULE that only Lean can skip.** Supplements 3–5 are about
   expressions — what an operation means, in which type, composed how. Supplement 6
   is about STATEMENTS, and the fifth recorded G-EQ finding needed no new type, no
   new constructor and no unrepresentable value: its sharpest shape
   (`atk_7_single_loop_cost`) is the frozen traversal with its counter started at
   `pageRange.length + 2 ^ (64 + pageRange.length)`, where the extra `2^64+`
   iterations are PROVED to do nothing (`pageRange[i - 1]? = none`,
   `pageRange.drop i = []`) and the annotation `invariant result =
   pageSeq (pageRange.drop i)`, `done_with i = 0` determines the post-state anyway.
   Transliterating the loop step for step yields a program that does not return —
   measured `completed=false` after 3 708–3 795 s against 118.2 s for the frozen
   control — so R1's own "total Python function" criterion rejects it. §2.1 therefore
   now carries R3: an annotated statement is realized by its DENOTATION, the
   post-state its invariant and `done_with` determine, never by its schedule; with
   the determinacy side condition stated explicitly, `check_loop_realization`
   measuring the Python half (including that the schedule really does not finish),
   and `admiss-loop-denotation-carried` pinning the determinacy of both annotation
   shapes in-region. §B''''' records the finding, the five verifying shapes, the
   measurement that all five counterparts resolve under R3, the `^`-row defect the
   family exposed, and what remains open.

7. **And no BINDING that only Lean can afford.** Supplement 6 is about statements
   with annotations; supplement 7 is about the statement that has none. The sixth
   finding bound a local to `2 ^ (2 ^ (64 + pageRange.length))` and never read it:
   dead, unobservable, and — transliterated — an integer CPython is measured to
   refuse, so `__iter__` raised on every input. R0–R3 all decline it (closed term,
   no; total Python operation, no; consuming composite, none; annotated statement,
   no), so §2.1 gained R4: a binding is realized by its denotation too, and a
   binding nothing READS denotes the identity, so its realization is the empty
   statement. The side condition is syntactic and is therefore decided rather than
   claimed — `impl_reads_binding` counts runtime reads, annotation-only mentions
   included as non-reads because a refined patch carries no annotations — with
   `check_dead_binding_realization` measuring both directions and
   `pos-control-dead-pow-local` / `live-local-drop-last` recording the two sides of
   the decision in the battery. §B'''''' records the finding, the measurement, and
   what remains open.

**Why this list is finite.** Each of supplements 3, 4, 5, 6 and 7 closed a round of the
same class, and each time the fix was a rule rather than a table — which raises the
obvious question of whether an eighth supplement is always pending. The honest answer
has two halves. Empirically the list does keep growing, and supplements 6 and 7 are the
rounds where that stopped being a worry and became a prediction confirmed: each landed exactly
where the argument below says every future finding of this family must land — in the
REFINEMENT MAP (a `^` row missing its side condition, a missing rule about annotated
statements, and then a missing rule about the one statement that has no annotations),
with the spec region provably not at fault and, measured, byte-identical
across all six rounds (`Solution.lean` sha256 `d68e534c…`, unchanged since the first
repair). The other half is why that is forced rather than convenient, and it is now a
machine-checked case rather than a promise
(`admiss-postcondition-single-valued`, discharged in-region under the frozen proof
body): the spec's only obligation is `out = pageSeq pageRange`, which determines
`out` from the input, so exactly one `o` satisfies `o = pageSeq pr` for
every input, so **any two verifying impls agree at every input** — the frozen impl
and every arithmetic/container positive control in the battery compute the same
function. A postcondition is a predicate over the inputs and the output, and this
one already pins the output uniquely, so the obligation is maximally strong on its
observable interface: no strengthening of the spec region could reject any of those
shapes without also rejecting gold. Every future finding of this family is therefore
a defect in THIS document or in mapping.md §2/§2.1 — not a missing clause — and
that is a statement about where the repair goes, not a licence to leave one
unrepaired. §B'''' states it in full, §B''''' is the first round to have been
routed by it — the repair went to the map, and the five submitted patches then
resolved — and §B'''''' is the second, in the one place a rule about statements had
left uncovered.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: callee-reference
soundness (G-AX — now including the callee's DOMAIN, which the carrier depends on)
and refinement fidelity (this doc plus mapping.md §2/§2.1, G-EQ + G-CONF — the
second of which now executes the arithmetic realization over all four algebras, the
derived-container realization of R2, the loop-denotation realization of R3 AND the
dead-binding decision of R4, rather than assuming any of them).
