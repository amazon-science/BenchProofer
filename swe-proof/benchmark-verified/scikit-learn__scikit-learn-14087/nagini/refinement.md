# refinement.md — scikit-learn__scikit-learn-14087

The operation-by-operation correspondence between `model.py`'s implementation
(`gather_per_class`, `mixing_record`, and their pure helpers) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses the axiom's `Ensures`, **A-reference**
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). The patch has two independent hunks,
both in the `else:` (no-refit) branch of `LogisticRegressionCV.fit`. There is
one `model_prepatch_<k>` per independently-fixed behaviour, plus one
consumer-freedom attacker for site 1 (see §A).

## A. Site 1 — per-class read driven by the concrete strategy in effect

Gold hunk (`sklearn/linear_model/logistic.py`, body line 2173):
```
-                if self.multi_class == 'ovr':
+                if multi_class == 'ovr':
                     w = np.mean([coefs_paths[i, best_indices[i], :]
                                  for i in range(len(folds))], axis=0)
                 else:
                     w = np.mean([coefs_paths[:, i, best_indices[i], :]
                                  for i in range(len(folds))], axis=0)
```
Modeled by `gather_per_class`.

The headline bug is a CONTROL-FLOW effect (the read either succeeds in-bounds or
raises `IndexError: too many indices for array`); the returned coefficient value
itself is value-irrelevant to the tested observable (the F2P asserts
`coef_.shape`, not values — mapping.md §2). A value-only postcondition
(`Result() == summary_token`) is therefore echoable by `return summary_token`
without performing any read. The discriminator is pinned instead by an
UNFORGEABLE capability: `read_admissible(rank)` is an abstract `@ContractOnly`
`@Predicate` (no body — cannot be `Fold`ed or fabricated), granted ONLY by the
consumed axiom `read_across_folds`, whose `Requires(gather_arity(use_joint_layout)
== table_rank)` enforces the arity match, and granted AT the rank the read was
checked against. `gather_per_class`'s `Ensures` *requires* the token at the
table's ACTUAL rank (`table_axes`), so the guard lives entirely in the frozen
contract, not in any impl-region assertion — and a read checked against a
self-consistent rank other than the actual layout's (forging the axiom's rank
argument from the read's own arity) grants only the token at the forged rank
and cannot discharge the obligation.

The real observable is UNIVERSAL, not existential: every index expression the
block executes against the one `coefs_paths` array must be in-bounds, not merely
the one whose value becomes `w`. A token demanded at `table_axes` is satisfied as
soon as ONE honest read happens, so with the rank passed as a plain `int` the
NUMBER and the RANKS of the other reads stay free — an implementation could issue
an extra read at any self-consistent `(arity, rank)` pair, a no-op in a value
model but a real index expression against the real array. The model therefore
carries the summary table as a RESOURCE rather than as a rank the reader supplies:
`summary_table(actual_rank)` is a second abstract `@ContractOnly` `@Predicate`,
held by `gather_per_class` at `table_axes` (`Requires`/`Ensures`) and
*consumed and returned* by `read_across_folds` at the rank the read is checked
against (`Requires(summary_table(table_rank))` /
`Ensures(summary_table(table_rank))`). A read is thus only performable against
the one table the step holds, at that table's actual rank, so EVERY read — not
just the delivering one — is arity-checked against the actual layout. Handing the
resource back (rather than consuming it) is what keeps a repeated in-bounds read
legal, which is correct: a duplicated in-bounds index expression does not raise.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `resolved_strategy: int ∈ {INDEPENDENT,JOINT}` (Requires excludes UNRESOLVED) | the local `multi_class` (= `_check_multi_class(self.multi_class, solver, n_classes)`, `logistic.py:2004`) used in the post-patch branch | R | `str ∈ {'ovr','multinomial'}` ↔ `int ∈ {INDEPENDENT,JOINT}`; the resolver never returns `'auto'` (mapping.md §3.1), encoded as the Requires `resolved_strategy != UNRESOLVED`. |
| A2 | param `unresolved_form: int ∈ {INDEPENDENT,JOINT,UNRESOLVED}` | `self.multi_class` (the unresolved attribute, the pre-patch branch operand) | R | `str ∈ {'ovr','multinomial','auto'}` ↔ `int ∈ {INDEPENDENT,JOINT,UNRESOLVED}`. Present so the prepatch can exercise the wrong operand. |
| A3 | param `table_axes == table_rank(resolved_strategy)` (3 for INDEPENDENT, 4 for JOINT) | the per-class `coefs_paths` numpy array, whose number of index axes is built from the resolved `multi_class` by the reshape at `logistic.py:2086-2106` | R | the array's axis rank is the only property of `coefs_paths` the bug depends on; `table_rank` is the reshape's rank table (validated == real `np.reshape` by G-AX R1). |
| A4 | `use_joint_layout = resolved_strategy != INDEPENDENT` | `if multi_class == 'ovr': ... else: ...` | I | identical concrete branch — the boolean negation of the equality test, on the resolved operand (A1). |
| A5 | `w = read_across_folds(use_joint_layout, table_axes, summary_token)` | the act of indexing `coefs_paths[i, best_indices[i], :]` (3 axes) vs `coefs_paths[:, i, best_indices[i], :]` (4 axes) inside `np.mean([... for ... folds], axis=0)` | **A-consumed** + R | `read_across_folds` is the consumed axiom modeling the across-folds read: its `Requires(gather_arity(use_joint_layout) == table_rank)` is the read's in-bounds condition (over-arity → `IndexError: too many indices for array`, the reported failure), and its `Ensures(read_admissible(table_rank))` grants the unforgeable in-range capability AT the checked rank. Crucially its `Requires(summary_table(table_rank))` binds the call to the ONE table the caller holds: `table_rank` is not a number the reader may name but the actual rank of the held array, so the correspondence "one axiom call ↔ one real index expression against the single real `coefs_paths`" holds for EVERY call, not just the delivering one. `gather_arity` (3 for the independent read, 4 for the joint read) ↔ the literal axis count of each `[...]` expression. The axiom is the WEAKEST sufficient contract for the arity behaviour (it constrains nothing on an arity mismatch — that case simply cannot satisfy the precondition) and it returns the table (`Ensures(summary_table(table_rank))`), so repeated in-bounds reads stay expressible. G-AX (R1+R2) validates: arity-match ⟺ in-bounds; over-arity ⟹ `IndexError`. The returned `summary_token` ↔ the gathered vector `w`; its numeric value/averaging (`np.mean`/`np.argmax`/the fold comprehension) is value-irrelevant (R; G-AX-referenced). |
| A6 | `Requires/Ensures(summary_table(table_axes))` + `Ensures(read_admissible(table_axes))` on `gather_per_class`; `return w` | post-patch EVERY read in the block is in-bounds, because there is one `coefs_paths` per iteration whose rank was built by the resolved value that also drives the branch (A1≡A3) | R | the obligation is now UNIVERSAL, matching the real observable. The step is handed the one summary table at its actual rank and must hand it back at that same rank, and a read is performable only against a held table — so no read at any point in the step, delivering or not, can be checked against a rank other than the actual layout's. Combined with the capability demanded at `table_axes` this pins both halves: that a read actually happened and was in range (against an echo), and that no *other* read was performed out of range (against an extra read at a self-named rank). Post-patch both always hold: the branch operand is the value that built the layout, and the block indexes exactly one array. |

Site-1 prepatch / attacker variants (all share the spec exactly):
- `model_prepatch.py` reverts A4 to `use_joint_layout = unresolved_form != INDEPENDENT` (the pre-patch `self.multi_class`). It **fails** at A5: when `unresolved_form == UNRESOLVED` and `resolved_strategy == INDEPENDENT` (so `table_axes == 3`), the joint read is taken and `gather_arity(True) == 4 ≠ 3` — the `read_across_folds` precondition is violated, exactly the out-of-range index the issue reports (`IndexError: too many indices for array`).
- `model_prepatch_1.py` is the CONSUMER-FREEDOM attacker the verdict required: it echoes the value with `w = summary_token` and never calls `read_across_folds`. It satisfies `Result() == summary_token` but **fails** the `Ensures(read_admissible(table_axes))` postcondition ("insufficient permission to access `read_admissible(table_axes)`") — the unforgeable capability cannot be fabricated. This proves the site-1 guard is a contract clause, not a discardable impl-region `Assert`. (It keeps failing on the capability, not on the held-table resource: the resource is handed in by the precondition and this body never spends it, so the recorded `fails_on` message is unchanged.)

These are G-DIFF for site 1.

## B. Site 2 — per-class mixing value recorded as the absent marker

Gold hunk (`sklearn/linear_model/logistic.py`, body lines 2183-2184 → post):
```
-                best_indices_l1 = best_indices // len(self.Cs_)
-                self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
+                if self.penalty == 'elasticnet':
+                    best_indices_l1 = best_indices // len(self.Cs_)
+                    self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
+                else:
+                    self.l1_ratio_.append(None)
```
Modeled by `mixing_record`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `family_has_mixing: bool` | `self.penalty == 'elasticnet'` (`logistic.py:2183`, and the same condition at `logistic.py:1964`) | R | `str`-equality ↔ `bool`; identical truth value. |
| B2 | params `selected_index`, `candidates_len`, with `0 <= selected_index < candidates_len` and (no-mixing ⇒ `candidates_len == 1`), where `candidates_len` is carried by the held-table resource `candidate_table(_, candidates_len)` | `best_indices_l1 = best_indices // len(self.Cs_)` indexing `l1_ratios_` (`[None]` sentinel of length 1 when penalty≠elasticnet, `logistic.py:1972-1978`) | R | `len(l1_ratios_)` ↔ `candidates_len`; the `[None]` sentinel ↔ `not family_has_mixing` with length 1 (mapping.md §3.2). `//`, `%`, `np.argmax` are unchanged numeric primitives producing the index (R; G-AX-referenced). The in-range fact is TRUE of the real post-patch code: `best_indices = np.argmax(scores, axis=1)` ranges over `scores.shape[1] == len(self.Cs_) * len(l1_ratios_)` (the reshape at `logistic.py:2108`), so `best_indices // len(self.Cs_) < len(l1_ratios_)` — every real lookup is within the real table. Because `candidates_len` is a parameter of the held resource rather than a plain int the caller names, that bound is the real table's extent for EVERY selection, not a number the reader may inflate. |
| B3 | `if family_has_mixing: entry = select_mixing_value(...)` | `if self.penalty == 'elasticnet': self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))` | R + **A-consumed** | identical branch + take-from-table, where the take is the consumed axiom `select_mixing_value`: the averaged lookup at the chosen position of the candidate table. It is a PARTIAL operation on the table it addresses in TWO respects, and both are properties of the HELD table rather than assertions of the selector's: (i) it is admissible only against a table whose entries are real mixing values, because on the placeholder table the average is not a mixing value at all (axiom_check.py R3); (ii) it is admissible only at a position within that table's ACTUAL EXTENT, because a position past the end addresses no entry (`IndexError: index N is out of bounds for axis 0 with size N`). Both facts are carried by the resource `candidate_table(holds_mixing_values, candidates_len)`, required and returned by the axiom at the entry-reality and extent the selection is checked against, so the correspondence "one axiom call ↔ one real IN-RANGE averaged lookup of the single real `l1_ratios_`" holds for EVERY call, not just the one whose value is recorded. Its result is the selected real ratio, modeled as the identity token `mixing_value` (the F2P asserts `l1_ratio_.shape`, not the numeric value — mapping.md §2), and it grants the unforgeable `mixing_selected()` capability, which the consumer demands whenever it records a value. So the obligation is UNIVERSAL over selections: every selection the step performs is a selection of an entry the candidate table in effect actually holds and whose entries are real, which is what makes "the placeholder table is never averaged" and "no lookup reaches past the end of the ratio table" observable rather than claims about the delivered record alone. |
| B4 | `else: entry = None` | `else: self.l1_ratio_.append(None)` | I | identical: record the explicit absent marker (`None` ↔ `Optional` `None`). |
| B5 | `return entry` | the per-class element appended to `self.l1_ratio_` | R | the list append ↔ the returned per-class entry; the postcondition pins it to a value xor `None`. |

`model_prepatch_2.py` reverts B3/B4 to the unguarded pre-patch form
`entry = mixing_value` (always take from the table — i.e. always run
`np.mean(l1_ratios_[best_indices_l1])`). It **fails** the postcondition
`not family_has_mixing ⇒ Result() is None`: a family without a mixing parameter
must record the absent marker, but the pre-patch records a table-derived value.
On the real code that table is the non-numeric `[None]` sentinel, so the real
pre-patch produces a malformed `l1_ratio_` (the new F2P `l2` cases assert
`l1_ratio_.shape == (n_classes,)` with well-formed entries). This is G-DIFF for
site 2.

## C. Axiom inventory (TWO consumed axioms, four abstract predicates, two A-reference facts)

Complete inventory of what the proof consumes, so that no axiom's precondition
escapes scrutiny:

| consumed axiom | abstract predicates it uses | site |
|---|---|---|
| `read_across_folds` | `summary_table(actual_rank)` (held resource), `read_admissible(checked_rank)` (capability) | 1 |
| `select_mixing_value` | `candidate_table(holds_mixing_values, actual_len)` (held resource), `mixing_selected()` (capability) | 2 |

Both axioms have the SAME shape, and deliberately so: the facts a call is
checked against (an axis rank at site 1, an entry-reality and an extent at
site 2) are carried by an abstract, un-`Fold`able RESOURCE the step is handed
and hands back, never by plain arguments the implementation may name for
itself; and each grants an unforgeable capability the consumer's `Ensures`
demands. Any fact a partial operation is guarded by that were passed as a bare
`int`/`bool` would make the guard existential over the delivering call instead
of universal over every call.

- **A-consumed: `read_across_folds`** (with its two abstract predicates: the
  capability `read_admissible` and the held-table resource `summary_table`).
  Models the across-folds read of the per-class summary
  table — an unchanged numeric read (`np.mean([coefs_paths[...] for folds])`)
  whose only behaviour the bug depends on is its index arity. The proof
  *consumes* its `Ensures(read_admissible(table_rank))` at `table_axes`, and
  threads `summary_table(table_axes)` through the read so that the rank every
  read is checked against is the held array's rather than one the reader names.
  Both predicates are abstract (`@ContractOnly` `@Predicate`, no body), so
  neither can be `Fold`ed into existence. It is
  the weakest contract
  sufficient: it constrains only the arity-match case (the precondition);
  nothing is claimed about the mismatch case, and the resource is returned
  unchanged so repeated in-bounds reads remain expressible. Provenance + G-AX
  evidence:
  mapping.md §3.1; axiom_check.py R1 (rank table matches real `np.reshape` /
  `_check_multi_class`) + R2 (arity-match ⟺ in-bounds; over-arity ⟹ real
  `IndexError`).
- **A-consumed: `select_mixing_value`** (with its two abstract predicates: the
  capability `mixing_selected` and the held-table resource `candidate_table`).
  Models the averaged lookup at the chosen position of the per-class
  candidate-mixing table (`np.mean(l1_ratios_[best_indices_l1])`,
  `logistic.py:2184`) — an unchanged numeric operation whose only bug-relevant
  behaviours are (i) whether it is performed at all against a table that holds
  no mixing values and (ii) whether the position it addresses exists. The proof
  *consumes* its `Ensures(mixing_selected())` and threads
  `candidate_table(family_has_mixing, candidates_len)` through the selection, so
  the entry reality AND the extent every selection is checked against are the
  held table's rather than ones the selector names. Both predicates are abstract
  (`@ContractOnly` `@Predicate`, no body), so neither can be `Fold`ed into
  existence. It is the weakest contract sufficient: it constrains only the
  admissible case (real entries, in-extent position); nothing is claimed about
  the placeholder table or an out-of-range position, and the resource is returned
  unchanged so repeated legitimate lookups remain expressible — including at a
  DIFFERENT in-range position, which is a correct alternative
  (`pos-control-site2-other-in-range-position`). Provenance + G-AX evidence:
  mapping.md §3.2; axiom_check.py R3 (`np.mean` over the `[None]` sentinel is not
  a real number). The in-extent fact is grounded in B2: `best_indices //
  len(self.Cs_)` is bounded by `len(l1_ratios_)` because `scores.shape[1] ==
  len(self.Cs_) * len(l1_ratios_)`.
- **A-reference: `l1_ratios_` `[None]` sentinel** (site 2). The non-mixing
  candidate table is the one-element `[None]` set at `logistic.py:1972-1978`;
  `np.mean` over it is not a real number, so the absent marker is required.
  Modeled deeply via the precondition `not family_has_mixing ⇒ candidates_len
  == 1` and the `Optional` `None` sentinel; NOT a consumed axiom. Checked by
  axiom_check.py R3.

The site-2 obligation is deliberately not a claim about the delivered record
only. Two implementations can deliver the identical record on every admissible
input and still differ on whether the placeholder table was averaged on the way
there, and on whether some lookup addressed an entry the ratio table does not
have; the first is correct and the others each raise inside `fit()`. Those
differences are invisible to any postcondition over the returned value, so they
are pinned where they actually live — in the admissibility of the selection
against the held candidate table (its entry reality AND its extent), plus the
unforgeable capability the selection grants.

The candidate-table resource is faithful to the real code rather than an artifact
of the model. In the no-refit branch there is exactly ONE `l1_ratios_` in scope
and its extent is fixed before the loop: it is bound once at `logistic.py:1971`
(the user's ratios, penalty `'elasticnet'`) or `logistic.py:1978` (the
one-element `[None]` placeholder) and never rebound. So "the step holds one
candidate table, whose entries are real exactly for the mixing family and whose
actual extent is `candidates_len`" is a true statement about the real state at
`logistic.py:2183-2187`, and it removes freedom from the IMPLEMENTATION, not from
the admissible domain: the extent is not restricted to any particular value, only
tied to the table actually in scope. What the resource forbids is exactly what
the real code never does — addressing `l1_ratios_` outside `[0, len(l1_ratios_))`
— and what it still permits (any provably in-range position, repeated lookups) is
exactly what the real observable does not distinguish.

There is **no kind-3 (unexpressible-changed-op) step**: both operations that
genuinely *changed* — the choice of read arity for the coefficient read (site 1,
modeled by which operand drives `use_joint_layout` and hence which
`read_across_folds` arity is requested) and the choice of absent-marker vs
table-value for the mixing record (site 2, modeled over `Optional`) — ARE the
fix, modeled directly. The unchanged numeric primitives in the block
(`np.argmax`, `np.mean`, `//`, `%`, `np.reshape`) are not changed by the patch
and do not affect the tested observables (attribute shape + absence of
`IndexError`); they are carried as already-computed inputs / inside the
`read_across_folds` axiom and validated out-of-band by `axiom_check.py` (G-AX).

## C.1 Totality (MustTerminate)

Nagini checks partial correctness by default, so a diverging body would satisfy
every postcondition — including the unforgeable capability obligation —
vacuously, while its faithful real patch (an unbounded loop inserted into the
no-refit branch) would hang `fit()` and resolve nothing. Both modeled functions
therefore carry `Requires(MustTerminate(2))`, and the consumed axiom
`read_across_folds` carries `Requires(MustTerminate(1))` (a strictly smaller
measure: the read is bounded straight-line work over a fixed number of folds,
so a caller holding measure 2 can perform it without leaking its obligation).
An implementation containing an unbounded loop (or calling anything not proven
to terminate) fails the obligation-leak check. This matches the real post-patch
code, which is loop-free apart from bounded comprehensions over the folds.

## D. verify(model) ⇒ resolved

`gather_per_class` verifies only if it terminates (C.1) AND its
`Ensures(read_admissible(table_axes))` and `Ensures(summary_table(table_axes))`
are discharged. The capability obligation forces at least one call to
`read_across_folds` with a read arity equal to the table's actual axis rank for
**every** admissible input — including `unresolved_form == UNRESOLVED` — which
forces the branch to be driven by the resolved strategy (A4–A6); that is exactly
the site-1 hunk. The held-table resource forces the converse closure: since the
resource is required by every read at the rank that read is checked against, and
the step holds exactly one instance of it at `table_axes`, **no** read anywhere in
a verifying body can be checked against a different rank. So a verifying
skeleton is the gold hunk possibly with in-bounds reads of the same table
repeated — never the gold hunk plus a read at a rank the layout does not have,
which is the shape that adds a real out-of-range index expression to the block.
No value-echo can fabricate the capability (`model_prepatch_1.py`), and neither
predicate can be `Fold`ed (both are abstract, no body).

The residual freedom a verifying body retains is *value provenance*: having
performed the arity-matching read of the held table, a body may deliver the
summary token without syntactically threading it through that call's result.
This is freedom the SPEC IS RIGHT TO LEAVE, not a residual weakness. Refined,
that shape is the correct branch evaluated twice with the first result unused —
every index expression it executes is in-bounds and the delivered vector is the
gathered one — and it was measured against the correctness oracle: the faithful
patch RESOLVES (3/3 FAIL_TO_PASS, all PASS_TO_PASS). A clause tying the
delivered value to the read's result (e.g. indexing the resource by the table's
contents) would therefore be SPEC-TOO-STRONG: it rejects a correct alternative.
`pos-control-site1-read-then-deliver` pins this side of the boundary and
`rival-echo-no-read` pins the other, so the contract is exactly "every read is
arity-checked against the actual layout and at least one such read happens" —
which is the real observable (no out-of-range index, correct gathered shape),
neither more nor less.
`mixing_record` verifies only if a no-mixing family records the absent marker
and a mixing family records the table value (B3–B4) — AND only if every
selection it performs is a selection of an entry the held candidate table
actually holds: from a table whose entries are real mixing values, at a position
inside that table's actual extent. The first half of that rules out the
record-correcting shape (select unconditionally, then overwrite the record with
the marker), which delivers the gold record on every input yet averages the
placeholder table for the family that has none. The second half rules out the
forged-extent shapes, which likewise deliver the gold record on every input yet
address a position the ratio table does not have (as the delivering selection, as
an extra unused one, or only on the non-singleton domain): since the extent is a
parameter of the resource the step holds exactly one instance of, **no** selection
anywhere in a verifying body can be checked against an extent other than the real
table's. So a verifying skeleton is the gold hunk possibly with in-range lookups
of the same table repeated or taken at another in-range position — never the gold
hunk plus a lookup past its end, which is the shape that adds a real
out-of-range index expression to the block. Together those are exactly the site-2
hunk.

The residual freedom a verifying site-2 body retains is WHICH in-range entry it
selects. This is freedom the SPEC IS RIGHT TO LEAVE, not a residual weakness: the
per-class mixing record is observed in the no-refit path only through its shape
(`l1_ratio_.shape == (n_classes,)`), and the one assertion on an `l1_ratio_`
value belongs to the refit path, which this hunk does not touch. A clause pinning
the position to the gold index expression would therefore be SPEC-TOO-STRONG —
it would reject a correct alternative — so `pos-control-site2-other-in-range-position`
pins that side of the boundary and the five forged-extent rivals pin the other,
making the contract exactly "every selection is of an entry the table has",
neither more nor less. By the R-refinements (categorical `str`↔`int`/`bool`, the array-rank
abstraction, the `None` sentinel, the value-irrelevant numeric tokens) and the
G-AX-sound `read_across_folds` axiom, the verified skeletons equal the gold
patch's two hunks on the tested inputs, and the gold patch resolves (G-RESOLVE).
The trust points are the G-AX soundness of the `read_across_folds` axiom and the
A-reference sentinel fact (axiom_check.py) and refinement fidelity (this
document, G-EQ) — PLAN §1.1.

The held-table resource is faithful to the real code rather than an artifact of
the model. In the no-refit branch there is exactly ONE `coefs_paths` in scope per
loop iteration and its rank is fixed before the read: it is bound once at
`logistic.py:2084`, reshaped by the resolved `multi_class` at
`logistic.py:2086-2106` (4 axes for the joint layout via reshape + two
`swapaxes`, 3 axes otherwise), and rebound per class only in the independent arm
at `logistic.py:2124`. So "the step holds one summary table, whose actual rank is
`table_axes`" is a true statement about the real state at `logistic.py:2172-2178`,
and it is available at the real call site rather than restricting which inputs the
real code must handle — the resource removes freedom from the IMPLEMENTATION, not
from the admissible domain (the admissibility case
`admiss-site1-arity-establishable` re-discharges the arity `Assert` under it, and
`pos-control-site1-duplicate-read` pins that repeated in-bounds reads stay legal).
G-PANEL-2 measured `table_rank(resolved) == the real array's ndim` on traced live
gather states with zero drift, so the rank the resource is indexed by is the real
`ndim`.

## E. Parameters the conformance shadow does not read

Three of the shadow bodies in `conformance_check.py` ignore a parameter the
contract constrains. The dangerous version of that shape is a contract that
permits an input the real callee REFUSES, with the bridge never noticing. Each
was checked by running the real patched statements on inputs the contract
permits:

* `read_across_folds` ignores `summary_token`. Legitimate, and required: the
  contract's only claim about the token is `Ensures(Result() == summary_token)`,
  which DEFINES it as whatever the real across-folds read yields. The shadow is
  handed `None` for it and recomputes the real indexed mean from the case's
  actual array, which `check_one` then `np.array_equal`-diffs against the
  oracle. A shadow that echoed the token instead would make the site-1 diff
  vacuous. No token value can disagree with the real callee.
* `gather_per_class` ignores `unresolved_form`. Legitimate, and it IS the fix:
  the patched read branches on the resolved local `multi_class`, so it is a
  function of `resolved_strategy` alone. All six (resolved, unresolved) pairs the
  contract permits were run through the real patched statements: every one is
  accepted, and for a given resolved value the gathered vector is identical
  across all three unresolved values. The bridge's driver varies
  `unresolved_tag` and feeds it to the real tail, so this independence is
  positively checked, not assumed. The pairs unreachable in the real caller
  (e.g. resolved joint with the attribute `'ovr'`) are admitted deliberately:
  widening the domain adds obligations, and it is what makes
  `model_prepatch.py`'s read of the attribute reachable and refutable.
* `mixing_record` ignores `selected_index` and `candidates_len`. These are not
  output parameters — the recorded value is the real average or the absent
  marker — they are the ADMISSIBILITY parameters the held
  `candidate_table(family_has_mixing, candidates_len)` carries, so a value diff
  alone leaves them dead. The real boundary was measured: for a 4-entry ratio
  table every position in `[0, 4)` is accepted and averages to a finite number,
  while position `4` raises `IndexError: index 4 is out of bounds for axis 0
  with size 4`. The extent the resource carries therefore coincides exactly with
  the real table's acceptance boundary — sound (it admits nothing the callee
  refuses) and unrestrictive (it forbids nothing the callee accepts).
  `_check_extent_boundary` now asserts that boundary, plus containment of the
  real flat decomposition, on every conformance case; G-CONF re-passed with it
  over 100072 inputs and 6 full patched `refit=False` fits, 0 disagreements.

The one genuine over-permissiveness the check surfaced is the VALUE claim at
site 2: `Ensures(Result() == mixing_value)` holds at any in-range
`selected_index`, while the real lookup at a different in-range position yields a
different ratio (measured: positions 0/1/3 give 0.000000/0.333333/1.000000 where
the gold position 2 gives 0.666667). This is the residual freedom already
declared above, and it is not the "permits a refused input" shape: the real
callee accepts every position the contract permits. It is also not
oracle-visible — recording the position-0 value for all three classes still
gives `l1_ratio_.shape == (3,)` with every entry finite, which is all the
no-refit test asserts — so pinning the position would be SPEC-TOO-STRONG for the
reason given above.

## H. What the verifier's FRONT END refuses, and why the battery no longer relies on it

Three uniqueness rivals in `properties.py` are fabrication probes: they ask
whether an implementation can obtain one of the four abstract `@ContractOnly`
`@Predicate`s — `summary_table(rank)`, `candidate_table(reality, extent)`,
`mixing_selected()`, `read_admissible(rank)` — at a parameterisation the step was
never handed. They were originally written with `Fold`, and that turned out to
measure nothing about this specification. Measured directly on the three rival
modules (`SBN_PARALLEL_VERIFIERS=1`, `scripts/nagini_verify.sh`):

```
Translation failed
Invalid program: abstract.predicate.fold (.../model.py@299.4)    # summary_table(4)
Invalid program: abstract.predicate.fold (.../model.py@364.8)    # mixing_selected()
Invalid program: abstract.predicate.fold (.../model.py@364.8)    # candidate_table(..., +1)
```

Nagini's `translate_fold` raises `InvalidProgramException('abstract.predicate.fold')`
for any predicate whose target is `contract_only`, so the program is turned down
by the FRONT END, at 22-25s, before Viper is started. Viper therefore issued no
judgment at all. The other minting construct is closed the same way and was
measured too: `Assume(summary_table(4))` exits with
`Invalid program: invalid.contract.position`, because `translate_assume`
translates its argument in a PURE position and a predicate access is not one — so
`Assume` cannot inhale a resource here either.

Both refusals are facts about the LANGUAGE, not about this spec: the identical
`Fold` line is refused in a bundle whose contracts require nothing at all. The
G-PBT backend screen (`backends/nagini.py:_no_verdict`) is right to record such a
run as `no-verdict` rather than as a rejection — and until 2026-08-15 it did not,
so this bundle carried a `G-PBT=pass` in which the three cases were stamped
`rejected` in ~10s on the strength of a translation error. That stamp certified
nothing about the resource discipline.

**Re-expression, not exclusion.** No case was dropped. Each of the three now
states the same fabrication as an ASSERTED CLAIM ABOUT THE STATE, which nagini
does translate, so Viper has to decide it from the spec's own resource discipline:

| case (renamed) | claim asserted | Viper's refutation |
|---|---|---|
| `rival-conjure-summary-table` | `Assert(summary_table(4))`, then the extra joint read it would license | `insufficient permission to access summary_table(4)` |
| `rival-site2-conjure-selection` | `Assert(mixing_selected())` before any selection, then delivers the value | `insufficient permission to access mixing_selected()` |
| `rival-site2-conjure-candidate-table` | `Assert(candidate_table(family_has_mixing, candidates_len + 1))`, then the out-of-extent selection it would license | `insufficient permission to access candidate_table(family_has_mixing, (candidates_len + 1))` |

This is strictly more evidence than the `Fold` form produced, in two ways. It is
a verdict rather than a refusal, and it is a statement about every reachable
state of the step rather than about one syntactic form: no admissible input puts
a table of rank 4, a table of extent `candidates_len + 1`, or a selection
capability into the step's state, at any program point. The `Fold` route stays
closed as well — it is simply closed by the language, which is why it is recorded
here instead of being scored.

**Non-vacuity controls (the `Assert(False)` question).** An `Assert` that can
never be discharged would reject those three rivals no matter what the spec said,
which is the exact hazard a guarded self-call has when its guard is infeasible.
Two `expect="verify"` soundness cases were added as the control, and both
verify:

* `pos-control-site1-held-table-assertable` asserts `summary_table(table_axes)`
  before and after the gold read and `read_admissible(table_axes)` after it.
* `pos-control-site2-held-table-assertable` asserts
  `candidate_table(family_has_mixing, candidates_len)` before the gold selection
  and `mixing_selected()` plus the returned table after it.

So a predicate assertion IS dischargeable at exactly the parameterisations the
contract makes available, and each of the three rejections is attributable to
the rank / extent the rival named for itself, or to the selection it never
performed — never to the construct. Battery after the change: 33 cases
(7 soundness, 1 admissibility, 25 uniqueness), `G-PBT=pass` SOUND, 0 failed,
0 no-verdict.
