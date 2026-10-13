# mapping.md — sympy__sympy-14531

Binds every `model.py` symbol to its repository counterpart, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

`base_commit = 205da797006360fc629110937e39a19c9561313e`. **All `file:line`
citations below are in the GOLD-PATCHED instance worktree** (the state G-AX and
G-CONF run against), because that is the source that must make each clause true.
The patch inserts lines, so a few base_commit line numbers are lower by up to 3
(`_print_Rational` 571→574, `_print_Relational` 619→622); the two modeled
methods' own `def` lines are unshifted (`_print_Limit` at 216 either way).

Repo file under change: `sympy/printing/str.py` — the *only* file the gold patch
touches (11 hunks, all in that file). The printer it defines, `StrPrinter`, is
the printer behind the public `sstr` / `str(expr)`, **and it is also a base class
of the python code printer** (`sympy/printing/python.py:15`:
`class PythonPrinter(ReprPrinter, StrPrinter)`), which is unchanged by the patch
but reaches new behaviour *through* it. §1.1 explains why that second receiver is
part of the specification and not a footnote.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line, gold-patched worktree) | role |
|---|---|---|
| `render_equation(wrap, kl, ul, vl, kr, ur, vr, reg)` | `StrPrinter._print_Relational(self, expr)`, the `expr.rel_op in charmap` branch — `sympy/printing/str.py:622` (patched body 636-637) | the modeled changed function: render a relation `Eq(left, right)`. `wrap` ↔ `self._settings['sympy_integers']`; `(kl,ul,vl)` / `(kr,ur,vr)` ↔ the operands `expr.lhs` / `expr.rhs`, each ranging over all three operand kinds (§2); `reg` ↔ the receiver's own name registry `self.symbols` (`python.py:21`). |
| `render_directed_limit(wrap, plus, ke, ue, ve, kz, uz, vz, k0, u0, v0, ud, reg)` | `StrPrinter._print_Limit(self, expr)` — `sympy/printing/str.py:216`, **both** arms (patched bodies 219 and 221-222) | the modeled changed function: render `Limit(e, z, z0, dir)`. `(ke,ue,ve)`, `(kz,uz,vz)`, `(k0,u0,v0)` ↔ `expr.args[0..2]`, each over all three operand kinds; `wrap`, `reg` as above. `plus` ↔ `str(expr.args[3]) == "+"`, the test the method branches on, and `ud` ↔ the handle of `dir = expr.args[3]` itself. **Every slot separately parameterised** because the patched bodies delegate them independently (`tuple(map(self._print, (e, z, z0)))` / `(e, z, z0, dir)`). **When `dir` appears in the output:** exactly when `str(expr.args[3]) != "+"`, and nothing else. `expr.args[3]` is the direction `Symbol` `Limit.__new__` stored (`sympy/series/limits.py:126-146`): the caller's `dir` (default `"+"`), overridden to `"-"` when `z0 is S.Infinity` and to `"+"` when `z0 is S.NegativeInfinity`, and restricted to `'+'`/`'-'`/`'+-'` (else `ValueError`). It is therefore NOT a function of the limit point — measured on the gold worktree, `Limit(x, x, oo)` and `Limit(x, x, 7/2, dir='-')` both take the four-slot arm while `Limit(x, x, -oo, dir='-')` and `Limit(x, x, 7/2)` both take the three-slot one — which is why `plus` is a free parameter rather than a predicate on `(k0,u0,v0)`. |
| `render_name(c, reg)` | `Printer._print(self, expr)` (`sympy/printing/printer.py:238`) dispatching on a `Symbol` — landing on `StrPrinter._print_Symbol` (`str.py:699`) for the TEXT and on `PythonPrinter._print_Symbol` (`python.py:38-42`) for the REGISTRY | the changed call at each NAME slot: post-patch the name operand goes through `self._print(...)`, i.e. through the receiver's own `_print_Symbol`. Pre-patch it was interpolated with a bare `%s` = `str(Symbol)`, which never touches the receiver. Both consequences are modeled: the returned text, and the append to `self.symbols`. |
| `render_operand(wrap, p, q, reg)` | `Printer._print` dispatch (`printer.py:238`) → `StrPrinter._print_Rational` (`str.py:574`), evaluated WITH `self._settings` | the changed call at the FRACTION slot: post-patch each operand is rendered via `self._print(...)` (same printer instance ⇒ same settings); pre-patch via `%s` = `str(operand)` (a FRESH default-settings `StrPrinter`). Modelled so the operand render takes the *parent's* `wrap`, and so that it leaves `reg` alone (a fraction is not a name). |
| `render_rational(wrap, p, q)` *(deep model — A-reference)* | `StrPrinter._print_Rational(self, expr)` — `str.py:574` (the `self._settings.get("sympy_integers", False)` branch at 577-579) | pure spec: the leaf rendering of a proper fraction (`q>=2`, coprime) under a given `sympy_integers` setting; deep model of an *unchanged* leaf renderer, validated `== real sstr(Rational(p,q), sympy_integers=wrap)` by axiom_check.py (G-AX), NOT consumed as an axiom. |
| `is_name(c)` | the carrier predicate for `Symbol(chr(c))` with a one-character lowercase name | pure spec: `97 <= c <= 122`. Every such `c` is a real `Symbol` whose `.name` is both its rendered text and its registry key (checked by the `ax-domain-containment` probe and axiom_check.py). |
| `lit_name(c)` *(deep model — A-reference)* | `StrPrinter._print_Symbol` — `str.py:699` (returns `expr.name`), reached via `Printer._print` | pure spec: the rendered text of a name operand — the single code point that names it. **Setting-independent**: `sstr(Symbol('x'), sympy_integers=True) == sstr(Symbol('x')) == 'x'`. This is precisely why the text of a name slot cannot on its own witness that the OWNING receiver rendered it, and why `registered` exists. |
| `registered(r, c)` *(deep model — A-reference)* | `PythonPrinter._print_Symbol` — `python.py:38-42`:<br>`symbol = self._str(expr)` / `if symbol not in self.symbols: self.symbols.append(symbol)` | pure spec: the receiver's registry after IT renders the name `c` — appended at the end unless already present (one entry per DISTINCT name, in first-render order). Exactly the `if … not in …: append` above. Drained into the `name = Symbol('name')` preamble by `python()` (`python.py:58-69`, one line per entry, in list order). |
| `eq_text` / `limit_text` *(deep model — A-reference)* | the string `_print_Relational` / `_print_Limit` return under `self._settings` (`str.py:636-637` / `str.py:219` and `221-222`) | pure spec: the compound rendering — fixed template, each slot's own text at the compound's OWN setting. `limit_text` has the two template forms `plus` selects: `'Limit(' e ', ' z ', ' z0 ')'` and `'Limit(' e ', ' z ', ' z0 ", dir='" d "')"`. Validated `== real sstr(...)` by axiom_check.py. |
| `eq_registry` / `limit_registry` *(deep model — A-reference)* | the `self.symbols` list after the same two methods run on a `PythonPrinter` receiver | pure spec: the registry after the compound is rendered — one step per slot, left to right, a fraction slot contributing nothing and a name slot one `registered`. In `limit_registry`'s `not plus` form the DIRECTION slot is a step too, and it comes LAST, after all three operands (measured: `symbols` after `Limit(y, z, 7/2, dir='-')` is `['y','z','-']`; after `Limit(x, x, 7/2)` it is `['x']`, the `+` direction being neither printed nor registered). Independent of `wrap` because `python.py:38-42` never consults `_settings`. Validated `== real PythonPrinter.symbols` growth (and `== python()`'s preamble) by axiom_check.py. |
| `digits(n)` *(axiom — A-consumed)* | Python built-in `str(int)` (CPython `int.__str__`) — invoked transitively inside `_print_Rational` to spell `expr.p`, `expr.q` | unchanged leaf callee: the decimal spelling of a non-negative integer. |
| `coprime(p, q)` *(axiom — A-consumed)* | (no single repo node) — the canonicalisation invariant of `Rational(p, q)`: `gcd(p, q) == 1` | abstract domain-restriction predicate: the fractional operand is already in lowest terms, so `digits(p)/digits(q)` faithfully renders `Rational(p, q)`. Proof-irrelevant beyond carving the non-collapsing carrier region. |
| `lit_S_open / lit_close_slash / lit_slash / lit_eq_open / lit_comma_space / lit_rparen / lit_limit_open / lit_dir_open / lit_quote_rparen` | the literal template fragments `'S('`, `')/'`, `'/'`, `'Eq('`, `', '`, `')'`, `'Limit('`, `", dir='"`, `"')"` in the methods' `%`-format strings (the last two only in `_print_Limit`'s four-slot arm) | pure spec: template tokens as code-point sequences |
| `materialize(s)` | (no repo node) | proof helper: realises a `PSeq[int]` spec value as a concrete `List[int]`; pure type-refinement glue, the identity on character content. |

The pre-patch repo state the change addresses (for the refinement audit, not
referenced from the consumer spec view): both methods interpolated **every**
operand with a bare `%s` (e.g. `'%s(%s, %s)' % (charmap[expr.rel_op], expr.lhs,
expr.rhs)` and `"Limit(%s, %s, %s)" % (e, z, z0)`). `%s` invokes `str(operand)` →
`Basic.__str__` → `sstr(self, order=None)` (`sympy/core/basic.py:399-401`), which
constructs a **fresh** `StrPrinter` with the DEFAULT settings
(`sympy_integers=False`) and, being a plain `StrPrinter`, **has no registry at
all**. The operand is therefore rendered by a detached printer: neither the
active `_settings` nor the active `self.symbols` participates. The gold patch
replaces each `%s`-of-operand with `self._print(operand)` (`Printer._print`,
`printer.py:238`), which reuses the SAME receiver and hence both pieces of its
state. (The patch makes that substitution at ~13 `_print_*` sites; the two
modeled here are exactly the two the F2P tests exercise — see §3.)

### 1.1 Why the specification pins TWO observables (the receiver split)

The patched line is one delegation, but the instance's own `FAIL_TO_PASS` pair
reads it through **two different receivers**, and the modeled postconditions
conjoin what each sees:

* `test_Rational` reads it through `sstr` ⇒ a `StrPrinter`, which carries the
  `sympy_integers` **configuration** (`str.py:577`) and no registry. Delegating
  the fraction slot is what makes `sstr(Eq(x, S(2)/3), sympy_integers=True)`
  come out `'Eq(x, S(2)/3)'`.
* `test_python_relational` reads it through `python()` ⇒ a `PythonPrinter`, which
  carries the **name registry** (`python.py:21`, `python.py:38-42`) and — being a
  `ReprPrinter` first — does *not* accept `sympy_integers` at all
  (`repr.py:20-22`: `_default_settings = {"order": None}`, so
  `PythonPrinter({"sympy_integers": True})` raises `TypeError`). Delegating the
  NAME slot is what makes `python(Eq(x, y))` emit the `x = Symbol('x')` preamble
  line.

The two receivers **share the patched method objects** —
`PythonPrinter._print_Relational is StrPrinter._print_Relational` and likewise
for `_print_Limit` (asserted in axiom_check.py, the `ax-render-sound` probe and
conformance_check.py) — so one modeled function faithfully abstracts both
readings. A `PythonPrinter` cannot be used for the text reading, because
`ReprPrinter._print_Rational` (`repr.py:128-129`) renders `Rational(p, q)`
instead of `p/q`; hence the text is read on a `StrPrinter` and the registry on a
`PythonPrinter`, with the shared-method identity carrying the join.

**Pinning only the text would leave the name slots unconstrained.** A name's text
is identical whether the owning receiver rendered it or a detached printer did
(`'x'` either way, under either setting), so a text-only specification is
satisfied by an implementation that emits each name slot as a bare constant
token. That implementation's faithful patch delegates only the fraction; it
resolves `test_Rational` and **fails** `test_python_relational`. The registry
clauses (`registered` / `eq_registry` / `limit_registry`) are what reject it —
see `properties.py::registry-skip-name-equation` and `registry-echo-text-only`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (each method's return value) | `List[int]` of Unicode code points | `s[k]` ↔ `out[k] == ord(s[k])`; `len(s)` ↔ `len(out)`; `"%s%s" % ...` / `+` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `PSeq` `+`/`take`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `self._settings['sympy_integers']` (a `bool`), the receiver's CONFIGURATION | the `wrap: bool` parameter | `True` ↔ wrap on (`'S(p)/q'`); `False` ↔ wrap off (`'p/q'`). Read on a `StrPrinter` receiver (§1.1). |
| `self.symbols` (a `list[str]` of one-character names), the receiver's NAME REGISTRY | the `reg: List[int]` parameter / `PSeq[int]` in the spec | `self.symbols == [chr(c) for c in reg]`, order-preserving; `self.symbols.append(name)` ↔ `reg.append(c)`; `name not in self.symbols` ↔ `not (c in reg)`. Read on a `PythonPrinter` receiver (§1.1). Passed as a *mutable* parameter at FULL `Acc(list_pred(reg))` because the modeled call WRITES it; the postconditions state exactly how it grows, so the permission is not licence to scribble (a rival that scribbles is `properties.py::registry-frac-writes`). |
| one proper-fraction operand `Rational(p, q)` (`q>=2`, lowest terms) | the pair `(p, q)` of `int` with `p >= 0`, `q >= 2`, `coprime(p,q)` | the F2P inputs are non-negative proper fractions (`2/3`, `7/2`, `1/2`); the modeled domain covers them. Whole numbers (`q==1`, dispatched to `_print_Integer`) and non-reduced pairs (which `Rational` reduces) are out of the modeled leaf domain (refinement.md §0); the SAME propagation refinement applies to them verbatim (R). |
| one name operand `Symbol(chr(c))`, one lowercase letter | the code point `c` with `is_name(c)` (97..122) | `Symbol(chr(c)).name == chr(c)` is BOTH its rendered text (`lit_name(c)`, setting-independent) and its registry key (`registered`). Parameterised rather than fixed at `'x'`, so a slot rendered under a hard-coded name is visible (`properties.py::registry-wrong-key`). |
| `expr.p`, `expr.q` spelled by `str(...)` | `digits(p)`, `digits(q)` | the A-consumed axiom; literal `str(int)`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `digits` ↔ `str(int)`, `coprime` ↔ `gcd==1` (A-consumed)
**`digits` callee:** the CPython built-in `str` applied to a non-negative `int`
(`int.__str__`). Inside `_print_Rational` (`str.py:574-580`) the
numerator/denominator are spelled with `"%s" % expr.p` / `expr.q`. The patch does
**not** change this spelling. The axiom encodes only the property the proof
consumes: `digits(n)` is a deterministic function of `n` and **non-empty**
(`len(digits(n)) >= 1`) — so `digits(p)` is the same code-point sequence
whichever `wrap` is active (the wrapper `S(...)` is the only setting-dependent
part). **Soundness (G-AX):** axiom_check.py runs the real `str(n)` over
`n ∈ {0,1,…,large}` and asserts non-empty.

**`coprime` callee:** the canonicalisation invariant of `Rational(p, q)` —
`gcd(p, q) == 1` once constructed. It restricts the operand to the carrier's
non-collapsing region (a non-coprime pair would reduce to a different fraction).
The proof does not otherwise depend on it. **Soundness (G-AX):** axiom_check.py
filters every fuzzed/boundary operand to `gcd(p, q) == 1` (and asserts
`Rational(p, q).p == p and .q == q`, i.e. it did not reduce), exactly the domain
`coprime` denotes.

### 3.2 `render_rational` deep model ↔ `StrPrinter._print_Rational` (A-reference)
**Callee:** `StrPrinter._print_Rational(self, expr)` (`str.py:574`):

```python
def _print_Rational(self, expr):
    if expr.q == 1:
        return str(expr.p)
    else:
        if self._settings.get("sympy_integers", False):
            return "S(%s)/%s" % (expr.p, expr.q)
        return "%s/%s" % (expr.p, expr.q)
```

This leaf renderer is *unchanged* by the patch; it already reads
`self._settings`. The modeled domain (`q >= 2`, coprime) is exactly the `else`
branch. It is modelled **deeply** by the `@Pure` `render_rational` (no consumed
axiom). The deep model is validated `== the real render` out-of-band by
axiom_check.py at the **public dispatch entry point** (never a hand-picked leaf
method): for a coprime non-integer grid + fuzz of `(wrap, p, q)` it asserts
`render_rational(wrap, p, q) == sstr(Rational(p, q), sympy_integers=wrap)`. The
discriminating value: `wrap=True ⇒ 'S(p)/q'`; `wrap=False ⇒ 'p/q'`.

### 3.3 `lit_name` / `registered` deep models ↔ the two `_print_Symbol`s (A-reference)
**Text callee:** `StrPrinter._print_Symbol` (`str.py:699`) returns `expr.name`,
reached from a name slot via the patched `self._print(...)`. It reads no setting,
so `lit_name(c)` is a bare code point and axiom_check.py asserts
`sstr(Symbol(chr(c)), sympy_integers=wrap) == chr(c)` for all 26 keys under
**both** settings.

**Registry callee:** `PythonPrinter._print_Symbol` (`python.py:38-42`):

```python
def _print_Symbol(self, expr):
    symbol = self._str(expr)
    if symbol not in self.symbols:
        self.symbols.append(symbol)
    return StrPrinter._print_Symbol(self, expr)
```

`self.symbols` is initialised at `python.py:21` and drained by `python()`
(`python.py:52-69`) into one `name = Symbol('name')` line per entry, **in list
order** — which is why `registered` appends at the END and dedups, and why the
model's registry is an ordered sequence rather than a set. This method is
*unchanged* by the patch; what the patch changes is whether a compound's name
operand ever reaches it. Nothing here consults `_settings`, which is why the
model's registry clauses are deliberately `wrap`-independent (a rival that makes
registration conditional on the setting is
`properties.py::registry-only-when-wrap`).

**Soundness (G-AX):** axiom_check.py builds a `PythonPrinter`, pre-seeds
`printer.symbols` from the model's `reg`, dispatches `printer._print(expr)`, and
asserts the resulting `symbols` list equals `[chr(c) for c in registered(reg, c)]`
— over all 26 keys × 7 pre-seeds (empty, disjoint, already-present at the head,
already-present at the tail, and both orders of a two-name seed, so the dedup and
the order clauses are both exercised). From an empty seed it additionally asserts
the public `python(expr)` preamble names equal the same list, so the check is
anchored at the surface the F2P test reads and not only at the private attribute.

### 3.4 `eq_text` / `limit_text` / `eq_registry` / `limit_registry` ↔ `_print_Relational` / `_print_Limit` (A-reference — THE CHANGED METHODS)
**Callees:** `StrPrinter._print_Relational` (`str.py:622`, charmap branch
636-637) and `StrPrinter._print_Limit` (`str.py:216`, **both** arms, 219 and
221-222), **after** the patch (each `%s`-of-operand replaced by
`self._print(operand)`):

```python
        if expr.rel_op in charmap:
            return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs),
                                   self._print(expr.rhs))
...
    def _print_Limit(self, expr):
        e, z, z0, dir = expr.args
        if str(dir) == "+":
            return "Limit(%s, %s, %s)" % tuple(map(self._print, (e, z, z0)))
        else:
            return "Limit(%s, %s, %s, dir='%s')" % tuple(map(self._print,
                                                            (e, z, z0, dir)))
```

`str(dir) == "+"` is the WHOLE condition on which the `dir` argument appears in
the output, and `dir` is `expr.args[3]` as `Limit.__new__` stored it
(`sympy/series/limits.py:126-146`) — see §1's `render_directed_limit` row. In the
four-slot arm the direction is delegated by the SAME `map(self._print, …)` as the
three operands, so it is a slot in exactly the same sense: its text is
`dir.name` (`str.py:699`) and it appends that name to `self.symbols`
(`python.py:38-42`).

The TEXT deep models encode that the fractional operand is rendered under the
*same* `wrap` as the compound while each name slot renders to its own
setting-independent character. The REGISTRY deep models encode that each name
slot — and only a name slot — takes one `registered` step, in left-to-right
source order (`self._print(expr.lhs)` before `self._print(expr.rhs)`;
`map(self._print, (e, z, z0))` — or `(e, z, z0, dir)` — in that tuple order, so
the direction step is last).

**Soundness (G-AX) — the load-bearing check.** axiom_check.py asserts, at the
public entry points:

* `eq_text(wrap, nl, rp, rq) == sstr(Eq(Symbol(chr(nl)), Rational(rp,rq)), sympy_integers=wrap)`
  and `limit_text(...) == sstr(Limit(Symbol(chr(ne)), Symbol(chr(nz)), Rational(z0p,z0q)), sympy_integers=wrap)`
  over the coprime non-integer boundary + thousands of fuzz inputs in both
  settings and over the name keys;
* `eq_registry(reg, nl)` / `limit_registry(reg, ne, nz)` == the real
  `PythonPrinter.symbols` after dispatching the same compound, from each of the 7
  pre-seeds, **and** == the `python()` preamble names when the seed is empty —
  including `ne == nz` and `ne != nz` limit pairs, which is what makes the second
  name slot separately observable;
* a fractional operand registers **nothing** (`render_operand`'s no-write
  clause);
* `PythonPrinter._print_Relational is StrPrinter._print_Relational` and the same
  for `_print_Limit`; `"sympy_integers" not in PythonPrinter._default_settings`
  and `PythonPrinter({"sympy_integers": True})` raises `TypeError`; a
  `PythonPrinter` has `symbols` and a `StrPrinter` does not — i.e. the receiver
  split §1.1 relies on is checked, not assumed;
* the EXACT F2P assertions:
  `sstr(Eq(x, S(2)/3), sympy_integers=True) == 'Eq(x, S(2)/3)'`,
  `sstr(Limit(x, x, S(7)/2), sympy_integers=True) == 'Limit(x, x, S(7)/2)'`,
  `sstr(x + S(1)/2, sympy_integers=True) == 'x + S(1)/2'`,
  `python(Eq(x, y)) == "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)"`, and
  `python(Limit(x, y, Rational(7, 2)))` == its three-line form.

A NAME operand is used in the relation because `Eq` of two numeric constants
auto-evaluates to a `BooleanFalse`/`BooleanTrue` (no template); axiom_check.py
asserts `rel.func is Eq` so the relation stays a genuine `Relational`, and
`str(lim.args[3]) == '+'` so the limit stays in the modeled branch. The text
assertions are at the FULL-STRING level and the registry assertions at the
FULL-LIST level — no double mask — so an operand render that dropped the setting
(`'2/3'` where `'S(2)/3'` is demanded) or a name slot that never reached the
receiver (registry unchanged where a new entry is demanded) fails them. **G-AX
executed RC=0 in-container under the gold patch** (recorded in meta.json).

All imports in axiom_check.py are either the standard library (`random`, `sys`,
`math.gcd`) or the repo's own public `sympy` API (`sstr`, `Eq`, `Limit`,
`Rational`, `Symbol`, `sympy.printing.python.python` / `PythonPrinter`,
`sympy.printing.str.StrPrinter`) — the same surface the gold patch and the F2P
tests exercise.

## G-CONF (differential conformance: model vs the REAL patched repo)

`conformance_check.py` refutes the refinement leg §1 asserts — that the model
agrees with the patched repository code, not merely with itself. It runs
in-container with `patch.diff` already applied.

**Shadow.** The `# impl-start` / `# impl-end` regions of `model.py`
(`render_equation`, `render_directed_limit`, `render_name`, `render_operand`,
`materialize`) copied VERBATIM with only the contract calls deleted (`Requires`,
`Ensures`, `Invariant`, `Assert`, `Acc`/`list_pred`, `ToSeq`, `MustTerminate` and
the `# invariants-start`/`-end` markers) — no restructuring, no renaming; the
model IS Python here, so there is no transliteration step to get wrong.
`materialize`'s element-at-a-time copy loop runs as written, and `render_name`'s
`if not (c in reg): reg.append(c)` mutates the real list. The `# pure-start` /
`# pure-end` `@Pure` helpers (`lit_*`, `render_rational`, `is_name`, `lit_name`,
`registered`, `eq_text`, `eq_registry`, `limit_text`, `limit_registry`) are copied
over the same way and diffed against the same oracle, so §3.2-§3.4's deep models
are re-refuted here as well as by G-AX. `PSeq` is realized by an immutable tuple
shim (`take`/`drop`/`+`/`len`/`[]`/`==`/`in`).

**`@ContractOnly` callees are CALLED, not assumed** (§3.1): `digits(n)` is the
real CPython `str(int)` (and its `len >= 1` Ensures is asserted on every call);
`coprime(p, q)` is the real `Rational` canonicalisation invariant —
`math.gcd(p, q) == 1` *and* `Rational(p, q).p == p and .q == q` (no reduction,
no collapse to `Integer`).

**Oracle — the REAL patched functions of §1, called (never transliterated), on
BOTH receivers of §1.1.** Each quantity is read twice — once through the public
instance dispatch and once by applying the patched method object directly — and
all readings must agree with the shadow and with each other, so neither a
dispatch-level nor a method-level mask can hide a divergence:

| model symbol | observable | repo oracle | readings |
|---|---|---|---|
| `render_equation` | text | `StrPrinter._print_Relational`, charmap arm (`str.py:622`, body 636-637) | `sstr(Eq(name, Rational(p,q)), sympy_integers=wrap)` + direct `printer._print_Relational(rel)` |
| `render_equation` | registry | the same method object on a `PythonPrinter` (`python.py:15`) whose `symbols` is pre-seeded from `reg` | `pp._print(rel)` then `pp.symbols` + `StrPrinter._print_Relational(pp2, rel)` then `pp2.symbols`; plus `python(rel)`'s preamble names when the seed is empty |
| `render_directed_limit` | text | `StrPrinter._print_Limit`, `str(dir) == "+"` arm (`str.py:216`, body 219) | `sstr(Limit(n1, n2, Rational(p,q)), sympy_integers=wrap)` + direct `printer._print_Limit(lim)` |
| `render_directed_limit` | registry | as above, on a `PythonPrinter` | `pp._print(lim)` / direct method application / `python(lim)` preamble |
| `render_name` | text + registry | `StrPrinter._print_Symbol` (`str.py:699`) and `PythonPrinter._print_Symbol` (`python.py:38-42`) via `Printer._print` | `sstr(Symbol(chr(c)), sympy_integers=wrap)` + `pp._print(sym)` then `pp.symbols` + `python(sym)` preamble |
| `render_operand` | text + no-write | `Printer._print` dispatch (`printer.py:238`) → `StrPrinter._print_Rational` (`str.py:574`), on the SAME printer instance | `sstr(...)` + `printer._print(r)` at top level + again at a pre-bumped `_print_level` (the nested frame a container's `self._print(sub)` really runs at; level-insensitivity is asserted, not assumed) + `pp.symbols` unchanged after `pp._print(r)` |

The receiver facts §1.1 depends on are asserted rather than assumed
(`check_receiver_facts()`): the shared `_print_Relational` / `_print_Limit`
method objects, `"sympy_integers" not in PythonPrinter._default_settings`,
`PythonPrinter({"sympy_integers": True})` raising `TypeError`, and the presence /
absence of `symbols` on the two receivers.

**Type bridge (§2, inverted).** `wrap: bool` → `_settings['sympy_integers']` on a
`StrPrinter`; `reg: List[int]` → `printer.symbols = [chr(c) for c in reg]` on a
`PythonPrinter`; the coprime pair `(p, q)` → `Rational(p, q)` (checked
non-collapsing); the name code point `c` → `Symbol(chr(c))`; the model's
`List[int]`/`PSeq[int]` code points → `str` via `"".join(chr(c) for c in out)`.
The diff is on the concrete `str` for text and on the concrete `list[str]` for
the registry, so a wrong code point, a missing entry, a duplicate entry or a
wrong order is a disagreement.

**Inputs — 100 324, every one satisfying the model's `Requires`
(`p >= 0 and q >= 2 and coprime(p, q)`, `is_name(...)` on each name slot).** 324
boundary cases: both `wrap` values × 7 registry pre-seeds (empty, disjoint,
already-present at head, already-present at tail, both orders of a two-name seed)
× the F2P shapes, all 26 name keys, equal *and* distinct limit name pairs, and 15
boundary fractions — the exact F2P operands `2/3` (Eq) and `7/2` (Limit), `1/2`,
small coprime fractions, and single- vs multi-digit numerators/denominators up to
11 digits so `materialize`'s loop runs both 1 and many iterations. Both `wrap`
values are enumerated, so **both arms of `render_operand`'s `if wrap:` are taken
by construction**, and both arms of `render_name`'s dedup guard are taken by
construction (the pre-seeds include the key and exclude it). Then 100 000 seeded
fuzz inputs over the same domain (magnitudes drawn log-uniformly to 10¹²,
filtered on the real `Rational`; names and pre-seeds drawn per input). `p == 0`
is never generated: `gcd(0, q) == q`, so it is outside `coprime` and
`Rational(0, q)` is an `Integer` — a different carrier (§2), not a narrowed spec.
Each input is checked through 15 shadow/pure quantities.

**Pinned seed: `SEED = 14531`** (module constant in `conformance_check.py`).

**Last recorded run: 100 324 inputs, 3 361 370 comparisons, 0 disagreements.**

**Capability (the check can fail).** Verified by three mutants: (a) running
against the UNPATCHED repo — `render_equation` / `render_directed_limit` /
`eq_text` / `limit_text` all disagree on the first `wrap=True` boundary input
(`'Eq(x, 2/3)'` vs the model's `'Eq(x, S(2)/3)'`) AND every registry reading
disagrees (the pre-patch `%s` never reaches the receiver, so `symbols` stays at
the seed); (b) forcing the shadow's `render_operand` down the non-wrapping arm —
`render_operand` disagrees (`'2/3'` vs `'S(2)/3'`) and the two compounds with it;
(c) dropping `render_name`'s `reg.append` — the text readings still agree
(confirming the text alone cannot see it) while `oracle_name_registry`,
`oracle_equation_registry` and `oracle_limit_registry` disagree. Exit 0 iff zero
disagreements; the final stdout line is a JSON report.
