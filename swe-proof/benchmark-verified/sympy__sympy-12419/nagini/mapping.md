# mapping.md — sympy__sympy-12419

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 479939f8c65c8c2908bbedc959549a257a7c0b0b`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/matrices/expressions/matexpr.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `diagonal_unit_entry(i, j)` | `Identity._entry(self, i, j)` — `sympy/matrices/expressions/matexpr.py:478` | the modeled changed function (the `(i, j)` entry of an identity matrix) |
| `eq_class(i, j)` *(axiom — A-consumed)* | `Eq(i, j)` then `is S.true` / `is S.false` — `sympy.core.relational.Equality.eval` (`sympy/core/relational.py:284`), result objects `S.true`/`S.false`/unevaluated `Equality` | unchanged community callee: the symbolic 3-valued equality test the new code branches on |
| `struct_eq(i, j)` *(axiom — A-consumed)* | Python structural equality `i == j` (`Basic.__eq__`, `sympy/core/basic.py`), the test the **pre-patch** `_entry` uses; also the `lhs == rhs` short-circuit inside `Equality.eval` (`relational.py:305`) | unchanged callee: structural identity of two index expressions |
| `ONE` / `ZERO` | `S.One` / `S.Zero` (`sympy.core.singleton`) | the two numeric matrix-cell values |
| `DEFERRED` | `KroneckerDelta(i, j)` — `sympy/functions/special/tensor_functions.py:84` | the symbolic deferred delta cell value the new code returns when equality is undecided |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): `_entry` used a plain `if i == j:
return S.One else: return S.Zero` — i.e. it tested only **structural identity**
and treated every structurally-distinct pair as a `0` cell, even when the two
index expressions are not decidably unequal.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| index expression `i` (a SymPy `Expr`/`Symbol`/`Integer`) | `int` used as an opaque identity tag | the model never performs arithmetic on `i`/`j`; they are passed only to the unchanged equality callees. `i`/`j` ↔ their model tags 1:1; equality of tags is NOT used as the semantic test (the callees are). |
| `Eq(i, j)` object reduced to `S.true` / `S.false` / unevaluated | `eq_class(i, j) ∈ {EQ_TRUE=1, EQ_FALSE=0, EQ_UNKNOWN=2}` | `S.true` ↔ `EQ_TRUE`; `S.false` ↔ `EQ_FALSE`; an unevaluated `Equality` (neither `is S.true` nor `is S.false`) ↔ `EQ_UNKNOWN` |
| Python `i == j` (`Basic.__eq__`) | `struct_eq(i, j): bool` | `True` ↔ structurally identical expressions; `False` ↔ structurally distinct |
| `S.One` matrix cell | `ONE = 11` | the unit cell tag |
| `S.Zero` matrix cell | `ZERO = 10` | the zero cell tag |
| `KroneckerDelta(i, j)` matrix cell | `DEFERRED = 12` | the symbolic deferred-delta cell; a value distinct from both `ONE` and `ZERO` (KroneckerDelta is not identical to either `S.One` or `S.Zero` as a SymPy object when `i`, `j` are undecided) |

The result `int` is a 3-valued **tag** identifying which of the three matrix
cells (`S.One`, `S.Zero`, `KroneckerDelta(i, j)`) the entry is — NOT an integer
to be summed. The tag values `{10, 11, 12}` are chosen pairwise distinct and
disjoint from the `EQ_*` codes `{0, 1, 2}` so the entry cannot be produced by
echoing the classifier.

The gold `_entry` additionally has a total-correctness obligation
(`Requires(MustTerminate(2))` in model.py): the real function is a
straight-line, loop-free decision that always returns a cell value (pre- and
post-gold alike), so the obligation is sound; it exists to reject
implementations that satisfy the value postconditions only vacuously by
diverging (see refinement.md A6).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `eq_class` ↔ `Eq(i, j)` + `is S.true` / `is S.false` (A-consumed)
**Callee:** `sympy.core.relational.Equality.eval` (`relational.py:284`). When
`Eq(i, j)` is constructed with the default `evaluate=True`, it returns:
- `S.true` if `i == j` structurally (`relational.py:305-306`), or the difference
  `i - j` is provably zero (`z is True`, line 323-328);
- `S.false` if the difference is provably nonzero (`z is False and
  commutative`, line 324-326), or other decided-unequal paths;
- an **unevaluated `Equality` object** (neither `is S.true` nor `is S.false`)
  when equality cannot be decided — e.g. two distinct integer symbols `i`, `j`.

The new `_entry` reads exactly these three outcomes (`eq is S.true` /
`eq is S.false` / neither). The axiom encodes only the three properties the
proof needs:
  (a) `eq_class(i, j) ∈ {EQ_TRUE, EQ_FALSE, EQ_UNKNOWN}` (totality / trichotomy);
  (b) reflexivity: `eq_class(i, i) == EQ_TRUE` (line 305: `lhs == rhs ⟹ S.true`);
  (c) the structural-identity link (§3.2): `struct_eq(i, j) ⟹ eq_class(i, j)
      == EQ_TRUE`.
It does NOT claim the callee decides any particular undecided pair — for two
distinct symbols `eq_class` may be `EQ_UNKNOWN`, which is the whole point.

### 3.2 `struct_eq` ↔ Python `i == j` (A-consumed)
**Callee:** `sympy.core.basic.Basic.__eq__` — structural (tree) equality of two
SymPy expressions; this is what the **pre-patch** `_entry` tests, and what
`Equality.eval` short-circuits on at `relational.py:305`. Axiom property used:
  (a) reflexivity: `struct_eq(i, i)` is `True`;
  (b) the link to semantic equality: `struct_eq(i, j) ⟹ eq_class(i, j) ==
      EQ_TRUE` (structural identity is a *sufficient* condition for `Eq` to
      reduce to `S.true`, never to `S.false` or unevaluated). The converse does
      NOT hold (semantically-equal but structurally-distinct pairs exist), and
      the axiom does not claim it.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `Eq` and `==` on
boundary + fuzz index pairs (identical symbol, distinct symbols, integer pairs
equal/unequal, `i` vs `i+1`, `i` vs `i+k`, mixed) **inside the instance image**
and asserts: every `Eq(i,j)` reduces to exactly one of `S.true`/`S.false`/
unevaluated (trichotomy); `Eq(i,i) is S.true` and `(i==i)` (reflexivity);
whenever `(i==j)` is `True` then `Eq(i,j) is S.true` (the §3.2 link); and the
*discriminating* witness — for distinct symbols `i`, `j`, `(i==j)` is `False`
(old ⇒ `S.Zero`) while `Eq(i,j)` is unevaluated, i.e. `EQ_UNKNOWN` (new ⇒
`KroneckerDelta`, not `S.Zero`). It imports only `sympy` (the repo under test).
Exit 0 iff sound.

## G-CONF (differential conformance — `conformance_check.py`)

**Shadow:** the `# impl-start` / `# impl-end` region of `model.py`
(`diagonal_unit_entry`) copied VERBATIM into `shadow_entry`, contracts stripped.
The model IS Python, so nothing is transliterated. The `pure` region is empty
(no `@Pure` helper to carry over) and no Nagini carrier appears in the signature
(`i`, `j`, result are plain `int`), so no `PSeq`/`ToSeq` shim is needed. The
`@ContractOnly` callee `eq_class` has no body to copy, so the shadow calls the
REAL callee it axiomatizes — `Eq(i, j)` read through `is S.true` / `is S.false`
(§3.1) — which EXERCISES the axiom instead of assuming it. `struct_eq` is not
called from this impl region (it is consumed only by the pre-image twin), so it
carries no shadow obligation; G-AX covers it.

**Oracle:** the real patched repo function, **called, not transliterated** —
`Identity._entry(self, i, j)` (`sympy/matrices/expressions/matexpr.py:478`, §1),
reached as `Identity(Symbol('n', integer=True, positive=True))._entry`. The gate
applies `patch.diff` to /testbed and sets `PYTHONPATH` before the script runs;
the script applies no patch and reimplements nothing. Boundary inputs are also
cross-checked through the public accessor `Identity(n)[i, j]`
(`MatrixExpr.__getitem__` → `_entry`), the path the F2P `test_Identity` drives;
`__getitem__`'s own UNCHANGED bounds validation (`matexpr.py:244`) raises
`IndexError` for indices it cannot place in range (negative-assumption symbols),
and those are skipped and counted on that secondary leg only — every input is
still compared through `_entry` directly. A startup guard reads
`inspect.getsource(Identity._entry)` and refuses to run (exit 1) if the
post-patch `Eq(` / `KroneckerDelta(` tokens are absent, so an unapplied gold
patch cannot produce a silent green.

**Type bridge (§2, inverted — both directions written out and both checked):**
index expressions are generated in the CONCRETE direction (real SymPy `Expr`)
and the same object is handed to both sides, since the model treats `i`/`j` as
opaque tags and only feeds them to the equality callee. Verdict:
`Eq is S.true`↔`EQ_TRUE`, `is S.false`↔`EQ_FALSE`, unevaluated `Equality`↔
`EQ_UNKNOWN`. Result, oracle→model (`tag_of_value`): `S.One`↔`ONE`,
`S.Zero`↔`ZERO`, a `KroneckerDelta` instance↔`DEFERRED`, anything else
unmappable and reported as a disagreement. Result, model→oracle
(`value_of_tag`, the redundant second leg): compared to the oracle value under
`Basic.__eq__`, the same structural equality `test_Identity`'s `In[i, j] != 0`
rests on. Bridge injectivity is not assumed: because `KroneckerDelta(i, j)`
evaluates to `1`/`0` on DECIDED pairs, every `EQ_UNKNOWN` input additionally
asserts the real delta is neither `S.One` nor `S.Zero` (a collapse there would
make §2's "distinct from both numeric cells" claim false and fails the check).

**Inputs — 101162 total, pinned seed `SEED = 12419`.** The model's `Requires` is
`MustTerminate(2)` only (a termination obligation with no data constraint), so
every index pair satisfies it and nothing is filtered. 6 F2P/branch boundary
pairs (the F2P shape `(i, j)` first; then `(i, i)`, `(0, 1)`, `(i, i+1)`,
`(i, i+0)`, `(i, 0)`) + an exhaustive ordered sweep of a 34-expression boundary
pool (34² = 1156 pairs: symbols under assorted assumptions, signed integer
literals, and symbol arithmetic `i±1`, `2*i`, `i+j`, `i*j`, `i**2`, `-i`, `5-i`,
`floor(i/2)`, `Abs(i)`) + 100000 seeded fuzz pairs drawn from 500 randomly built
integer index expressions. All three impl branches are taken, and the
discriminating one dominates: observed `EQ_TRUE=1466`, `EQ_FALSE=12277`,
`EQ_UNKNOWN=87419`, with all 87419 deferred cells confirmed distinct from both
numeric cells.

**Recorded verdict:** `G-CONF=pass`, 0 disagreements over 101162 inputs.
Negative controls confirm the check is capable of failing: (a) run against the
PRE-patch oracle with the guard disabled it reports
`i=i j=j eq_class=EQ_UNKNOWN shadow=DEFERRED oracle=ZERO` and exits 1;
(b) against the pre-patch oracle with the guard active it refuses and exits 1;
(c) with the shadow's third branch mutated to `ZERO` (the pre-patch bug) against
the patched oracle it reports the mirrored disagreement and exits 1.
