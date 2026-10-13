# refinement.md — django__django-11815

The operation-by-operation correspondence between `model.py`'s implementation
(the `serialize_member` impl region and the deep `rendered`/`quoted`/
`import_line` models in the `pure` region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee/operation
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The changed function — `EnumSerializer.serialize()` (`serializer.py:120`)

Gold hunk:
```
     def serialize(self):
         enum_class = self.value.__class__
         module = enum_class.__module__
-        v_string, v_imports = serializer_factory(self.value.value).serialize()
-        imports = {'import %s' % module, *v_imports}
-        return "%s.%s(%s)" % (module, enum_class.__name__, v_string), imports
+        return (
+            '%s.%s[%r]' % (module, enum_class.__name__, self.value.name),
+            {'import %s' % module},
+        )
```

| # | model.py impl op (`serialize_member`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `module, class_name, identifier, payload : List[int]` | `module = enum_class.__module__`, `enum_class.__name__`, `self.value.name`, and (pre-patch only) a renderable `self.value.value` | R | `str` ↔ `List[int]` code points (mapping.md §1, §2). `payload` is the model's witness for `self.value.value`; the post-patch impl reads it not at all. |
| A2 | `frag = module + [46] + class_name + [91] + [39] + identifier + [39] + [93]`, proven `== rendered(ToSeq(module), ToSeq(class_name), ToSeq(identifier))` | `'%s.%s[%r]' % (module, enum_class.__name__, self.value.name)` | A-reference | the changed string operation is modelled **deeply**: `rendered`/`quoted` (the spelled-out concatenation in the `pure` region) and the verified impl ARE the format string. No consumed `serialize_enum` axiom — the proof never depends on one. The deep model is validated **== the real format string** out-of-band: G-AX (axiom_check.py) reconstructs the gold f-string and asserts `rendered == it` and `quoted == repr(name)` on the F2P enums + 20 000 fuzz names (mapping.md §3.1-3.2). The `%r` of an enum member name (a valid identifier) is exactly the single-quote wrap `quoted` encodes. |
| A3 | `imp = [105,109,112,111,114,116,32] + module`, proven `== import_line(ToSeq(module))` | `{'import %s' % module}` | A-reference | the post-patch import set is the singleton module import; the model encodes its single element `"import " ++ module`. The set wrapper is the identity on its one element under the F2P comparison (mapping.md §2). G-AX asserts the real post-patch set has exactly one element == `import_line(module)`. |
| A4 | `return (frag, imp)` | `return (string, imports)` | R | the 2-tuple `(str, set)` refines as `(List[int], List[int])` per mapping.md §2; `Result()[0]`/`Result()[1]`. |
| A5 | `Requires(MustTerminate(2))` (total-correctness obligation) | the real `serialize()` body is a single straight-line format expression — it always returns | I | the real method performs a bounded amount of work with no loop or recursion, so it trivially satisfies the termination obligation. The obligation is load-bearing the other way: WITHOUT it the spec is partial-correctness-only and admits a same-spec impl that diverges before the gold construction (`while True:` ahead of the return) — the P2 audit built exactly that impl, it verified, and its faithful patch hangs the F2P tests (does not resolve). `MustTerminate(2)` makes Nagini's obligation-leak check reject any unbounded loop/callee in the impl region (properties.py case `nontermination-diverge-before-return`). |
| A6 | `plain_token_char` + `Requires(Forall(int, ... plain_token_char(identifier[k])))` (domain-scoping precondition) | the domain of `self.value.name`: a class attribute name always matches `[A-Za-z_][A-Za-z0-9_]*` | R | scopes the modeled slice to exactly the identifiers on which the `quoted` deep model equals the real `%r` rendering (`repr` of such a name is the bare single-quote wrap; mapping.md §3.1, G-AX). WITHOUT it the spec claimed `rendered(...)` for ALL code-point sequences, including names carrying a quote/backslash (reachable only via the enum functional API `Enum('E', {"a'b": 1})`, never via a class-body declaration) where the real rendering escapes or switches delimiter — so the gold-faithful impl violated the postcondition on those inputs and the spec was UNFAITHFUL-too-strong (found by the P2 audit). The precondition removes those out-of-alphabet inputs from the modeled domain instead of mis-describing them; every F2P/caller-reachable name satisfies it. |

The discriminating content of the change — the fragment is keyed by the
**stable identifier** (`Class['NAME']`) rather than by the **mutable payload**
(`Class(value)`) — lives in step A2: the post-patch result equals
`rendered(module, class_name, identifier)` (built from `identifier`), whereas
the pre-patch built `module ++ "." ++ class_name ++ "(" ++ payload ++ ")"` from
`payload`. `model_prepatch.py` reproduces that pre-patch by-payload form and
**fails** the postcondition `ToSeq(Result()[0]) == rendered(...)`, which is
exactly the spec sensing the change (G-DIFF). The failing clause is the string
postcondition — confirmed: Nagini reports
*"Postcondition ... (ToSeq(Result()[0]) == rendered(...)) might not hold."*

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the enum serializer's rendering — is modelled **deeply** (the
spelled-out concatenation `rendered`/`quoted`/`import_line` in the `pure`
region, consumed by the verified `serialize_member` impl, step A2/A3, an
**A-reference**), not hidden behind an axiom about the function under change:
there is **no consumed `@ContractOnly` axiom** in this bundle (the `axioms`
region is empty). The only stdlib operation the rendering leans on — the `%r`
of a simple identifier — is itself an **A-reference** validated by G-AX
(`quoted == repr`), not a consumed axiom.

## C. verify(model) ⇒ resolved

`serialize_member` verifies only if it TERMINATES (A5 — `MustTerminate(2)`
turns the contract into total correctness, closing the diverge-before-return
hole the P2 audit exhibited), its first output equals the exact
name-keyed rendering `rendered(module, class_name, identifier)` (A2), and its
second output equals the singleton module import `import_line(module)` (A3). By
R (str ↔ List[int]; the set wrapper as identity on its single element; the
2-tuple refinement) the verified output equals
`('%s.%s[%r]' % (module, class_name, name), {'import %s' % module})` on the
tested inputs; by G-AX the deep models `rendered`/`quoted`/`import_line` equal
the real post-patch format string and import set (A-references). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited deep-model references — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ); no
consumed axiom is in play.
