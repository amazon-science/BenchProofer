# refinement.md — sphinx-doc__sphinx-7910

The operation-by-operation correspondence between `model.py`'s implementation
(the `skip_decision` impl region and the consumed `canonical` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses this axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `_skip_member` class-owner resolution

Gold hunk (`sphinx/ext/napoleon/__init__.py`), plus the import it adds:
```
+ from sphinx.util import inspect
  ...
-                         cls = obj.__globals__[cls_path]
+                         cls = inspect.unwrap(obj).__globals__[cls_path]
```

| # | model.py impl op (`skip_decision`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `obj: MemberObj` (fields `has_doc`, `is_class_member`, `cls_name`, `ns`) | the member object `obj: Any` of `_skip_member` | R | rich function/method object ↔ minimal class with only the touched fields (mapping.md §2). |
| A2 | `if not obj.has_doc: return None` | `has_doc = getattr(obj, '__doc__', False)` guarding the whole owner block (`__init__.py:424,426`); when false the function falls through to `return None` | R + I | `obj.__doc__` truthiness ↔ `has_doc`; the abstain-on-no-doc control flow is identical. |
| A3 | `canon = canonical(obj)` | `inspect.unwrap(obj)` (the newly-called `sphinx.util.inspect.unwrap`) | **A-consumed** | `canonical` is the weakest contract on `inspect.unwrap` the proof needs: it recovers the original object, preserves `has_doc`/`cls_name`/`is_class_member`, and — the substantive clause — its namespace `Result().ns` records ground-truth ownership (`obj.cls_name in Result().ns and Result().ns[obj.cls_name]` ⇔ `obj.is_class_member`). The proof consumes exactly this `Ensures` (it discharges the asserts A5 and the postcondition). G-AX confirms it against the real `inspect.unwrap` (mapping.md §3.1). |
| A4 | `cls_is_owner = False; if obj.cls_name in canon.ns: cls_is_owner = canon.ns[obj.cls_name]` | `cls = inspect.unwrap(obj).__globals__[cls_path]` (KeyError → `except: cls_is_owner = False`) then `cls_is_owner = (cls and hasattr(cls,name) and name in cls.__dict__)` (`__init__.py:441-446`) | R + I | the two-step `cls_path in <globals>` (membership / KeyError) and `name in cls.__dict__` are observed only through their conjunction `cls_is_owner`, collapsed into the boolean `canon.ns[cls_name]` keyed by the class name (mapping.md §2). The guarded lookup (`key in ns` before `ns[key]`) ↔ the try/except KeyError handling. The `<globals>` source is `canon = canonical(obj)` ⇔ `inspect.unwrap(obj)` — the one changed operand. |
| A5 | `Assert(cls_is_owner == obj.is_class_member)` (discharged by A3's axiom) | (proof step; no runtime counterpart) | A-consumed | not a repo op — it is the proof bridge: the unwrapped-namespace lookup recovers true ownership, which is exactly the axiom's substantive `Ensures`. |
| A6 | `if cls_is_owner: if (is_special and inc_special) or (is_init and inc_init) or (is_private and inc_private): return False` | `if what=='module' or cls_is_owner: … if ((is_special and inc_special) or (is_private and inc_private) or (is_init and inc_init)): return False` (`__init__.py:450-462`) | I | identical boolean control flow on the class/exception branch (the modeled `what`). The three category settings are the `napoleon_include_*_with_doc` configs (mapping.md §2). |
| A7 | fall through to `return None` | the implicit `return None` at `__init__.py:463` | I | identical: any case that is not "documented, owned, enabled-category" abstains. |

## B. The discriminator — the one operand that changed

The ONLY operation the patch changes is the **source of `__globals__`** in
step A4: `obj.__globals__` (pre-patch) → `inspect.unwrap(obj).__globals__`
(post-patch). In the model this is `obj.ns` vs `canonical(obj).ns`. The frozen
spec pins the result to the GROUND-TRUTH ownership (`is_class_member`), which —
by the `canonical` axiom (A3, A-consumed) — is exactly what the **unwrapped**
namespace recovers. A decorator-wrapped member’s OWN namespace (`obj.ns`) need
not contain the class, so an implementation that resolves ownership through
`obj.ns` (the pre-patch operand) cannot prove `cls_is_owner == is_class_member`
and FAILS the postcondition. This is `model_prepatch.py`: identical spec, the
single edit `canon.ns` → `obj.ns`, and it fails on
`(Result() is False) == (has_doc and is_class_member and …)` — the spec sensing
the change (G-DIFF). The F2P test `test_class_decorated_doc` is precisely this
case: a `functools.wraps`-decorated documented special member that must yield
`False` (include), where the pre-patch yields `None` (skip).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — switching the `__globals__` source to the unwrapped object — is the
`canonical(obj)` call, an **A-consumed** axiom over the **unchanged** library
primitive `inspect.unwrap` (which the new code merely *invokes*; the patch does
not change `inspect.unwrap` itself). There is **no axiom about the function
under change** (`_skip_member` is modeled directly as `skip_decision`); the only
consumed axiom covers the unchanged callee the patch newly calls. There is no
A-reference (no operation was modeled as a deep fold here).

## D. verify(model) ⇒ resolved

`skip_decision` verifies only if its result equals the ground-truth inclusion
decision `has_doc ∧ is_class_member ∧ enabled-category` (the postcondition),
and that decision is dischargeable ONLY by resolving ownership through the
unwrapped namespace (A3, A5). By R (the field bijection of §2 and the
`cls_is_owner` collapse) the verified body equals
`inspect.unwrap(obj).__globals__[cls_path]` ownership resolution feeding the
unchanged `_skip_member` control flow; by G-AX the `canonical` axiom is sound
against the real `inspect.unwrap`. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
