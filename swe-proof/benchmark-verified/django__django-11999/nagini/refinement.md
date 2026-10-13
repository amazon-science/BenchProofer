# refinement.md — django__django-11999

The operation-by-operation correspondence between `model.py`'s implementation
(the `preserve_existing_accessor` and `install_missing_accessor` impl regions,
which share one guarded-installation skeleton) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, proof uses the axiom's `Ensures`, and **A-reference**,
a deep model validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single change site — `Field.contribute_to_class` choices branch

Gold hunk (`django/db/models/fields/__init__.py:765-767`):
```
-        if self.choices is not None:
-            setattr(cls, 'get_%s_display' % self.name,
-                    partialmethod(cls._get_FIELD_display, field=self))
+        if self.choices is not None:
+            if not hasattr(cls, 'get_%s_display' % self.name):
+                setattr(
+                    cls,
+                    'get_%s_display' % self.name,
+                    partialmethod(cls._get_FIELD_display, field=self),
+                )
```

The model spells out the post-fix branch (the `self.choices is not None` guard
is the trigger under which both modelled functions operate, mapping.md §2):
```python
if accessor_name not in cls:
    cls[accessor_name] = generated_accessor()
```

| # | model.py impl op (both functions) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `cls: Dict[int, int]` | the model class object `cls` (an attribute namespace) | R | class attribute namespace ↔ `Dict[int,int]` name-token→identity-token (mapping.md §2); `hasattr`/`setattr`/binding ↔ `in`/assignment/value. |
| 2 | parameter `accessor_name: int` | `'get_%s_display' % self.name` | R | the display-accessor name `str` ↔ an `int` token; only name equality/inequality is observed (mapping.md §2). |
| 3 | guard `accessor_name not in cls` | `not hasattr(cls, 'get_%s_display' % self.name)` | R | the resolvability test on the class ↔ key membership (mapping.md §2). This is the operation the gold patch ADDS. |
| 4 | `cls[accessor_name] = generated_accessor()` | `setattr(cls, 'get_%s_display' % self.name, partialmethod(cls._get_FIELD_display, field=self))` | A-reference | the installed generated accessor is modeled DEEPLY as the constant identity `generated_accessor()`; its concrete label-returning behaviour (`Model._get_FIELD_display`, base.py:941-944) is observed by G-AX, which validates the deep guarded-installation == the real `contribute_to_class` (preserve vs install, both declaration orders). There is NO consumed axiom. |
| 5 | (when `accessor_name in cls`) no write | (when `hasattr` true) no `setattr` — the `else` of the new guard | I | both leave the existing binding untouched: the deep model's conditional skips the assignment, exactly as the gold `if not hasattr` skips the `setattr`. |
| 6 | `Requires(MustTerminate(2))` — the step runs to completion and returns | the patched branch is straight-line (one `hasattr` test, at most one `setattr`): it always returns, so `contribute_to_class` returns and `ModelBase.__new__` completes the class | I | boundedness of the concrete step. Not a type refinement and not an axiom: the real branch's control flow is unconditionally finite, and the model states that as an obligation rather than leaving it implicit. Budget 2 is what the single guarded namespace write costs; the gold skeleton pays it with room to spare. |

The discriminating content of the change — *do not overwrite an existing
`get_<name>_display`* — lives in step 3/5: the guard. It is sensed by the
postcondition `cls[accessor_name] == Old(cls[accessor_name])` of
`preserve_existing_accessor`. The pre-patch code omits the guard and overwrites
unconditionally; `model_prepatch.py` reproduces that (the unconditional
`cls[accessor_name] = generated_accessor()` in both functions) and **fails**
exactly that postcondition (G-DIFF: `model_prepatch.py:97`, the preservation
clause of `preserve_existing_accessor`). The `install_missing_accessor`
behaviour is unaffected by the bug and still verifies in the prepatch — the
failure is sharply localized to the one fixed behaviour.

## Boundedness is a stated obligation, not an assumption (step 6)

An earlier revision of this document had **no row about whether the operation
returns**, and every clause above is about *what is written*. A G-EQ / G-PANEL-1
audit turned that silence into a counterexample. Viper proves **partial**
correctness: an `Ensures` is claimed only of runs that reach the return, so an
implementation that never returns satisfies the whole postcondition surface
vacuously — including the quantified whole-namespace frame added to close the
*previous* audit's finding, since doing nothing forever respects a frame
perfectly. Two same-spec impls that re-enter the modeled step on unchanged
arguments (bare, and inside the guard this document calls the "byte-identical
installation skeleton") verified; their faithful patches hang model-class
assembly, so 0/1 F2P and 0/30 P2P. Vacuity controls (`Assert(False)` after the
self-call) failed, confirming the program point was reachable and the recursion
genuinely taken rather than dead under an infeasible guard.

`Requires(MustTerminate(2))` on both modeled functions closes it. The write axis
and the termination axis are **independent** — no clause about *what* is written
can constrain *whether* the step finishes, and vice versa — so the earlier repair
could not have covered this and this one does not subsume it. The obligation is a
consumable budget: a self-call must be handed a strictly smaller measure to prove
progress, which an unchanged-argument re-entry cannot supply, so the
obligation-leak check fires at the call site. The frozen impl is a single guarded
assignment and pays nothing for it (G-VERIFY, G-GOLD). `properties.py` carries
`rival-diverge-preserve` / `rival-diverge-install` so the clause is held
non-vacuous by the reject lane in both modeled behaviours, and both admissibility
probes exercise their `Requires` predicate directly rather than by self-call (a
self-call would need a `Decreases` the spec does not carry — a proof gap in the
probe, not a precondition defect).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the `hasattr` guard around the `setattr` — is modeled
**deeply** (the spelled-out `if accessor_name not in cls` in both impl regions),
not hidden behind an axiom about the function under change. There is no consumed
`@ContractOnly` axiom; the only A-tagged step (4) is an **A-reference** whose
deep model `axiom_check.py` validates == the real `contribute_to_class`.

## verify(model) ⇒ resolved

`preserve_existing_accessor` verifies only if, when an accessor of the name is
already present, the bound identity is unchanged (step 5; the
`cls[accessor_name] == Old(cls[accessor_name])` clause) — i.e. an author-defined
`get_<name>_display` survives assembly. `install_missing_accessor` verifies only
if, when no such accessor exists, the generated one is installed
(`cls[accessor_name] == generated_accessor()`). Each also pins one per-key frame
fact: a representative unrelated attribute keeps its exact bound identity
(`cls[other_name()] == Old(cls[other_name()])`) — an impl that clobbers that
attribute fails verification.

## Frame fidelity is a verified postcondition

Whole-namespace frame fidelity — that the operation adds/alters at most the
accessor key and disturbs no *other* attribute — is **stated and verified as
quantified postconditions** in both functions:

  * `preserve_existing_accessor` (this case performs NO write):
    `Forall(k: (k in cls) == Old(k in cls))` and
    `Forall(k: k in cls and Old(k in cls) ⇒ cls[k] == Old(cls[k]))`.
  * `install_missing_accessor` (this case writes AT MOST the accessor key):
    `Forall(k: k != accessor_name ⇒ (k in cls) == Old(k in cls))` and
    `Forall(k: k != accessor_name and k in cls and Old(k in cls) ⇒
    cls[k] == Old(cls[k]))`.

Each quantifier carries an explicit trigger (`[[k in cls]]` /`[[cls[k]]]`),
which is what makes the obligation tractable on Nagini 1.2.0: without triggers
the same clauses do not converge within the verification budget. With triggers
the clauses are **non-vacuous** (empirically confirmed): an impl that writes any
key other than the accessor key — adding a fresh unrelated key, or rebinding a
pre-existing one, in either function — fails verification on exactly these
clauses, while the gold guarded skeleton (and its correct reshapes: the
branch-reorder and the precondition-redundant unconditional install) verifies.
These clauses close the spec-admittance gap a G-EQ audit demonstrated against
the earlier per-key-only frame (a same-spec impl that installed the accessor
AND wrote one extra unrelated key verified; it no longer does). The
per-key value preservation facts (`Old(cls[k])` for the accessor key and
`other_name()`) are retained as the sharp, named witnesses the PBT rivals
target. The quantified frame exactly mirrors the gold patch's single guarded
`setattr` of `'get_%s_display' % self.name`, which touches no other attribute.

By R (class namespace ↔ `Dict`, `hasattr` ↔ `in`, `setattr` ↔ assignment) the
verified guarded installation equals the gold `if not hasattr: setattr(...)`; by
G-AX the deep model equals the real `contribute_to_class` (the A-reference, step
4). Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited A-reference — and the gold patch
resolves (G-RESOLVE). This holds TOTALLY rather than partially: by step 6 the
verified operation also returns, so the postconditions above are claims about a
step that finishes, and the class it assembles is usable. The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
