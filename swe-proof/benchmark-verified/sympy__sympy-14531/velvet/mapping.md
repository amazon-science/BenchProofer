# mapping.md — sympy__sympy-14531

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 205da797006360fc629110937e39a19c9561313e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `sympy/printing/str.py` (the `StrPrinter`). Repo file
that CONSUMES the modeled effect: `sympy/printing/python.py` (the
`PythonPrinter` subclass and the `python()` caller).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `printTaggedPair (cfg) (tag) (a) (b) (mut reg)` | `StrPrinter._print_Relational` — `sympy/printing/str.py:619` (the `charmap` arm, line 633) | modeled changed function: serialize a binary head `tag(lhs, rhs)` |
| `printLimit (cfg) (e) (z) (z0) (mut reg)` | `StrPrinter._print_Limit` — `sympy/printing/str.py:216` (the `str(dir) == "+"` arm, line 219) | modeled changed function: serialize `Limit(e, z, z0)` |
| `renderSub` *(opaque — A-reference)* | `self._print(sub)`: `sympy.printing.printer.Printer._print`, the configuration- AND state-aware sub-dispatch the patch routes each sub-object through | unchanged callee: ONE rendering step of the ACTIVE serializer — the text `sub` renders to under the active settings AND the declaration registry the serializer carries afterwards |
| `renderText` / `renderReg` (pure) | the two halves of ONE `self._print(sub)` call: its return value, and the serializer's `symbols`/`functions` state after it | projections `.1` / `.2` of a single step |
| `taggedPair`, `limitTriple` (pure) | the assembled return string of the post-patch arms | pure spec: the composite's serialized text |
| `taggedPairReg`, `limitTripleReg` (pure) | the serializer's declaration registry after the arm has rendered all its sub-objects | pure spec: the composite's registry EFFECT — the left-to-right fold of its steps |
| `cfg : Bool` | the relevant `StrPrinter._settings` entry (e.g. `sympy_integers`) that controls a sub-object's surface form | the printer configuration that must propagate to sub-objects |
| `reg : List Char` (a `mut` parameter) | the active serializer's DECLARATION REGISTRY — `PythonPrinter.symbols` / `.functions` (`sympy/printing/python.py:21-22`), read back as the preamble `python()` emits (`python.py:58-82`) | the accumulated declaration text the caller emits AHEAD of the composite; every step extends it |

The pre-patch repo behavior the change removes (refinement audit only, not in
the consumer spec view): the arms interpolated each sub-object via `'%s' % sub`,
i.e. Python `str(sub)` — which constructs a FRESH default `StrPrinter()` with
default settings AND an empty declaration registry, discarding the active
printer's `self._settings` and leaving the active printer's registry untouched.
The patch replaces every such `%s`/`str(sub)` of a SymPy sub-object with
`self._print(sub)`, which does BOTH of the things the throwaway printer did not:
the active settings reach the sub-object, and the active printer is the one whose
registry advances. Both halves are graded by the instance's F2P tests, one each:

* `test_Rational` (`sympy/printing/tests/test_str.py`) grades the SETTINGS half —
  `sstr(Eq(x, Rational(2, 3)), sympy_integers=True) == "Eq(x, S(2)/3)"` and
  `sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) == "Limit(x, x, S(7)/2)"`.
* `test_python_relational` (`sympy/printing/tests/test_python.py`) grades the
  REGISTRY half — `python(Eq(x, y)) == "x = Symbol('x')\ny = Symbol('y')\ne =
  Eq(x, y)"` (the base_commit expectation on that line is the bare
  `"e = Eq(x, y)"`, with no declarations at all). Note the two declarations are
  pinned in ARGUMENT ORDER, so this test grades the ORDER of the steps as well as
  the fact that they happen on the active serializer.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the serializer's output `str` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; ASCII output is per-code-point exact |
| a SymPy sub-object (`expr.lhs`, `expr.rhs`, `e`, `z`, `z0`) | `SubObj` (opaque, `id : Nat`) | an opaque handle; its only observables are the text it renders to and the registry entry its step leaves (`renderSub`). Distinct sub-objects ↔ distinct `id`. |
| the active printer configuration (`self._settings`, e.g. `sympy_integers`) | `cfg : Bool` | a boolean selecting which of two surface forms a step produces. `cfg = false` ↔ the DEFAULT settings a fresh `StrPrinter()` carries; `cfg = true` ↔ a non-default setting that changes a sub-object's rendering. |
| the active serializer's declaration state — the pair of lists (`printer.symbols`, `printer.functions`) | `reg : List Char` | the DECLARATION TEXT that state emits: `"<s> = Symbol('<s>')\n"` per symbol in `symbols` order, then `"<f> = Function('<f>')\n"` per function (`python.py:58-82`). This text determines the pair of lists uniquely (the two line forms are distinct, and G-AX asserts the injectivity over its fuzz corpus), so one `List Char` loses nothing. `[]` ↔ a fresh serializer's empty registry. |
| ONE `self._print(sub)` call on the active serializer | `renderSub cfg reg sub : List Char × List Char` | `.1` = the call's return value (the text); `.2` = the declaration registry afterwards. BOTH halves come from the SAME call and cannot be obtained apart — which is what makes the step order and the serializer's identity observable. |
| `str(sub)` / `'%s' % sub` (settings-blind, state-less) | `renderSub false [] sub`, with the active `reg` left unchanged | render `sub` on a THROWAWAY serializer: default configuration, empty registry, and no effect on the active serializer (the pre-patch defect, exactly) |
| ONE `self._print(sub)` on a PROBE — a copy of the active printer carrying its settings and a copy of its registry, discarded afterwards | an application `renderSub cfg reg sub` whose `.2` is NOT written back to `reg` | an OBSERVATION of the step the active serializer would take, with no effect on the active serializer. Same text as the live call (G-AX check 10), no registry advance. This is the general form of the row above (`renderSub false []` is the probe primed to the default configuration and the empty registry) |
| the head token (`charmap[rel_op]` such as `"Eq"`/`"Ne"`; the literal `"Limit"`) | `tag : List Char` / the literal `"Limit("` | constant string content, ASCII-exact |

Lean `String`/`List Char` is total and sound; the carrier is `List Char`
because both the output and the declaration registry are assembled by string
concatenation.

### 2.1 TWO REALIZABLE SLICES of the modeled domain

The model's step takes `cfg` and `reg` together, but the real system cannot
present both at once, and this is asserted rather than assumed (axiom_check.py
check 0):

* the declaration registry exists only on `PythonPrinter`, and
  `PythonPrinter._default_settings` is `{'order': None}` — it REJECTS
  `sympy_integers` with `TypeError: Unknown setting`;
* `StrPrinter` accepts `sympy_integers` but has no `symbols`/`functions` at all.

So the `cfg` leg is realizable only on the StrPrinter slice (registry always
empty) and the `reg` leg only on the PythonPrinter slice (configuration at its
default). Both slices are validated separately by G-AX and diffed separately by
G-CONF. Modeling them as ONE step with both parameters is a sound
over-approximation: `renderSub` is `opaque` and asserts NOTHING about either
component, so every real behaviour on either slice is an instance of it. It is
also the right model of the code, because `_print_Relational` /`_print_Limit`
are single methods inherited by both printers — the arm the patch changes is the
same code on both slices, and it is the arm that must forward `self` in both
respects.

### 2.2 MATERIALIZATION RULE — how a model impl is turned back into code

The table above translates VALUES. This subsection translates OPERATIONS, in the
direction an auditor needs: given an impl region, what is the arm it refines to.
It is stated because the model's step is a FUNCTION returning a pair while the
repo's step is a method call, and a function application is not by itself a call
on the active printer — the write-back is what makes it one.

For each `renderSub cfg reg s` application in an impl region:

1. **`.2` written back** (`reg := r.2`, or the value flows into the `reg` a later
   written-back step reads) → **a live `self._print(s)` on the active printer**.
   The registry advance IS the write-back; the text is `r.1`.
2. **`.2` never written back** (nothing downstream of it ever reaches `reg`) →
   **`self._print(s)` on a PROBE**: a copy of the active printer carrying
   `self._settings` and a copy of `self`'s registry, used and discarded
   (`_probe = self.__class__.__new__(self.__class__); _probe.__dict__.update(
   self.__dict__); _probe._settings = dict(self._settings); _probe.symbols =
   list(self.symbols); ...; _probe._print(s)`). No effect on `self`.
3. `renderSub false [] s` with the active `reg` untouched → the special case of
   (2) at the default configuration and the empty registry, i.e. `str(s)` /
   `'%s' % s`: the pre-patch defect.

Rule (2) is FORCED, not chosen: the model's post-state for `reg` is the value the
impl assigns, so an application whose result is discarded asserts that the
composite's own serializer did not advance. Materializing it as a live
`self._print` on `self` would materialize an effect the impl does not have, and
would make the map non-monotone — two impls with the same denotation refined into
two arms with different behaviour. It is sound because a primed probe returns the
step's text EXACTLY as the live call would and leaves the live registry untouched:
asserted against the real callee over the fuzz corpus by axiom_check.py check 10
(G-AX), and end-to-end for the composite arm by conformance_check.py's probe
slice (G-CONF), which materializes an extra uncommitted observation and checks the
emitted `python()` program is byte-identical to gold's.

The rule has a consequence worth stating plainly, because it is the boundary of
what this spec can pin: an extra step whose result is discarded is invisible to
the two `ensures` clauses AND invisible in the materialized behaviour, so it is
not a spec weakness — refinement.md §F proves the two impls are the same program
and measures the materialization resolved=True through the official harness. An
extra step whose result IS written back changes `reg` and is rejected
(`properties.py weak-tagged-dup-step`); reusing an uncommitted observation's TEXT
in an output slot changes `out` and is rejected
(`properties.py weak-tagged-reuse-probe-text`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `renderSub` ↔ one `self._print` step (A-reference, opaque)
**Callee:** `sympy.printing.printer.Printer._print(self, expr)` as seen through
the serializer that is printing the composite. It dispatches `expr` to the right
`_print_X`, is governed by the printer's `self._settings`, and — on the
`PythonPrinter` subclass, whose `_print_Symbol` / `_print_Function`
(`python.py:31-42`) append to `self.symbols` / `self.functions` — EXTENDS the
printer's declaration registry as a side effect. The operation under spec does
NOT change how a single sub-object renders; it changes only WHICH serializer
renders it: the buggy code used `str(sub)` (a fresh default-settings printer with
an empty registry), the fix uses `self._print(sub)` (the active printer, with its
settings and its registry). So `renderSub` is modeled **opaquely** (an `opaque`,
no value pinned, no `axiom` declared and none consumed); the proof borrows no
soundness from it. It is an **A-reference**: validated by G-AX to behave as a
deterministic per-object rendering step whose text depends on the configuration
and whose effect is an ordered extension of the registry.

Two facts the spec relies on, both purely structural:

1. **The configuration is observable.** `self._print(sub)` under the active
   settings can DIFFER from `str(sub)` (default settings) for the same `sub`.
   Witness used by the F2P tests: with `sympy_integers=True` the rational
   `Rational(2, 3)` renders as `S(2)/3` under the active printer
   (`renderSub true`) but as `2/3` under a fresh default printer
   (`renderSub false`); likewise `S(7)/2` vs `7/2`.
2. **The effect, and its ORDER, are observable.** A step appends the sub-object's
   declaration to the active printer's registry, the caller emits that registry
   ahead of the composite, and the registry is APPEND-ORDERED — so stepping `b`
   before `a` emits the two declarations in the other order, and stepping either
   one on a throwaway printer omits it entirely. Witness:
   `python(Eq(x, y))` must be `"x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)"`.

One fact the spec deliberately does NOT rely on: the real registry
**deduplicates** (`if symbol not in self.symbols`, `python.py:40-41`), so
re-registering an already registered sub-object is a no-op. The model assumes
nothing of the kind — an opaque step is a function of its incoming registry and
nothing more — so the model is strictly WEAKER than the real callee here, which
is the sound direction. (This is the measured reason a duplicated-step rival's
faithful counterpart still resolves; see refinement.md and properties.py
`weak-tagged-dup-step`.)

**Soundness check (G-AX):** `axiom_check.py` runs the real callee at
base_commit, unpatched, and asserts: (0) the two-slice claim above, including
that `PythonPrinter` really does reject `sympy_integers`; (1) one step is a
FUNCTION of `(cfg, reg, sub)` — independently primed printers carrying the same
registry produce the same (text, next-registry) pair — on both slices; (2)
HISTORY COLLAPSE, i.e. the result depends on the registry's value and not on the
sequence that produced it, which is what licenses a value carrier; (3) the
declaration text is INJECTIVE on the real `(symbols, functions)` state, so the
`List Char` carrier loses nothing; (4) the registry effect is observable and
reaches the caller's output; (5) the step ORDER is observable in that output;
(6) the real dedup fact holds (recorded, not assumed); (7) a throwaway
serializer starts empty and leaves the live registry untouched; (8)
COMPOSITIONALITY — for both arms, the (text, registry) produced by taking the
steps in sequence on ONE printer equals the chained composition of single steps,
i.e. `taggedPair`/`taggedPairReg` and `limitTriple`/`limitTripleReg` are exactly
the real arms' fold, including that `tuple(map(self._print, (e, z, z0)))` is
forced left to right; (9) the configuration is observable with the F2P
witnesses; (10) the MATERIALIZATION RULE of §2.2 — a probe primed to the active
printer's settings and registry returns the step's text EXACTLY as the live
`self._print` call would, and leaves the active printer's `(symbols, functions)`
untouched, so an uncommitted observation refines to real, effect-free code.
Imports only `sympy`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14531`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the `pure` region of `Solution.lean` — the assembly AND the registry fold — to
Python, and leaves `renderSub`'s callee as the REAL `self._print` (the A-tagged
callee → run the real callee, not a stand-in), observed as a SINGLE step on a
printer primed to the incoming registry, so the shadow is genuinely the model's
chained fold rather than a second spelling of the oracle's own loop. It diffs the
shadow against the gold patch's actual `_print_Relational` / `_print_Limit` on
fuzzed relational/limit expressions, over three slices (§2.1):

* **text slice** — `StrPrinter` under both default and non-default settings:
  the assembled string;
* **effect slice** — `PythonPrinter` primed to a fuzzed non-empty registry: the
  assembled string, the resulting `(symbols, functions)` state, AND the
  declaration preamble that state emits;
* **caller slice** — end to end through `python(expr)` on a sampled subset: the
  whole emitted program (preamble in fold order, then `e = <expr>`) must equal
  what the shadow predicts, which is the observable the F2P test reads.
* **probe slice** (§2.2) — the materialization rule for an UNCOMMITTED
  observation: an arm that takes an extra step on a primed probe before the two
  live steps must produce the SAME text, the SAME `(symbols, functions)` state,
  the SAME declaration preamble and the SAME end-to-end `python()` program as the
  gold arm. This is the executable half of refinement.md §F.
