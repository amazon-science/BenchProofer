# refinement.md — matplotlib__matplotlib-24026

The operation-by-operation correspondence between `model.py`'s implementation
(the `assign_layer_facecolors` impl region, the deep `cyc`/`cyc_prefix` model,
and the `Axes.cycle` read-only field) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change (`lib/matplotlib/stackplot.py`, `stackplot`)

Gold hunks:
```
+import itertools
 ...
     if colors is not None:
-        axes.set_prop_cycle(color=colors)
+        colors = itertools.cycle(colors)
+    else:
+        colors = (axes._get_lines.get_next_color() for _ in y)
 ...
-    color = axes._get_lines.get_next_color()
     coll = axes.fill_between(x, first_line, stack[0, :],
-                             facecolor=color, label=next(labels, None),
+                             facecolor=next(colors), label=next(labels, None),
 ...
     for i in range(len(y) - 1):
-        color = axes._get_lines.get_next_color()
         r.append(axes.fill_between(x, stack[i, :], stack[i + 1, :],
-                                   facecolor=color, label=next(labels, None),
+                                   facecolor=next(colors),
+                                   label=next(labels, None),
```

The change has two coupled, jointly-tested effects in the `colors is not None`
branch (the F2P case `colors=["C0","C1","C2"]`):
  (i) the explicit colours are no longer pushed into the Axes property cycle
      (`set_prop_cycle(color=colors)` is removed) — so the Axes colour cycle is
      left untouched (the issue title: "stackplot should not change Axes
      cycler"; this is also what avoids the `ValueError` on `CN` aliases, since
      `set_prop_cycle`'s validator is never invoked);
  (ii) layer `i`'s facecolour is sourced from `itertools.cycle(colors)` —
      `colors[i % len(colors)]`.

| # | model.py impl op (`assign_layer_facecolors`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `colors: List[int]`, `n: int` (layer count `M = len(y)`) | the `colors` sequence, layer count `len(y)` | R | a colour spec ↔ an opaque `int` token (only identity/order/count matter); `M = len(y)` ↔ `n` (mapping.md §2). The `CN`-alias inhabitant that the pre-patch rejects is one token value the model abstracts over. |
| A2 | `axes: Axes` with read-only field `cycle` held at `Acc(axes.cycle, 1/2)` | the Axes object whose line-property-cycle state is read/advanced via `axes._get_lines` and mutated by `axes.set_prop_cycle(...)` | R | the model abstracts the colour-cycle STATE to one opaque snapshot `cycle`; the only observed property is whether the call mutates it (mapping.md §2). Half-permission encodes "read-only" (directive 5). |
| A3 | the removed `set_prop_cycle(color=colors)` is **absent** from the impl; `axes.cycle` is never assigned, so `Ensures(axes.cycle == Old(axes.cycle))` holds | the deleted `axes.set_prop_cycle(color=colors)` line | I (a removal) | the fix removes the mutation; the model's impl simply does not write `axes.cycle`, and the half-permission contract makes any write unverifiable. The pre-patch (`model_prepatch.py`) reinstates `axes.cycle = ToSeq(colors)` and FAILS — exactly the spec sensing effect (i). |
| A4 | `result[i] == cyc(ToSeq(colors), i) == colors[i % len(colors)]`, built by the loop and pinned by `ToSeq(Result()) == cyc_prefix(ToSeq(colors), n)` | `facecolor=next(colors)` after `colors = itertools.cycle(colors)`, once per layer | A-reference | the changed colour-source operation is modelled **deeply**: `cyc`/`cyc_prefix` (spelled-out modular indexing in the `pure` region) and the verified loop ARE the cyclic reading. There is no consumed axiom. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) draws `n` values from the real `itertools.cycle(colors)` and asserts it equals `[colors[i % len(colors)] for i in range(n)]`. `itertools.cycle` repeats from the beginning (docs.python.org/3/library/itertools.html#itertools.cycle), which is exactly `i % len(colors)` (mapping.md §3). |

## B. No consumed axioms

The bundle has no `@ContractOnly` axiom. The only library operation the changed
code introduces — cycling a finite colour sequence — is integer indexing with a
modulus, fully expressible in Nagini, so it is modelled deeply (A4, an
**A-reference**), not hidden behind an axiom. `set_prop_cycle` /
`get_next_color` are referenced only to identify the colour-cycle STATE the fix
must leave untouched; the proof depends on the *absence* of the mutation (A3),
not on any contract for those callees.

## C. Scope: the modelled branch and the unmodelled `else`

The model specifies the **`colors is not None` branch** (the F2P case). The
gold patch's `else` branch (`colors = (axes._get_lines.get_next_color() for _
in y)`) draws `M` colours from the Axes cycle; the pre-patch likewise drew `M`
colours via `get_next_color()` per layer, so the per-layer colour SEQUENCE is
identical pre/post in the no-colours case — that branch is not the tested
behaviour and is deliberately out of modelled scope (mapping.md §2). The tested
delta lives entirely in the `colors is not None` branch, where the change is
both (i) no Axes-cycle mutation and (ii) `itertools.cycle` sourcing — both
captured above. Because the two effects are coupled in a single hunk, a single
`model_prepatch.py` (which reinstates the mutation) is the differential witness;
the cycling postcondition is shared, frozen spec, validated against the real
`itertools.cycle` by G-AX.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — sourcing each layer's colour from a cycle of the supplied colours,
and dropping the property-cycle mutation — is modelled **deeply** (the
spelled-out modular index `cyc`/`cyc_prefix`, consumed in
`assign_layer_facecolors`, A4) and **structurally** (the removed mutation, A3),
not hidden behind an axiom about a callee. There is no consumed axiom at all.

## E. verify(model) ⇒ resolved

`assign_layer_facecolors` verifies only if (1) it never mutates `axes.cycle`
(A3 — guaranteed by the half-permission read-only contract and the
`axes.cycle == Old(axes.cycle)` postcondition), and (2) its output is exactly
the cyclic reading `colors[i % len(colors)]` per layer (A4). By R (colour-token
abstraction, `M = len(y) = n`, Axes-state snapshot) the verified routine equals
the gold `stackplot` on the `colors is not None` branch on the tested input
(`colors=["C0","C1","C2"]`, 3 layers ⇒ facecolours C0, C1, C2, Axes cycle
untouched), which is what the F2P image comparison checks. By G-AX the deep
model `cyc_prefix` equals the real `itertools.cycle` drawing (A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited A-reference — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
(here A-reference) soundness (G-AX) and refinement fidelity (this document,
G-EQ).

## F. Counter-tracking obligations in the impl region (decidability, measured)

Three proof obligations sit in the impl region purely so that a WRONG loop is
rejected in arithmetic rather than on a recursive-sequence identity the solver
cannot settle:

```
        i = i + 1
        Assert(cyc_prefix_len(ToSeq(colors), i))
        Assert(len(ToSeq(result)) == i)      # per step
    Assert(i == n)                            # after the loop
```

They add obligations and assume nothing (no `Assume`, no axiom, no contract
change): every `Requires` / `Ensures` and both `@Pure` lemma bodies are
untouched, so `markers.spec_signature` is byte-identical to the audited spec and
the retained G-EQ / G-PANEL attack batteries still describe what ships.

Why they are here, measured (nagini 1 verifier per run, `SBN_PARALLEL_VERIFIERS=1`,
host load 50–300 on 96 cores, gold verifying in 17–25s throughout):

| artifact | rival | cap | wall | verdict |
|---|---|---|---|---|
| without them | `while i < n` → `while i > n` | 1800s | 1800.2s | **no verdict** (exit 124) |
| without them | `i = i + 1` → `i = i + 0` | 1800s | 1800.1s | **no verdict** (exit 124) |
| with them | `while i < n` → `while i > n` | 900s | 15.4s | rejected |
| with them | `i = i + 1` → `i = i + 0` | 900s | 18.1s | rejected |

Both rivals are genuinely incorrect (the first paints nothing, the second never
advances), so the old artifact was not turning them down — the solver simply
never came back. Diagnosis: with the counter havoced by the loop and constrained
only by `0 <= i <= n`, the surviving goals are `cyc_prefix(colors, i) ==
cyc_prefix(colors, n)` and a step-wise identity on the same front-recursive
function, and the solver does not converge on either. Pinning the counter to the
painted length turns both into linear arithmetic on `i`, which is decided
immediately. G-MUT went from `killed 5/5, 2 no verdict` (rate `5/7`, under the
0.8 floor once the unjudged are charged to the spec) to `killed 7/7 (100%)`.

Nothing is excluded: every mutant this operator set produces now reaches a real
verdict, so no exclusion needs recording here.

The same three obligations are carried by the G-PBT positive control
(`properties.py:_POS_IMPL`, an inline-append reshape of the loop), which still
verifies — evidence that they are obligations on any correct implementation of
this loop and not a shape fingerprint of the gold one.

Method-level `MustTerminate(2)` and the loop's `MustTerminate(n - i + 1)` were
already present and are unchanged; they are what rejects a diverging rival
(`properties.py` carries the `Fp-partial-diverging` probe), and they are not
what was failing here — the `i = i + 0` rival stalls the solver on the sequence
invariant listed before the measure, not on the measure.

Line-count sensitivity, recorded because it cost a measurement cycle: the same
three obligations with six extra lines of explanatory comment around them left
the `i = i + 0` rival running past 490s at a 900s cap, where the shorter comment
above decides it in 18.1s. The asserts were byte-identical in both; only the
line numbers Nagini stamps into the Viper program differed. The text above is
the measured one and should not be re-flowed without re-running the mutant set.
