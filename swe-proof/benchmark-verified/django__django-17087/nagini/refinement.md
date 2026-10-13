# refinement.md — django__django-17087

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_class_member_reference` impl region and the deep `member_path`/
`import_line` models in the `pure` region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee/operation by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit`, `git apply --check` OK, and is the real correctness oracle,
G-RESOLVE).

## A. The changed function — `FunctionTypeSerializer.serialize()` (`serializer.py:165`)

Gold hunk (`django/db/migrations/serializer.py:171`), inside the branch taken
when the value is a callable bound to a class object
(`getattr(self.value, "__self__", None) and isinstance(self.value.__self__, type)`):
```
             klass = self.value.__self__
             module = klass.__module__
-            return "%s.%s.%s" % (module, klass.__name__, self.value.__name__), {
+            return "%s.%s.%s" % (module, klass.__qualname__, self.value.__name__), {
                 "import %s" % module
             }
```

| # | model.py impl op (`render_class_member_reference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `module, class_simple_name, class_qualified_name, method_name : List[int]` | `module = klass.__module__`; `klass.__name__`; `klass.__qualname__`; `self.value.__name__` (with `klass = self.value.__self__`) | R | `str` ↔ `List[int]` code points (mapping.md §1, §2). The branch guard `getattr(self.value, "__self__", None) and isinstance(self.value.__self__, type)` is unchanged control-flow context that selects this hunk; every value the F2P/P2P tests route here is a class-bound method, so the model takes the four texts directly (`I` context, see mapping.md §1). |
| A2 | `frag = module + [46] + class_qualified_name + [46] + method_name`, proven `== member_path(ToSeq(module), ToSeq(class_qualified_name), ToSeq(method_name))` | `return "%s.%s.%s" % (module, klass.__qualname__, self.value.__name__)` | A-reference | the changed string operation is modelled **deeply**: `member_path` (the spelled-out concatenation `module ++ "." ++ class_qualified_name ++ "." ++ method_name` in the `pure` region) and the verified impl ARE the format string. No consumed axiom — the proof never depends on one. The deep model is validated **== the real format string** out-of-band: G-AX (axiom_check.py) reconstructs the gold `"%s.%s.%s" % (module, klass.__qualname__, value.__name__)` and asserts `member_path == it` on nested/top-level class-bound methods (incl. the F2P `NestedChoices.method` shape) + 20 000 fuzz shapes (mapping.md §3.1). The `%s.%s.%s` splice of three whole strings around two literal `.`s is exactly list `+` with two `[46]`s. |
| A3 | `imp = [105,109,112,111,114,116,32] + module`, proven `== import_line(ToSeq(module))` | `{"import %s" % module}` | A-reference | the import set is the singleton module import; the model encodes its single element `"import " ++ module`. The set wrapper is the identity on its one element under the F2P comparison (mapping.md §2). G-AX asserts the real import set has exactly one element == `import_line(module)` (mapping.md §3.2). This step is UNCHANGED by the patch; modeled for skeleton faithfulness. |
| A4 | `return (frag, imp)` | `return (string, imports)` | R | the 2-tuple `(str, set)` refines as `(List[int], List[int])` per mapping.md §2; `Result()[0]`/`Result()[1]`. |

The discriminating content of the change — the fragment addresses the callable
through the owning class's **fully-qualified name** (`module.Enclosing.Leaf.method`)
rather than the owning class's **bare leaf name** (`module.Leaf.method`) — lives
in step A2: the post-patch result equals
`member_path(module, class_qualified_name, method_name)` (built from
`class_qualified_name`), whereas the pre-patch built
`module ++ "." ++ class_simple_name ++ "." ++ method_name` from
`class_simple_name`. `model_prepatch.py` reproduces that pre-patch
by-simple-name form and **fails** the postcondition
`ToSeq(Result()[0]) == member_path(ToSeq(module), ToSeq(class_qualified_name),
ToSeq(method_name))`, which is exactly the spec sensing the change (G-DIFF).
Confirmed: Nagini reports *"Postcondition of render_class_member_reference might not
hold. Assertion (ToSeq(Result()[0]) == member_path(ToSeq(module),
ToSeq(class_qualified_name), ToSeq(method_name))) might not hold."* — the
discriminating clause, because `class_simple_name` and `class_qualified_name`
are independent inputs that differ exactly in the nested case.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — keying the rendered fragment on the owning class's fully-qualified
name instead of its bare leaf name — is modelled **deeply** (the spelled-out
concatenation `member_path` in the `pure` region, consumed by the verified
`render_class_member_reference` impl, step A2, an **A-reference**), not hidden behind
an axiom about the function under change: there is **no consumed `@ContractOnly`
axiom** in this bundle (the `axioms` region is empty). The unchanged import
construction is the other **A-reference** (`import_line`, A3), validated by
G-AX, not a consumed axiom.

## C. verify(model) ⇒ resolved

`render_class_member_reference` verifies only if its first output equals the
fully-qualified rendering `member_path(module, class_qualified_name,
method_name)` (A2) and its second output equals the singleton module import
`import_line(module)` (A3). By R (str ↔ List[int]; the set wrapper as identity
on its one element; the 2-tuple refinement) the verified output equals
`"%s.%s.%s" % (module, klass.__qualname__, self.value.__name__),
{"import %s" % module}` on the tested inputs; by G-AX the deep models
`member_path`/`import_line` equal the real post-patch format string and import
set (A-references). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited deep-model
references — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: the A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ); no consumed axiom is in play.
