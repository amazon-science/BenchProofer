# refinement.md — sympy__sympy-14976

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `mpfRational` `do` block and the deep `render`/`mpfName`/`mpfImport` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4);
the A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The render site — `MpmathPrinter._print_Rational` (`sympy/printing/pycode.py`)

Gold hunk (added method):
```python
def _print_Rational(self, e):
    return '{0}({1})/{0}({2})'.format(
        self._module_format('mpmath.mpf'),
        e.p,
        e.q,
        )
```

| # | Solution.lean impl op (`mpfRational`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `p : Int` | `e.p` (numerator of the `Rational` `e`) | R | Python `int` ↔ Lean `Int` (mapping.md §2). G-CONF bridges via `Rational(p,q).p ↔ p`. |
| A2 | parameter `q : Int` | `e.q` (denominator of the `Rational` `e`) | R | as A1 (mapping.md §2). |
| A3 | parameter `qualified : Bool` | `self._settings['fully_qualified_modules']` — the ambient state the callee on the next row reads | R | Python `bool` ↔ Lean `Bool` (mapping.md §2). The setting is not an argument of the real method but state on `self`; since the modeled operation only READS it and never writes it, carrying it as an extra parameter is a faithful refinement of "the value it has at the call" — and G-AX asserts the binding executably (default `True`; an explicit override takes). Both values are reachable in the real caller (mapping.md §3.2), which is why it is a parameter and not a pin. |
| A4 | `mpfName qualified` (the two-branch model `if qualified then "mpmath.mpf" else "mpf"`) | `self._module_format('mpmath.mpf')` — its RETURN VALUE | A-reference | the unchanged name-resolution callee is modeled **deeply** as a function of the setting it reads: it returns the dotted name verbatim when module-qualified spellings are asked for and its last component otherwise (`pycode.py:117-121`). G-AX validates `mpfName qualified == _module_format('mpmath.mpf')` against the real helper in BOTH configurations, and additionally that the two branches differ (so the branch is observable and the check is not vacuous). No consumed axiom. |
| A5 | `mpfImport` (`[("mpmath", "mpf")]`) returned as `out.2` | the same `self._module_format('mpmath.mpf')` call's SIDE EFFECT `self.module_imports['mpmath'].add('mpf')` (`pycode.py:115-116`) | A-reference | the callee's second observable, modeled as the recording **delta** with the law `post-state = pre-state ∪ delta` — exact because the underlying op is `set.add` (idempotent, pre-state independent). Validated by G-AX from 5 pre-states × 2 configurations plus an idempotence probe, and by G-CONF on 2 000 fuzzed pre-states. Modeled as an output component rather than a `mut` binder for the reason in mapping.md §2 (a list post-state would impose an order the real callee does not have). |
| A6 | `toString p`, `toString q` | the `{1}` / `{2}` positional substitutions of `e.p`/`e.q` (Python `str(int)`) | I | identical concrete op: canonical signed base-10 integer rendering, equal on both sides for every integer (mapping.md §2). |
| A7 | `m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"` with `m = mpfName qualified` | the `'{0}({1})/{0}({2})'.format(m, e.p, e.q)` template expansion | I | the format template with `{0}` reused twice ↔ the two `mpfName qualified` occurrences joined by `(`, `)/`, `(`, `)`; `str` `.format` ↔ `String ++`. The reuse of `{0}` is why the SAME resolved spelling appears in both positions on both sides. |
| A8 | `out.1` returned (`String`) | the `return` of the formatted string | R | Python `str` ↔ Lean `String` content identity (mapping.md §2). |

Discriminating content of the change — the numerator and denominator are EACH
wrapped in the backend float constructor, instead of emitted as a bare integer
ratio `p/q` — lives in `render qualified p q` requiring the two
`mpfName qualified ++ "(" ++ … ++ ")"` factors (model) ⇔ the
`'{0}({1})/{0}({2})'` template (real). The pre-patch path was the inherited
`StrPrinter._print_Rational` returning the bare `"%s/%s" % (e.p, e.q)`, and
`str(e.p)` alone when `e.q == 1`; `Solution_prepatch.lean` reproduces that bare
quotient (including the `q = 1` special case, measured at base_commit) and
records NO import, and it **fails** both clauses (G-DIFF) — the unsolved goals
`(if q = 1 then toString p else toString p ++ "/" ++ toString q) = render qualified p q`
and `[] = mpfImport`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — adding the
constructor wrapping around each part of the quotient — is modeled **deeply** (the
spelled-out `render` concatenation, steps A6/A7, I), not hidden behind an axiom
about the function under change: there is no consumed `printRational` axiom. The
two kind-A rows, `mpfName` (A4) and `mpfImport` (A5), are the two observables of
one **unchanged** callee (`_module_format`), both validated by G-AX as
A-references.

## C. verify(Solution) ⇒ resolved

`mpfRational` verifies only if BOTH clauses hold **at every input**, i.e. for
every `qualified`, `p`, `q`:

1. `out.1 = render qualified p q` — the quotient with BOTH parts wrapped in the
   spelling the ambient configuration resolves the constructor's dotted name to
   (A4/A7), the same spelling in both positions, and the integers rendered
   canonically (A6); and
2. `out.2 = mpfImport` — the call records the import the resolved spelling needs
   (A5), in both configurations.

By R (`int ↔ Int`, `bool ↔ Bool`, `str` content identity, `defaultdict(set)` ↔
the set of `(module, name)` pairs) the verified renderer equals
`'{0}({1})/{0}({2})'.format(self._module_format('mpmath.mpf'), e.p, e.q)`
together with that call's recording, on every `Rational` **and in either
configuration of `fully_qualified_modules`**; by G-AX the deep models `mpfName`
and `mpfImport` equal the real `_module_format('mpmath.mpf')`'s value and effect
in both configurations (A-references); by G-CONF the R/I transliteration agrees
with `patch.diff`'s behaviour on 200 030 fuzzed value observations across both
configurations and 2 000 recording observations from fuzzed pre-states, with
three liveness probes confirming the differential would SEE a defective model.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee, on the whole modeled
domain — and the gold patch resolves (G-RESOLVE: the F2P `test_MpmathPrinter`
asserts `p.doprint(Rational(1,2)) == 'mpmath.mpf(1)/mpmath.mpf(2)'`). Trust
points are exactly the two of plan §1.1: axiom soundness (G-AX, the two
A-reference observables) and refinement fidelity (this doc, G-EQ + G-CONF).

### C.1 Scope of the claim, and what a previous revision got wrong

The claim above is stated over BOTH configurations on purpose. A previous
revision of this document made the same universal claim ("is the gold patch up to
type refinement and the one audited callee … on every `Rational`") while the model
it described pinned the resolver to the single constant `"mpmath.mpf"` and modeled
no recording at all. That claim was **false**, and a G-PANEL-2 faithfulness review
refuted it by execution against the patched repo:

* the model's post-image demanded `'mpmath.mpf(1)/mpmath.mpf(2)'` where the real
  patched callee returns `'mpf(1)/mpf(2)'` — namely under
  `MpmathPrinter({'fully_qualified_modules': False})`, the printer that
  `sympy/utilities/lambdify.py:416` hardcodes, which is the very path the reported
  issue concerns. So the spec was STRONGER than the real callee on a reachable
  input: an implementation faithful to the repo would have been REJECTED.
* the model was silent about the import the same call records, so it was WEAKER
  than the real callee on the effect: an implementation that emitted the bare
  spelling and recorded nothing — leaving generated code with an unbound name —
  would have been ACCEPTED.

The repair carries the configuration as the `qualified` parameter with the
two-branch deep model (A3/A4) and the recording as the `mpfImport` delta (A5),
rather than narrowing the domain to the qualified configuration. Narrowing was
rejected because the real caller demonstrably reaches the other branch
(mapping.md §3.2), so a `require qualified = true` would have excluded a live
input and the unreachability could not be proved. Nothing in the spec got weaker
as a result: the rendering clause now pins the exact spelling **in each branch**
(strictly more than the old unconditional constant, which pinned one branch and
asserted it everywhere), and the effect clause is entirely new. G-PBT records the
falsification side of that statement: the old model's own rendering
(`weak-config-blind-qualified`, an impl that emits the qualified spelling
regardless of the configuration) and the old model's own effect
(`weak-import-dropped`, an impl that records nothing) are both now REJECTED, each
by a kernel-checked witness that fails against the frozen solution — alongside
`weak-config-blind-bare`, `weak-config-inverted`,
`weak-import-only-when-qualified` and `weak-import-transposed`, and with
`pos-branch-split` / `pos-import-spelled-out` confirming the two new clauses are
satisfiable without naming the model's own helpers.
