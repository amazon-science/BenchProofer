# mapping.md — pytest-dev__pytest-7324

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 19ad5889353c7f5f2b65cc2acd346b7a9e95dfcd`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `src/_pytest/mark/expression.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `encode_ident(ident)` | the identifier branch of `not_expr(s)` — `src/_pytest/mark/expression.py:162-164` (the `ast.Name(ident.value, ast.Load())` node construction) | modeled changed function — site 1 (the name placed into the compiled program for an identifier) |
| `lookup_key(key)` | `MatcherAdapter.__getitem__(self, key)` — `src/_pytest/mark/expression.py:174-175` (the `return self.matcher(key)` lookup) | modeled changed function — site 2 (the membership lookup performed when the program is evaluated) |
| `match(name)` *(axiom — A-consumed)* | `self.matcher` — the `Callable[[str], bool]` membership predicate passed to `MatcherAdapter.__init__` (`src/_pytest/mark/expression.py:171-172`) and ultimately to `Expression.evaluate` (`:207`) | unchanged user-supplied callee the lookup consults; an arbitrary deterministic predicate |
| `sentinel()` | the fixed prefix code point added to identifiers (the post-patch module constant set to the dollar sign `"$"`, U+0024) | pure spec: the single sentinel code point prepended to / stripped from a name |
| `strip_sentinel(name)` | the slice that removes the leading prefix from a name before the lookup (`key[len(PREFIX):]`, post-patch `MatcherAdapter.__getitem__`) | pure spec: recover the original identifier from a prefixed name |

The pre-patch repo behaviour the change replaces (for the refinement audit; not
referenced from the consumer spec view):
- site 1: `not_expr` built `ast.Name(ident.value, ast.Load())` — the bare
  identifier as the program name. For the three reserved spellings `True`,
  `False`, `None` this is an `ast.Name` whose id is a keyword/constant; on
  CPython 3.8+ `compile()` rejects it (`ValueError: identifier field can't
  represent 'True' constant`, and on a debug build the interpreter aborts on
  the `compiler_nameop` assertion). The F2P tests `test_valid_idents[True]`,
  `[False]`, `[None]` exercise exactly this.
- site 2: `MatcherAdapter.__getitem__` returned `self.matcher(key)` — the raw
  program name, which post-patch carries the sentinel prefix; the predicate
  would then be asked about the prefixed name rather than the identifier the
  user wrote.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the identifier `ident.value`; the AST `Name.id`; the lookup `key`) | `List[int]` of Unicode code points | `s[k]` ↔ `xs[k] == ord(s[k])`; `len(s)` ↔ `len(xs)`; `str` concatenation (`PREFIX + ident`) ↔ list `+`; the slice `key[len(PREFIX):]` ↔ `xs.drop(1)` (the prefix is exactly one code point) |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes a list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `ast.Name(id, ast.Load())` node | the `List[int]` returned by `encode_ident` (its `id` content) | the only field the change touches is the `id` string; the `ast.Load()` context and node wrapping are constant and observation-irrelevant, so the node is modeled by its `id` code-point list. The fix's *correctness*-relevant property is that this `id` is a legal program name (never bare `True`/`False`/`None`) and round-trips. |
| the membership predicate `self.matcher` (`Callable[[str], bool]`) | `match(name: PSeq[int]) -> bool` axiom | a `str -> bool` function ↔ a `PSeq[int] -> bool` function under the `str ↔ List[int]` carrier |
| the fixed string prefix (the `"$"` constant) | `sentinel() == 36` and `PSeq(sentinel())` | the prefix is the single code point U+0024 (`ord("$") == 36`); `len(PREFIX) == 1`, so adding/removing it is a one-element prepend/`drop(1)` |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; specifications are phrased over `PSeq[int]` via `ToSeq`.

### Termination obligation
Both contracted functions carry `Requires(MustTerminate(2))` (with a
decreasing `MustTerminate` measure on each loop). The repo counterparts are
plain straight-line/linear-scan operations that always return; the obligation
records that liveness fact so the value postconditions cannot be discharged
vacuously by an implementation that never returns.

### Why the sentinel value matters (and why 36)
The fix is correct for ANY prefix that (a) is exactly one code point, (b) is not
a word character (so it cannot collide with the body of a real identifier), and
(c) does not begin a Python keyword/constant spelling. The real patch uses `"$"`
(U+0024, code point 36). The model fixes `sentinel() == 36` to match the real
patch exactly; the safety clauses `Result()[0] != 84/70/78` (the first code
points of `True`/`False`/`None`) are the property that makes the emitted name a
legal program name, and `36` satisfies them. axiom_check.py asserts the real
`IDENT_PREFIX == "$"`, pinning the model's `36` to the patch.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `match` ↔ the user membership predicate `self.matcher` (A-consumed)
**Callee:** the `Callable[[str], bool]` passed to `Expression.evaluate(matcher)`
and stored on `MatcherAdapter` (`src/_pytest/mark/expression.py:171-172,207`).
It is an arbitrary, caller-supplied total predicate (in the F2P tests it is
`{ident: True}.__getitem__`). The patch does NOT change it.

The axiom encodes **only** the property the proof relies on: `match` is a
deterministic function of its argument (no constraint on the boolean it
returns). This is the weakest contract sufficient for `lookup_key`'s
postcondition `Result() == match(strip_sentinel(ToSeq(key)))` — the lookup just
forwards the recovered identifier to the predicate.

**Why it is sound (and why it is the crux of the change):** the membership
predicate must be consulted on the identifier the user actually wrote. Site 2
strips the one sentinel code point so that `match` receives the original
identifier, exactly inverting the prepend at site 1. G-AX records the argument
the real machinery passes to the predicate and asserts it is the original
identifier (round trip) and that repeated evaluation is deterministic.

### 3.2 Deep models (A-reference) — sites 1 and 2 vs. the real operations
The two *changed* operations are modeled DEEPLY (spelled out), not behind an
axiom; G-AX validates the deep models against the real callees:

- **site 1** `encode_ident(ident) == PSeq(36) + ToSeq(ident)` ↔ pytest's
  `not_expr`, which builds `ast.Name(IDENT_PREFIX + ident.value, ast.Load())`
  with `IDENT_PREFIX == "$"`. axiom_check.py asserts the real AST `Name.id` is
  `"$" + ident` for every identifier (including `True`/`False`/`None`) and that
  the expression `compile()`s without the 3.8+ rejection/abort.
- **site 2** `lookup_key(key) == match(strip_sentinel(ToSeq(key)))` ↔ pytest's
  `MatcherAdapter.__getitem__`, which returns `self.matcher(key[len(IDENT_PREFIX):])`.
  Since `len(IDENT_PREFIX) == 1`, the slice removes exactly one leading code
  point — `strip_sentinel == drop(1)`. axiom_check.py asserts the predicate is
  consulted on the de-prefixed identifier.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`_pytest.mark.expression` (the very module the gold patch edits; importable in
the official eval container), asserts `IDENT_PREFIX == "$"`, and exercises the
three reserved spellings plus a spread of ordinary/exotic identifiers the
grammar accepts (word chars, `:`, `+`, `-`, `.`, `[`, `]`, non-ASCII). For each
it checks: site-1 `Name.id == "$"+ident` and the AST compiles; site-2 the
predicate is consulted on the original identifier; the `match` axiom is
deterministic. Exit 0 iff every obligation holds. Imports are the standard
library `ast`/`sys` plus the patched module under test — nothing else.
