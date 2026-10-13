# refinement.md — django__django-17087

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildReference` `do` block and the deep `referencePath` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == a real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs**: the changed assembly is modeled deeply and validated entirely by
G-CONF (see §C). Claim: any impl verifying against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reference-assembly branch — `FunctionTypeSerializer.serialize` (`serializer.py:166-173`)

Gold hunk:
```
             klass = self.value.__self__
             module = klass.__module__
-            return "%s.%s.%s" % (module, klass.__name__, self.value.__name__), {
+            return "%s.%s.%s" % (module, klass.__qualname__, self.value.__name__), {
                 "import %s" % module
             }
```

| # | Solution.lean impl op (`buildReference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `module : String` | `module = klass.__module__` | R | `str` ↔ `String`; the defining module path, read off the value (mapping.md §1, §2). |
| A2 | parameter `clsChain : List String`, `require clsChain ≠ []` | `klass.__qualname__` (post-patch middle component), as its `.`-split component list | R | `__qualname__` ↔ the ordered enclosing-qualifier chain; `str.split('.')` ↔ `List String`; a class qualname is always non-empty (mapping.md §2). This is the component the patch changes: `__qualname__` (full chain) replaces `__name__` (innermost only). |
| A3 | parameter `memberName : String` | `self.value.__name__` (final component) | R | `str` ↔ `String`; the bound member's own name, unchanged by the patch (mapping.md §1). |
| A4 | `let out := (module :: clsChain) ++ [memberName]` | `"%s.%s.%s" % (module, klass.__qualname__, self.value.__name__)` | I | identical concrete op: the post-patch format string concatenates the three components with `.` separators; modeled as the component list `[module] ++ clsChain ++ [memberName]`, joined on `.` by G-CONF. The format `"%s.%s.%s"` over `klass.__qualname__` (a possibly-dotted chain) yields exactly `module . <chain> . member`. |
| A5 | `return out` (`List String`) | the returned `(reference_string, {"import %s" % module})` tuple | R | the dotted reference `str` ↔ the `List String` joined on `.` (mapping.md §2); the unchanged second tuple element (the import set, `{"import %s" % module}`) depends only on `module`, is untouched by the patch, and is re-exercised verbatim end-to-end by G-CONF. |

Discriminating content of the change — the owning class is named by its **full
enclosing-qualifier chain** rather than its **bare innermost name** — lives in
`out = referencePath module clsChain memberName` (model, where `referencePath`
splices the WHOLE `clsChain`) ⇔ the `klass.__qualname__` middle component (real).
The pre-patch code used `klass.__name__` (the innermost name only);
`Solution_prepatch.lean` reproduces that (`[module, clsChain.getLast!,
memberName]`) and **fails** the clause `out = referencePath module clsChain
memberName` (G-DIFF) — e.g. at `clsChain = ["WriterTests", "NestedChoices"]` the
innermost-only path drops `WriterTests`, but the spec demands the full chain.

## B. The supporting (non-discriminating) postconditions

| # | Solution.lean construct | role | tag | justification |
|---|---|---|---|---|
| B1 | `ensures out.length = clsChain.length + 2` | the reference carries the whole chain plus the module and the member (no qualifier dropped) | I (spec-side) | structural invariant of the assembly; an innermost-only impl gives length `3` regardless of chain depth, so this clause (with B-discriminator) rules it out for deep chains. Grounds the postcondition in the inputs (SPEC_GUIDE §0.8). |
| B2 | `ensures out.head? = some module` | the reference begins with the module path | I (spec-side) | pins the first component to the actual `module` input, not an oracle. |
| B3 | `ensures out.getLast? = some memberName` | the reference ends with the member's own name | I (spec-side) | pins the last component to the actual `memberName` input; together with `out = referencePath …` forces the entire chain to sit, in order, strictly between them. |

B1–B3 are not separate impl ops; they are additional `ensures` clauses the
single returned value must satisfy, tightening the spec so no wrong assembly
verifies (G-PANEL attacker 1 / G-MUT). They are provable from `referencePath` by
`simp`/`loom_solve`.

## C. No A legs; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom** and **no A-reference**: the
one operation that genuinely *changed* — which class-name attribute supplies the
reference's middle component — is modeled **deeply** as plain structural
assembly of name components (`referencePath`), and the components themselves are
attribute reads modeled as free inputs (`module`, `clsChain`, `memberName`), not
callees with assumed contracts. Therefore nothing is audited by G-AX (G-AX
`skip`, no `axiom_check.py`); the deep model's fidelity to the real patched
`serialize` is established end-to-end by **G-CONF** over ≥10⁵ fuzzed
`(module, clsChain, memberName)` triples (nesting depth 1..5).

## D. verify(Solution) ⇒ resolved

`buildReference` verifies only if its output equals the full-chain reference
`referencePath module clsChain memberName` (A4), spans `clsChain.length + 2`
components (B1), begins with `module` (B2) and ends with `memberName` (B3). By R
(`str ↔ String`, `__qualname__` ↔ the `.`-split chain, the `List String` ↔
dotted-string join, the unchanged import-set tuple element) the verified assembly
equals the patched `"%s.%s.%s" % (module, klass.__qualname__,
self.value.__name__)`; by G-CONF the R/I transliteration of that assembly agrees
with `patch.diff`'s observable behaviour (the dotted reference the real
`serializer_factory(...).serialize()` emits for a bound class method of a nested
class) on ≥10⁵ inputs, including the gold F2P shape and the depth-1/depth-≥2
edges. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
sole trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms to trust.
