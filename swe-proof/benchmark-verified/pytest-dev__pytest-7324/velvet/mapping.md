# mapping.md — pytest-dev__pytest-7324

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 19ad5889353c7f5f2b65cc2acd346b7a9e95dfcd`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deeply-modeled callee.

Repo file under change: `src/_pytest/mark/expression.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `evalBareIdent (ident, matcher)` | the bare-identifier path of `Expression.compile`+`Expression.evaluate` — construction of the name node at `src/_pytest/mark/expression.py:164` (the changed site A) and its lookup through the matcher adapter at `src/_pytest/mark/expression.py:174` (the changed site B) | the modeled changed behavior: compile a single bound name, then look it up through the matcher |
| `compileName` *(deep model — A-reference)* | CPython `compile(ast.Expression(ast.Name(name, Load())), …, "eval")` — invoked at `src/_pytest/mark/expression.py:202`, on the node built at line 164 | unchanged callee: turns one bound-name node into evaluable code; **rejects** names spelled exactly `True`/`False`/`None` (they are `ast` constants, not nameable). Validated `compileName == real compile` by axiom_check.py (G-AX); NOT a consumed axiom |
| `isReservedName` | the set of spellings CPython's `compiler_nameop` / `ast.Name` constructor refuses (`True`, `False`, `None`) | pure spec helper: exactly the three reserved-constant spellings |
| `matcher : List Char → Bool` | the `Callable[[str], bool]` passed to `Expression.evaluate`, reached via `MatcherAdapter.__getitem__` (`src/_pytest/mark/expression.py:175`) | FREE INPUT — the spec makes no claim about its values; the modeled behavior is that the matcher is consulted on the *original* identifier |

The two gold change sites are a single logical change with one shared knob
(`IDENT_PREFIX = "$"`): site A prepends the prefix to the compiled name
(`src/_pytest/mark/expression.py:169`), site B strips it back off before
calling the matcher (`src/_pytest/mark/expression.py:181`). Modeled together as
`evalBareIdent`'s prefix/drop pair — the prefix is `identPrefix` and the strip
is `name.drop identPrefix.length`. The repo prefix character is a
`problem_statement`-neutral sentinel; in the model the concrete sentinel `'$'`
is an internal implementation choice (any character that can never begin a
user-writable bound name works), localized to the elided `impl` region.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `ident.value` / `key` (Python `str`) | `List Char` | `s` (Python str) ↔ `s`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; the prefix `"$"` ↔ `['$']`; `key[len(IDENT_PREFIX):]` ↔ `name.drop identPrefix.length` |
| outcome of `compile(...)` on the name node | `Except CompileErr Unit` | success (a code object is produced) ↔ `Except.ok ()`; the `ValueError`/interpreter-abort CPython raises on a reserved-constant name ↔ `Except.error .reservedConstant`. The code object's *content* is unobservable here (only success/failure and the subsequent matcher lookup are), so it is dropped to `Unit` |
| `MatcherAdapter(matcher).__getitem__(key)` / `matcher(key)` (`Callable[[str],bool]`) | `matcher : List Char → Bool` | total Boolean function on identifiers; `matcher(s)` ↔ `matcher s` |
| value of the evaluated expression for a bare ident | `Except CompileErr Bool` | the `eval` result `bool` ↔ `Except.ok b`; a compile-time failure ↔ `Except.error` |

A single Python character on the BMP ↔ Lean `Char` via `Char.ofNat (ord ch)`,
total and exact. `List Char` indexing/drop is total and sound.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `compileName` deep model ↔ CPython `compile(ast.Name(name), "eval")`
**Callee:** building `ast.Expression(ast.Name(name, ast.Load()))`,
`fix_missing_locations`, then `compile(..., mode="eval")` — exactly the path
`Expression.compile` runs (`src/_pytest/mark/expression.py:201-203`) on the
node `not_expr` builds (line 164/169). This callee is **unchanged** by the gold
patch; only its *argument* (the name string) changes.

Observed behavior (verified empirically on the in-image interpreter, see
axiom_check.py): `compile` of a `Name` node **fails** (raises `ValueError`
"identifier field can't represent '…' constant", and on a debug interpreter
trips the `compiler_nameop` assertion in the problem statement) iff the name
string is exactly one of `"True"`, `"False"`, `"None"`; for every other string
(including keyword-like `if`/`else`/`while`, numeric-looking `1234`,
prefixed `"$True"`, non-ASCII, punctuation-bearing match idents like `a[bcd]`,
empty) it **succeeds**. This is exactly `compileName`:
`isReservedName name → error`, else `ok ()`.

Modeled DEEPLY (spelled out in `pure`), so there is **no `compile` axiom** the
proof consumes — `compileName` is an **A-reference**, validated
`compileName == real compile-of-Name` by axiom_check.py (G-AX) over the three
reserved spellings (the boundary) + fuzzed identifiers.

### 3.2 `matcher` — free input (no axiom)
`matcher` is the user-supplied `Callable[[str], bool]`. It is taken as a free
input; the spec asserts only that it is consulted on the ORIGINAL `ident`
(`out = Except.ok (matcher ident)`), never on the prefixed name. No behavioral
claim, hence no axiom and no G-AX obligation for it.

## 4. G-CONF fuzz seed
Pinned seed: **7324**. conformance_check.py builds the R/I shadow of the
`evalBareIdent` `do` block in Python (the `compile`-of-`Name` callee left as
the real CPython callee, A-reference) and diffs it against `patch.diff`
behaviour over ≥10⁵ fuzzed `(ident, matcher)` inputs drawn from the match-ident
grammar (`(\w|:|\+|-|\.|\[|\])+`) plus the three reserved spellings as forced
boundaries.
