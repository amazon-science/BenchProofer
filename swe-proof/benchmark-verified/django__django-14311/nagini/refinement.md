# refinement.md — django__django-14311

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_module_name` impl region, with the opaque `marks_entry` classifier
and the `module_arg` selection built on it) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The module-name selection — `get_child_arguments()` (`django/utils/autoreload.py:226`)

Gold hunk:
```
-    if getattr(__main__, '__spec__', None) is not None and __main__.__spec__.parent:
-        args += ['-m', __main__.__spec__.parent]
+    if getattr(__main__, '__spec__', None) is not None:
+        spec = __main__.__spec__
+        if (spec.name == '__main__' or spec.name.endswith('.__main__')) and spec.parent:
+            name = spec.parent
+        else:
+            name = spec.name
+        args += ['-m', name]
         args += sys.argv[1:]
```

`model.py`'s `select_module_name(name, parent)` models the value placed after
`-m` (the only thing this hunk changes; the `getattr(__main__,'__spec__',None)
is not None` guard, the `'-m'` prefix and the `sys.argv[1:]` tail are unchanged
and observationally constant under the F2P/P2P tests).

| # | model.py impl op (`select_module_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `name: List[int]`, `parent: List[int]` | `spec.name`, `spec.parent` (both `str`) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `sentinel = marks_entry(ToSeq(name))` | `spec.name == '__main__' or spec.name.endswith('.__main__')` | A-reference | the entry-file classification is an unchanged boundary callee, modelled as a FULLY OPAQUE `@Pure @ContractOnly marks_entry` (no `Ensures`; the proof consumes no contract — it treats `marks_entry` as an uninterpreted pure function and the impl calls it). It is NOT an axiom whose `Ensures` the proof relies on; it is a reference the deep model is validated against: the concrete classifier `name == '__main__' or name.endswith('.__main__')` is checked == `marks_entry` (and the resulting `module_arg` selection) code-point-for-code-point by G-AX (mapping.md §3.1). |
| A3 | `if sentinel and len(parent) > 0:` | `if (... ) and spec.parent:` | R | `spec.parent` truthy ↔ `len(parent) > 0` (a `str` is falsy iff empty; mapping.md §2). |
| A4 | copy `parent` into `result` (the `parent`-loop) | `name = spec.parent` | R + I | element-wise copy of the parent code points (the verified `take`-loop) is the identity on the value; ↔ binding `name = spec.parent`. |
| A5 | copy `name` into `result` (the `name`-loop, else branch) | `name = spec.name` | R + I | element-wise copy of the name code points ↔ `name = spec.name`. |
| A6 | `return result` | `args += ['-m', name]` | R | the produced module-name value follows `-m` unchanged; the list wrapping is the identity on the modeled value (mapping.md §2). |

The discriminating content of the change — a **directly-named** module
(`name` not an entry-file package, e.g. `utils_tests.test_module.main_module`)
reproduces as the **name** rather than the parent package — lives in
`module_arg(name, parent) == name` when `not marks_entry(name)`
(model) ⇔ the `else: name = spec.name` branch (real). The pre-patch always used
`spec.parent`; `model_prepatch.py` reproduces that (copies `parent` whenever
non-empty) and **fails** the postcondition
`ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent))`, which is exactly
the spec sensing the change (G-DIFF). This is the single F2P test
`test_run_as_non_django_module_non_package`.

## B. The one opaque A-reference classifier; the grounded selection on top of it

There is exactly **one** `@ContractOnly` callee in the model:
`marks_entry(name) -> bool` — the unchanged entry-file classification performed
by the module-execution machinery (the gold patch CALLS this classification via
`spec.name == '__main__' or spec.name.endswith('.__main__')` but does not
*change* the classification itself; what the patch changes is the *selection*
that consumes the classification). It carries **no contract** (`pass` body): the
proof treats it as a fully opaque uninterpreted pure function and consumes none
of its behaviour. It is therefore an **A-reference**, not an A-consumed axiom —
the deep model is validated against the real callee by `axiom_check.py` (G-AX):
the concrete `name == '__main__' or name.endswith('.__main__')` classifier and
the resulting selection are shown to match `module_arg`'s semantics
code-point-for-code-point on 16 boundary names × 6 parents + 40 000 fuzz inputs
(mapping.md §3.1).

(Audit note: this was originally mislabelled A-consumed with a redundant
`Ensures(Implies(len(name)==0, not Result()))`. That contract was empirically
**dead** — deleting it leaves model.py verifying and model_prepatch.py failing
on the same discriminating postcondition — so the proof never consumed it. Per
SPEC_GUIDE §3 the correct relationship is A-reference; the dead `Ensures` has
been removed so `marks_entry` is purely opaque.)

The *selection* under change — `parent` vs `name`, gated on the classification
and a non-empty parent — is modelled **deeply and grounded in the inputs** by
the pure function `module_arg`, defined on top of `marks_entry` over the real
input carriers `name`/`parent` (no opaque "answer-key" oracle, no lookup
table). An implementation that simply echoes `module_arg(name, parent)` and
materializes it is therefore *correct*, not a cheat (directive 8): the value is
*produced by* the modelled branch over the actual inputs, not merely equal to a
constant. Because `marks_entry` is uninterpreted, no impl can discharge the
postcondition with a constant — it must branch on the real classifier and copy
the actually-selected sequence.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The changed *selection* (which name to
reproduce, based on the classification and a non-empty parent) is modelled
**deeply** by `module_arg` over the input carriers; the unchanged
*classification* (`marks_entry`) is the one opaque A-reference boundary callee
(no contract consumed, G-AX-validated). There is no operation modelled by an
axiom *about the function under change*, and no dead axiom is shipped.

## D. verify(model) ⇒ resolved

`select_module_name` verifies only if its output equals `module_arg` of the
inputs (A1-A6): the qualified name itself for a directly-named module, and the
parent package only for a package executed through its entry file (with a
non-empty parent). By R (`str` ↔ `List[int]`, `spec.parent` truthiness ↔ length,
`args += ['-m', name]` identity) the verified selection equals the gold
`name = spec.parent if (sentinel and spec.parent) else spec.name` on the tested
inputs; by G-AX the deep model `module_arg` (built on the opaque A-reference
`marks_entry`) equals the real `str` classifier+selector code-point-for-code-point
on boundary + 40 000 fuzz inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited A-reference classification — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: the A-reference soundness
(G-AX: deep model == real callee) and refinement fidelity (this document,
G-EQ).
