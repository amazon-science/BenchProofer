# refinement.md — sympy__sympy-22456

Maps every op in `implementation_reconstructString` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom),
**A-reference** (deep model, G-AX-validated == real callee), **I** (identical op).

The modeled behavior is the argument-reconstruction round-trip of the atomic
`codegen.ast` string value, under EVERY argument-passing convention that value
publishes about itself: `expr.func(*expr.args) == expr` for the positional
argument list AND `expr.func(**expr.kwargs()) == expr` for the keyword mapping.
The F2P test asserts BOTH identities, so both are modeled; the spec quantifies
over the convention (`∀ c : ReconCall, result c = some s`) rather than fixing
one. The gold patch makes that value a genuine atom whose reconstruction callable
(`func`) consumes no reconstruction data at all and returns the value itself,
while the data the value publishes under each convention is likewise empty — so
the callable admits exactly what the value publishes, on both conventions, and
each round-trip reproduces the value.

Why the quantification is load-bearing rather than decorative: the two
conventions can be honoured INDEPENDENTLY, and a value that honours one while
refusing the other is wrong even though a one-convention model would accept it.
Both directions are real and both are measured (see the table's last column and
`properties.py`'s `convention-split-*` rivals):

| variant of the real callee | `args` | `kwargs()` | `func(*args)` | `func(**kwargs())` | F2P `test_String` |
|---|---|---|---|---|---|
| pre-patch | `()` | `{'text': ...}` | `TypeError` | ok | FAIL |
| gold patch | `()` | `{}` | ok | ok | PASS |
| positional-only (reconstruction callable admits no keyword, value still publishes one) | `()` | `{'text': ...}` | ok | `TypeError` | FAIL |
| keyword-tolerant alternative (callable accepts any arguments, keyword mapping left as-is) | `()` | `{'text': ...}` | ok | ok | PASS |

Rows 1 and 3 fail on OPPOSITE conventions, so no single-convention clause can
reject both. Row 4 matters as much: it resolves the F2P without emptying the
keyword mapping, so the modeled property must be the AGREEMENT between what the
value publishes and what its callable admits — NOT "the keyword mapping is
empty", which is incidental to the gold spelling and would make row 4 (a correct
alternative implementation) fail. `properties.py`'s `pos-tolerant-callable` is
the standing control for that.

| # | `implementation_reconstructString` op | `patch.diff` counterpart | tag |
|---|---|---|---|
| 1 | `let args := stringArgs s` (empty positional arg list of the atomic value) | `String.args == ()`: every slot (`text`) is in `not_in_args`, so `Token.__new__` passes NO positional arg to `Basic`; the value has no positional children (`sympy/codegen/ast.py` Token `__new__` + String `not_in_args`) | R: a `codegen.ast.String` ↔ `StringObj`; its positional arg tuple `()` ↔ `stringArgs s = []` |
| 2 | `let kwargNames : List String := []` (the keyword names the atomic value publishes about its own reconstruction) | post-patch `String.kwargs` returns `{}` (`sympy/codegen/ast.py`, the new `kwargs` member); the value publishes no reconstruction keyword | R: the real keyword mapping's KEY SET ↔ `List String`. Only the key set is modeled, because that is what determines whether the callable admits the call; the values are the value's own text, already carried by `s.text` |
| 3 | `reconstructPositional args` / `reconstructKeyword kwargNames` (the value's reconstruction callable applied to the value's own self-reported data, per convention, yielding the value itself) | post-patch `String.func` property returns `lambda: self`; `class String(Atom, Token)` — the callable consumes no reconstruction data and returns `self`, so it admits exactly the empty positional list and the empty keyword mapping the value publishes, giving `func(*args) == self` AND `func(**kwargs()) == self` | A-reference: the round-trips `obj.func(*obj.args)` and `obj.func(**obj.kwargs())` of the patched atomic value are modeled DEEPLY (spelled out as "apply the callable to the published data"); G-CONF differential-tests BOTH against the REAL patched `String` |

- No op is changed-inexpressible: the entire round-trip is concrete.
- No consumed axiom: nothing is assumed about an unchanged callee; the
  reconstruction is modeled deeply. → G-AX is a skip (axiom_check.py stub).
- Impl region is NOT all-A-tagged (rows 1–2 are R, row 3 is A-reference with
  concrete R/I content), so G-CONF runs (conf_skip = false). `conformance_check.py`
  observes BOTH conventions, matching the quantified clause: a shadow watching
  only the positional round-trip would not see a value that refuses the keyword
  data it publishes.

## Prepatch (the real bug)
`Solution_prepatch.lean` models the PRE-PATCH `String`: it inherits the GENERIC
reconstruction callable (`Basic.func` = the class constructor), which rebuilds the
value from whatever reconstruction data it is handed. Handed the keyword mapping
the value publishes (`{'text': ...}`) it does reproduce the value; handed the
POSITIONAL list it has no `text` to rebuild from, because that list is empty, so
the positional round-trip fails (`TypeError`) → modeled as `none`. So the prepatch
twin satisfies the keyword leg and violates the positional one — it is row 1 of
the table above, and the quantified clause `∀ c, result c = some s` is then
unprovable at `c = positional` (`none ≠ some s`), exactly mirroring F2P
`test_String`'s new assertion `st.func(*st.args) == st` alongside the assertion
`st.func(**st.kwargs()) == st` that already held.
