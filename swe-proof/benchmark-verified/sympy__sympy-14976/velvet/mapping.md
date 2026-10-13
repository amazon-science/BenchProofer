# mapping.md — sympy__sympy-14976

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9cbea134220b0b951587e11b63e2c832c7246cbc`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `sympy/printing/pycode.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `mpfRational (qualified : Bool) (p : Int) (q : Int)` | `MpmathPrinter._print_Rational(self, e)` — `sympy/printing/pycode.py` (added post-patch after `_print_Float`, body at line 333; class `MpmathPrinter` opens at `pycode.py:314`) | the modeled changed function (renderer for a rational in the mpmath backend) |
| `qualified : Bool` | `self._settings['fully_qualified_modules']` — the printer's own setting, default declared at `pycode.py:95` and overridden by callers (see §3.2) | the ambient name-spelling configuration the renderer's only callee reads; a model *parameter*, not a modeled function |
| `mpfName (qualified : Bool)` *(deep model — A-reference)* | `self._module_format('mpmath.mpf')` — `AbstractPythonCodePrinter._module_format`, `sympy/printing/pycode.py:113` | the (unchanged) helper that resolves the backend float constructor's dotted name to its emitted spelling; deep-modeled as a **two-branch function of the setting**, validated `mpfName qualified == _module_format('mpmath.mpf')` in BOTH branches by axiom_check.py (G-AX), NOT consumed as an axiom |
| `mpfImport` *(deep model — A-reference)* | the mutation `self.module_imports['mpmath'].add('mpf')` performed by that same `_module_format` call (`pycode.py:115-116`) | the import the resolver RECORDS while resolving that dotted name, as a delta; validated `==` the real delta in both branches by axiom_check.py (G-AX) |
| `render (qualified : Bool) (p q : Int)` | the `'{0}({1})/{0}({2})'.format(...)` body of the added `_print_Rational` | pure spec: the rendered text for a rational, under the resolved spelling |
| `out.1` / `out.2` | the method's return value / the printer's `module_imports` delta | the two observable components of one call (§2) |

Pre-patch symbol the change shadows (refinement audit only, not in the consumer
spec view): the inherited `StrPrinter._print_Rational` (`sympy/printing/str.py:594`),
which under the printer's default settings (`sympy_integers=False`) returns the
bare `"%s/%s" % (expr.p, expr.q)` — and plain `str(expr.p)` when `expr.q == 1`
(measured at base_commit). `MpmathPrinter` had no own `_print_Rational` at
base_commit, so a `Rational` printed as the bare quotient `p/q`, and no import
was recorded for it.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self._settings['fully_qualified_modules']` — a Python `bool` read by the resolver | `qualified : Bool` | Python `bool` ↔ Lean `Bool`, identity on the two values. G-AX asserts the binding executably: the printer's default is `True` and an explicit `settings={'fully_qualified_modules': v}` override takes the value `v`, so `MpmathPrinter()` ↔ `qualified = true` and the printer `lambdify` builds ↔ `qualified = false` (§3.2). |
| `e.p` — the signed integer numerator of a sympy `Rational` (a Python `int`) | `p : Int` | Python `int` ↔ Lean `Int`; arbitrary precision both sides; `str(e.p)` ↔ `toString p` (canonical signed decimal, no leading `+`, `-` for negatives) |
| `e.q` — the positive integer denominator of a sympy `Rational` (`q ≥ 1`) | `q : Int` | as above. In a canonical sympy `Rational`, `q ≥ 1` and `gcd(p,q)=1`; the renderer is total in `(p,q)` and never inspects these invariants, so the model leaves `q` an unconstrained `Int` (the post-condition is the same string-concatenation either way). |
| the rendered code fragment (Python `str` returned by `_print_Rational`) | `out.1 : String` | Python `str` ↔ Lean `String`; `'...'.format(a,b)` ↔ `String` `++` concatenation; the format template `'{0}({1})/{0}({2})'` ↔ `m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"` with `m = mpfName qualified` |
| the imports the call RECORDS — the pairs added to `self.module_imports`, a `defaultdict(str -> set[str])` | `out.2 : List (String × String)` | the Python mapping is flattened to the **set** of `(module, name)` pairs (`{(mod, nm) for mod, names in module_imports.items() for nm in names}`); the Lean list abstracts that set, so it is read **order-insensitively and duplicate-free** by both G-AX and G-CONF (`flat_imports`). The modeled value is the **delta** of one call, not the post-state (§3.1). |

`toString (p : Int)` and Python `str(int)` agree on every integer: both emit the
canonical base-10 representation, with a leading `-` exactly for negatives and no
leading `+` or zero-padding. (The `.format` positional substitution stringifies
`e.p`/`e.q` via `str`.) G-CONF exercises this over fuzzed magnitudes incl.
negatives and large values, in both configurations.

**Why the recorded import is an output component and not a `mut` binder.** The
real effect is a *set insertion* into a `defaultdict(set)`. A `mut` binder
carrying the post-state as a `List (String × String)` would have to pin an ORDER
and a POSITION that the real callee simply does not have, so it would reject a
correct implementation that recorded the same pair elsewhere in the list —
SPEC-TOO-STRONG on an artefact of the carrier. Modeling the **delta** as a
returned component, together with the law in §3.1, states exactly what the real
call guarantees and nothing more: the delta is a one-element list, so there is no
order or multiplicity freedom left to over-fit. The cost is that the model does
not carry the pre-state; the law is what recovers the post-state, and G-AX and
G-CONF both check it from *fuzzed non-empty pre-states* rather than only from a
fresh printer.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `mpfName` / `mpfImport` ↔ `_module_format('mpmath.mpf')` (A-reference)
**Callee:** `AbstractPythonCodePrinter._module_format(self, fqn, register=True)`
(`sympy/printing/pycode.py:113`). It records the import and returns the spelling
to emit for a dotted name. Source at base_commit:

```python
def _module_format(self, fqn, register=True):
    parts = fqn.split('.')
    if register and len(parts) > 1:
        self.module_imports['.'.join(parts[:-1])].add(parts[-1])
    if self._settings['fully_qualified_modules']:
        return fqn
    else:
        return fqn.split('(')[0].split('[')[0].split('.')[-1]
```

The changed function reads `self._module_format('mpmath.mpf')`. This is the
operation's only callee, and it is UNCHANGED by the patch — hence an
A-reference, modeled deeply, not a function under spec. It has **two observable
effects**, and the model carries both:

**(value)** the returned spelling is settings-dependent, so the deep model is a
function of the setting rather than a constant:

- `fully_qualified_modules=True` (the documented **default**, `pycode.py:95`):
  returns `'mpmath.mpf'` verbatim ⇔ `mpfName true`.
- `fully_qualified_modules=False`: returns the last dotted component `'mpf'`
  ⇔ `mpfName false`.

G-AX runs the real `_module_format('mpmath.mpf')` under BOTH configurations and
asserts equality with `mpfName qualified` in each; both are hard obligations,
neither is merely "recorded". It additionally asserts that the two branches
really do differ (else the model's `Bool` branch would be unobservable and the
check vacuous) and that a default-settings printer resolves exactly as the
`true` branch.

**(effect)** the same call inserts `(module, name)` into `self.module_imports`
before it consults the setting — `parts = 'mpmath.mpf'.split('.')` gives
`['mpmath', 'mpf']`, and `len(parts) > 1`, so with `register=True` (the default,
and what the changed function uses) `self.module_imports['mpmath'].add('mpf')`
runs in BOTH configurations. Modeled as the delta
`mpfImport = [("mpmath", "mpf")]` with the law

> **post-state = pre-state ∪ delta** (as sets of `(module, name)` pairs)

which is exact because the underlying operation is `set.add`: it is idempotent
and independent of what is already recorded. G-AX checks the law by execution
from 5 pre-states × 2 configurations (fresh, unrelated entries present, the delta
already present, same module other name, mixed) and checks idempotence by
resolving twice; it also asserts the delta is non-empty, so the effect clause
cannot be satisfied by a model that records nothing. G-CONF re-checks the law on
2 000 fresh printers with randomly pre-populated pre-states.

### 3.2 Configuration dependence — REACHABILITY OF BOTH BRANCHES
The resolver's value branch is chosen by `fully_qualified_modules`, and **both
branches are reachable in the real caller**, so the model must be a function of
the setting rather than a pin of one branch:

- `qualified = true` — `MpmathPrinter()` with no override. This is what the F2P
  unit test constructs (`test_MpmathPrinter`: `doprint(Rational(1,2)) ==
  'mpmath.mpf(1)/mpmath.mpf(2)'`).
- `qualified = false` — `sympy/utilities/lambdify.py:416` constructs the printer
  as `Printer({'fully_qualified_modules': False, 'inline': True,
  'user_functions': user_functions})`. Measured on the patched worktree:
  `MpmathPrinter({'fully_qualified_modules': False})._print_Rational(Rational(1,2))`
  returns `'mpf(1)/mpf(2)'`. That is the path the reported issue is actually
  about (`nsolve`/`lambdify` over the mpmath backend at high precision), and
  `lambdify` turns the printer's recorded `module_imports` into the emitted
  module's `from mpmath import mpf` line — which is what makes the bare spelling
  resolvable there, and what makes the recorded import load-bearing rather than
  incidental.

**Corrected record.** A previous revision of this document stated that the
`fully_qualified_modules=False` branch was "a different but equally-correct
rendering … out of scope of the F2P test and recorded here for completeness, NOT
a soundness gap", and the model accordingly pinned `mpfName := "mpmath.mpf"`. That
claim was **false in both halves**, and a G-PANEL-2 faithfulness review refuted it
against the real repo:

1. the branch is not out of scope — the caller in `lambdify` hardcodes it, so the
   model's post-image asserted a value the real callee does not return there
   (`'mpmath.mpf(1)/mpmath.mpf(2)'` where the real one returns `'mpf(1)/mpf(2)'`),
   making the spec STRONGER than the real callee on a reachable input; and
2. it was not the only divergence — the pure-constant model dropped the
   resolver's recording effect entirely, making the spec WEAKER than the real
   callee on the import.

Both are now modeled (§3.1) instead of argued away, both are checked in both
configurations by G-AX, and both are observed independently on the two sides of
the G-CONF differential (§4). No setting other than `fully_qualified_modules`
affects this operation: measured on the patched worktree, no other
`MpmathPrinter` setting changes the rendered value (`sympy_integers` and
`standard` are not even accepted settings for this printer), and the renderer
reads no other state.

## 4. G-CONF fuzz seed and axes (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14976`** so the
consumer-side verdict is reproducible. It transliterates the R/I-tagged ops of
the impl region to Python over the real repo types via §2 — including the
A-reference deep models **as the model writes them** (`shadow_mpf_name` is the
two-branch function, `SHADOW_MPF_IMPORT` the delta) — and diffs the shadow
against the patched real `MpmathPrinter._print_Rational`. Axes:

- **value leg** — 15 boundary pairs (the F2P `1/2`, the `test_nsolve_rational`
  `1/3`, the problem statement's `232/3`, zero and unit numerators, both signs,
  non-canonical inputs, and `10**50`-scale magnitudes) plus 100 000 fuzzed
  `(a, b)` pairs, each observed under **both** configurations of the modeled
  `Bool` binder: 200 030 observations.
- **effect leg** — 2 000 fresh printers with a fuzzed configuration and a fuzzed
  non-empty pre-state, asserting the §3.1 law `after == before | delta`.
- **liveness** — three probes substitute deliberately DEFECTIVE models on the
  shadow side (the flag-blind `'mpmath.mpf'` — the previous revision's own model
  —, the bare-pinned `'mpf'`, and an empty import delta) and REQUIRE the
  differential to disagree with the real repo in each case. If any probe finds no
  disagreement the script reports `G-CONF FAIL: … this differential is blind`
  rather than conformance. This exists because the previous revision hardcoded
  the constructor spelling on BOTH sides, so the shadow and the model shared one
  error and agreed by construction: the gate passed a divergence a human review
  then found. The probes make that failure mode mechanical.
