# refinement.md — sympy__sympy-22456

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`reconstructInvariance` `do` block, plus the deep `applyPos`/`applyKw`/
`exposedArgs` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized/deep-modeled callee — **A-consumed**
where the proof uses an axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The argument-invariance site — `String` (`sympy/codegen/ast.py:872`)

Gold hunks (the behavioural ones; the two whitespace/import-only hunks are
inert — see §C):
```
- class String(Token):
+ class String(Atom, Token):
      ...
+     def kwargs(self, exclude = (), apply = None):
+         return {}
+
+     #to be removed when Atom is given a suitable func
+     @property
+     def func(self):
+         return lambda: self
```

| # | Solution.lean impl op (`reconstructInvariance`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s : StrObj` (`text : List Char`) | a `String` instance `self` | R | rich object → structure with only the touched field `text`; `str ↔ List Char` (mapping.md §1, §2). G-CONF bridges via `String(t)` with `t = s.text` as a Python `str`. |
| A2 | `let kind := FuncKind.noArgForm` (returned as `out.kind`) | the added `@property func: return lambda: self` | R | the reconstruction function `func` accepts a no-argument call and returns the object. `FuncKind.noArgForm` models that arity (mapping.md §1). The impl's ONLY observable outputs are `out.kind`/`out.kwNames` — there is no free outcome value to echo (anti-echo, §E). |
| A3 | `let kwNames : List (List Char) := []` (returned as `out.kwNames`) | the added `def kwargs(...): return {}` | R | the `kwargs()` view exposes no keyword names; `{}` ↔ `[]` (mapping.md §2). Load-bearing: with the no-argument `func`, a non-empty keyword set would make `func(**kwargs())` raise (the half-fix prepatch). |
| A4 | postcondition `applyPos out.kind s (exposedArgs s) = some s` | evaluating `self.func(*self.args) == self` | A-reference + I | `exposedArgs s = []` is the deep model of the UNCHANGED `String.args == ()` (A-reference, mapping.md §3.1). `applyPos` is the concrete reconstruction-call semantics (I): the positional call reproduces the object → `some s`. The verdict is PRODUCED by applying the impl's recorded `out.kind` to the structural args view; it is not a value the impl may assert. Forces `out.kind = noArgForm` (`oneArgForm` on empty args → `none`). |
| A5 | postcondition `applyKw out.kind s out.kwNames = some s` | evaluating `self.func(**self.kwargs()) == self` | I | `applyKw` is the concrete reconstruction-call semantics: the keyword call reproduces the object → `some s`. PRODUCED by applying `out.kind` to the recorded `out.kwNames`; given `out.kind = noArgForm` (from A4), forces `out.kwNames = []` (any keyword → `none`). |
| A6 | `return { kind, kwNames }` | the post-patch `String` reconstruction signature the test exercises | R | the record carries only the two structural choices; the two invariance identities are the postcondition (A4/A5), not record fields. `some s ↔ (call) == self`, `none ↔ (call) raises` (mapping.md §2). |

Discriminating content of the change — applying the object's `func` to its own
empty positional `args` must reproduce the object
(`applyPos out.kind s (exposedArgs s) = some s`) AND applying it to its keyword
`kwargs()` must reproduce it (`applyKw out.kind s out.kwNames = some s`)
**simultaneously**. These two clauses jointly force the unique verifying
`(out.kind, out.kwNames) = (noArgForm, [])` — the gold reconstruction signature
(see §E). There are two independently-fixed
behaviours, each with its own failing prepatch:

* `Solution_prepatch.lean` (the original bug): `func` is the inherited
  constructor (`FuncKind.oneArgForm`) and `args` is empty, so `func(*args)`
  supplies no value for the required `text` specifier and raises —
  `applyPos oneArgForm s [] = none` — failing
  `applyPos out.kind s (exposedArgs s) = some s`. This is the exact `TypeError`
  the F2P test `st.func(*st.args) == st` exposes.
* `Solution_prepatch_2.lean` (a half-fix): `func` is made a no-argument form
  (`FuncKind.noArgForm`) — fixing positional invariance — but `kwargs()` is
  left exposing `["text"]`. Then `func(**kwargs())` passes an unexpected `text`
  keyword to the no-argument function and raises — `applyKw noArgForm s ["text"]
  = none` — failing `applyKw out.kind s out.kwNames = some s`. This is why the
  gold patch must override `kwargs()` to `{}` in addition to adding `func`.

## B. No consumed axioms

There are no A-consumed axioms. The only A-tagged step is the **A-reference**
`exposedArgs == String.args == []` (A4), a deep model of an UNCHANGED structural
inspection, validated by G-AX. The reconstruction-call semantics
(`applyPos`/`applyKw`) are concrete I ops, mechanically refuted by G-CONF
against the real patched `String`.

## C. Inert gold hunks (refinement audit only)

The gold patch contains two non-behavioural hunks: `from sympy.core.expr import
Expr` → `Expr, Atom` (an import needed only so `String(Atom, Token)` resolves),
and the deletion of one blank line before `class BreakToken`. Neither alters any
observable behaviour; both are carried verbatim so `patch.diff` == gold and
applies cleanly (G-RESOLVE). The `String(Atom, Token)` base-class change is what
gives `String` `is_Atom`/atom semantics; in the model the object is already
atomic (`exposedArgs = []`), so it is absorbed into the A-reference of A4.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed — making
`func` reproduce the object from its (empty) `args` while keeping the keyword
reconstruction valid — is modeled **deeply** (`FuncKind` + `applyPos`/`applyKw`,
the spelled-out reconstruction-call semantics), not hidden behind an axiom about
the function under change. There is no consumed `func`/`kwargs` axiom.

## E. verify(Solution) ⇒ resolved (grounded postcondition — anti-echo)

The impl's ONLY observable outputs are the two structural choices it records:
`out.kind` (the `func` arity) and `out.kwNames` (the `kwargs()` keyword-name
view). There is no `viaArgs`/`viaKwargs` outcome field, so there is nothing for a
directive-8 impl to ECHO. The postcondition has exactly two clauses:
```
applyPos out.kind s (exposedArgs s) = some s   -- (C1) func(*args) reproduces the object
applyKw  out.kind s out.kwNames     = some s   -- (C2) func(**kwargs()) reproduces the object
```
Each verdict is *produced by* applying the impl's recorded choices through the
modeled call semantics (`applyPos`/`applyKw`); it cannot be asserted as a free
value. Because `exposedArgs s = []` (A-reference, validated by G-AX), (C1) reads
`applyPos out.kind s [] = some s`, which holds for `out.kind = noArgForm` and is
**`False` for `out.kind = oneArgForm`** (`applyPos oneArgForm s [] = none` —
no positional value for the required specifier). So a verifying impl is FORCED to
record `out.kind = noArgForm`. Then (C2) reads `applyKw noArgForm s out.kwNames =
some s`, which holds only for `out.kwNames = []` (any other keyword set → `none`).
Hence **the unique `(out.kind, out.kwNames)` that verifies is `(noArgForm, [])`**
— exactly the gold reconstruction signature (`func := lambda: self`, `kwargs() :=
{}`). This is mechanically confirmed: the bare-echo attack the P2 audit found
(`return { viaArgs := some s, viaKwargs := some s }`) no longer type-checks
against this spec (no such fields), and a wrong reconstruction
(`out.kind := oneArgForm`, or `out.kwNames := ["text"]`) is rejected at (C1)/(C2)
respectively (re-tested: exit 1).

Given the forced `(noArgForm, [])`: by R (the `StrObj`/`String` and
`str`/`List Char` bijections, mapping.md §2) these structural choices are the real
patched `String`'s `func`/`kwargs()` signature; by G-AX the deep model
`exposedArgs` equals the real `String.args` (A-reference); by G-CONF the R/I
transliteration of `applyPos`/`applyKw` over the impl's chosen `kind`/`kwNames`
agrees with `patch.diff`'s real `func(*args)`/`func(**kwargs())` reproduction on
the fuzzed inputs. The F2P test adds exactly `assert st.func(*st.args) == st` (the
positional identity (C1) pins) to the already-passing keyword identity
`st.func(**st.kwargs()) == st` ((C2)) — both guaranteed by any model satisfying
this spec. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and an audited UNCHANGED inspection — and
the gold patch resolves (G-RESOLVE).
