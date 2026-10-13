# refinement.md — django__django-12125

The operation-by-operation correspondence between `model.py`'s implementation
(the `serialize_type` impl region and the deep `dotted_path`/`import_line`
models in the `pure` region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee/operation by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The changed function — `TypeSerializer.serialize()` (`serializer.py:259`)

Gold hunk (`django/db/migrations/serializer.py:272`):
```
             if module == builtins.__name__:
                 return self.value.__name__, set()
             else:
-                return "%s.%s" % (module, self.value.__name__), {"import %s" % module}
+                return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}
```

| # | model.py impl op (`serialize_type`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `module, simple_name, qualified_name : List[int]`, `module_is_builtin : bool` | `module = self.value.__module__`; `self.value.__name__`; `self.value.__qualname__`; the boolean `module == builtins.__name__` | R | `str` ↔ `List[int]` code points (mapping.md §1, §2); the branch boolean is identical Python `bool`. The `hasattr(self.value, "__module__")` guard and the `models.Model`/`type(None)` special-cases (lines 260-267) are unchanged control-flow context — every tested value has a `__module__`, so the model takes the texts + flag directly (`I`). |
| A2 | `if module_is_builtin:` → `frag = [] + simple_name`, `imp = []`; `return (frag, imp)` | `if module == builtins.__name__: return self.value.__name__, set()` | I + R | identical branch; the bare simple name (`R`: str↔List[int]) and the empty import set (`R`: `set()` ↔ empty `List[int]`, `len(Result()[1]) == 0`). UNCHANGED by the patch; modeled for skeleton faithfulness. |
| A3 | `else:` → `frag2 = module + [46] + qualified_name`, proven `== dotted_path(ToSeq(module), ToSeq(qualified_name))` | `else: return "%s.%s" % (module, self.value.__qualname__), ...` | A-reference | the changed string operation is modelled **deeply**: `dotted_path` (the spelled-out concatenation `module ++ "." ++ qualified_name` in the `pure` region) and the verified impl ARE the format string. No consumed `serialize_type` axiom — the proof never depends on one. The deep model is validated **== the real format string** out-of-band: G-AX (axiom_check.py) reconstructs the gold `"%s.%s" % (module, value.__qualname__)` and asserts `dotted_path == it` on nested/top-level/enum/built-in classes (incl. the F2P nested-enum shapes) + 20 000 fuzz classes (mapping.md §3.1). The `%s` splice of two whole strings around a literal `.` is exactly list `+` with `[46]`. |
| A4 | `imp2 = [105,109,112,111,114,116,32] + module`, proven `== import_line(ToSeq(module))` | `{"import %s" % module}` | A-reference | the non-built-in import set is the singleton module import; the model encodes its single element `"import " ++ module`. The set wrapper is the identity on its one element under the F2P comparison (mapping.md §2). G-AX asserts the real post-patch import set has exactly one element == `import_line(module)` (mapping.md §3.2). |
| A5 | `return (frag2, imp2)` | `return (string, imports)` | R | the 2-tuple `(str, set)` refines as `(List[int], List[int])` per mapping.md §2; `Result()[0]`/`Result()[1]`. |

The discriminating content of the change — the non-built-in fragment is keyed by
the **fully-qualified name** (`module.Enclosing.Leaf`) rather than by the
**bare leaf name** (`module.Leaf`) — lives in step A3: the post-patch result
equals `dotted_path(module, qualified_name)` (built from `qualified_name`),
whereas the pre-patch built `module ++ "." ++ simple_name` from `simple_name`.
`model_prepatch.py` reproduces that pre-patch by-leaf-name form and **fails** the
postcondition `Implies(not module_is_builtin, ToSeq(Result()[0]) ==
dotted_path(ToSeq(module), ToSeq(qualified_name)))`, which is exactly the spec
sensing the change (G-DIFF). Confirmed: Nagini reports *"Postcondition of
serialize_type might not hold. Assertion Implies((not module_is_builtin),
(ToSeq(Result()[0]) == dotted_path(ToSeq(module), ToSeq(qualified_name)))) might
not hold."* — the discriminating clause, because `simple_name` and
`qualified_name` are independent inputs that differ exactly in the nested case.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — keying the non-built-in class path on the fully-qualified name
instead of the bare leaf name — is modelled **deeply** (the spelled-out
concatenation `dotted_path` in the `pure` region, consumed by the verified
`serialize_type` impl, step A3, an **A-reference**), not hidden behind an axiom
about the function under change: there is **no consumed `@ContractOnly` axiom**
in this bundle (the `axioms` region is empty). The unchanged import construction
is the other **A-reference** (`import_line`, A4), validated by G-AX, not a
consumed axiom.

## C. verify(model) ⇒ resolved

`serialize_type` verifies only if, in the non-built-in branch, its first output
equals the fully-qualified rendering `dotted_path(module, qualified_name)` (A3)
and its second output equals the singleton module import `import_line(module)`
(A4), and in the built-in branch the bare simple name with no import (A2). By R
(str ↔ List[int]; the set wrapper as identity on its ≤1 element; the 2-tuple
refinement; the branch boolean) the verified output equals
`"%s.%s" % (module, self.value.__qualname__), {"import %s" % module}` in the
non-built-in branch (and `self.value.__name__, set()` in the built-in branch) on
the tested inputs; by G-AX the deep models `dotted_path`/`import_line` equal the
real post-patch format string and import set (A-references). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model references — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ); no consumed
axiom is in play.
