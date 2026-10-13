# mapping.md — astropy__astropy-7606

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3cedd79e6c121910220f8e6df77c54a0b344ea94`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the one unchanged callee modeled as a free input.

Repo file under change: `astropy/units/core.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compareName (selfName : List Char) (outcome : InterpretOutcome)` | `UnrecognizedUnit.__eq__(self, other)` — `astropy/units/core.py:1710` | the modeled changed function (equality of an unrecognized unit against an arbitrary operand) |
| `selfName : List Char` | `self.name` — the name string of the `UnrecognizedUnit` receiver (set in `astropy/units/core.py`’s `UnrecognizedUnit.__init__`/`IrreducibleUnit`) | the receiver’s identifying name |
| `outcome : InterpretOutcome` *(free input — no contract)* | the result of `Unit(other, parse_strict='silent')` — `_UnitMetaClass.__call__`, `astropy/units/core.py:1789` | the UNCHANGED operand-interpretation callee, abstracted to its three observable outcomes |
| `compareSpec` *(deep model)* | the post-patch body of `UnrecognizedUnit.__eq__` (the try/except + `isinstance(other, type(self)) and self.name == other.name`) | pure spec: how each interpretation outcome becomes a verdict |

### 1.1 Additional change site (refinement.md §B; no separate prepatch)
`UnitBase.__eq__` — `astropy/units/core.py:728` — also changes in the gold
patch: its `except (...)` branch returns `NotImplemented` instead of `False`.
This is **behaviourally inert for the official harness**: a binary `==`/`!=`
whose `__eq__` returns `NotImplemented` falls back to the reflected comparison
and finally to identity, yielding the *same* `False`/`True` the old `return
False` produced for every operand the test suite exercises (no F2P/P2P test
distinguishes them — see refinement.md §B). It carries no separately-observable
fixed behaviour, so it gets no `Solution_prepatch_<k>.lean`; it is recorded here
and audited by G-CONF only through the shared `deferred ↔ NotImplemented`
abstraction.

The pre-patch bug the F2P test observes lives entirely at site `UnrecognizedUnit.__eq__`:
`other = Unit(other, parse_strict='silent')` is called with **no** `try/except`,
so an operand the interpreter rejects with `TypeError` (e.g. `None`) raises
out of `__eq__` instead of yielding a verdict. `Solution_prepatch.lean`
reproduces exactly that escape and fails (G-DIFF).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.name` (a Python `str`) | `selfName : List Char` | `s` (Python str) ↔ `s` as a `List Char`; equality `self.name == other.name` ↔ `decide (selfName = name)` (both are exact code-point string equality) |
| `Unit(other, parse_strict='silent')` raising `(ValueError, UnitsError, TypeError)` | `InterpretOutcome.uninterpretable` | the interpretation attempt fails ⇒ `uninterpretable` |
| interpretation succeeding to an `UnrecognizedUnit` named `name` | `InterpretOutcome.sameKind name` | `isinstance(interp, UnrecognizedUnit)` with `interp.name = name` ⇒ `sameKind name` |
| interpretation succeeding to a non-`UnrecognizedUnit` `UnitBase` (or any object that is not an `UnrecognizedUnit`) | `InterpretOutcome.otherKind` | `not isinstance(interp, UnrecognizedUnit)` ⇒ `otherKind` |
| the Python value `NotImplemented` returned by `__eq__` | `Verdict.deferred` | `NotImplemented` (decline → reflected/identity fallback) ↔ `deferred` |
| the Python `bool` `b` returned by `__eq__` | `Verdict.decided b` | `True ↔ decided true`, `False ↔ decided false` |
| an exception escaping `__eq__` to the caller | `Except.error .interpretationEscaped` | the failure mode the fix removes; never produced by `compareSpec` (always `Except.ok`) |

`type(self)` in the gold body is `UnrecognizedUnit` for every receiver the tests
construct (`UnrecognizedUnit` has no subclasses in the suite), so
`isinstance(other, type(self))` ⇔ `isinstance(other, UnrecognizedUnit)`, matching
the `sameKind`/`otherKind` split above.

## 3. Callee provenance — the one free input

`Unit(other, parse_strict='silent')` is an **unchanged** callee; the gold patch
does not touch `_UnitMetaClass.__call__`. The comparison reacts only to which of
the three outcomes it produces, never to any further detail, so it is modeled as
the **free input** `outcome : InterpretOutcome`. The postconditions of
`compareName` hold for EVERY value of `outcome`, so the callee is owed **no
contract** — strictly weaker than any concrete interpreter (directive 7). There
is therefore **no `axiom`** and **no `axiom_check.py`** (G-AX = skip): nothing is
claimed about the callee that would need executable validation. The mapping of
real interpretation results onto the three outcomes (above) is exercised
end-to-end by G-CONF, which drives the REAL `Unit(...)` interpreter.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7606`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`compareSpec` to Python and classifies `outcome` by running the REAL
`Unit(other, parse_strict='silent')` (the unchanged callee, run live — not an
axiom model), then diffs against the gold-patched `UnrecognizedUnit.__eq__`
behaviour over the boundary operands plus ≥10⁵ fuzzed operands.
