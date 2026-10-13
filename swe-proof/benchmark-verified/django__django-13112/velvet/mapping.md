# mapping.md — django__django-13112

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 09914ccf688974e068941f55412b930729bafa06`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records that
this bundle consumes no axioms.

Repo file under change: `django/db/models/fields/related.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalizeRef (ref : List Char)` | the model-reference normalization branch inside `ForeignObject.deconstruct` — `django/db/models/fields/related.py:584-587` (`if isinstance(self.remote_field.model, str): kwargs['to'] = ...`) | the modeled changed behaviour: how a string model reference is canonicalized into `kwargs['to']` |
| `normalizedRef (ref : List Char)` *(deep model)* | the post-patch branch body (`django/db/models/fields/related.py:584-589` post-patch) | pure spec: canonical normalization of a string model reference; modeled DEEPLY from concrete char ops, NOT an axiom |
| `foldCase`, `isQualified`, `appPart`, `namePart` | the components of that branch (`str.lower()`, `'.' in m`, `m.split('.')`) | pure spec helpers |

No symbol is axiomatized: the changed operation is a value-level string
transformation built entirely from concrete character operations over the input
(directive 7 — the operation the patch changes is never axiomatized). There is
no unchanged outside callee whose contract the proof consumes, and no A-reference
deep model of an outside callee.

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the unconditional `self.remote_field.model.lower()`
(`related.py:585`, pre-patch), which lowercases the entire reference.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.remote_field.model` when it is a `str` (the reference), and the resulting `kwargs['to']` `str` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; the literal `'.'` ↔ `'.'` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `s.lower()` (a model name / unqualified reference) | `s.map Char.toLower` (`foldCase`) | **exact over the ASCII domain** (every code point < 128), which contains the identifier alphabet — ASCII letters/digits/underscore — of application labels and model names. This is not merely a fuzz-alphabet convention: the spec **pins** it with `require ∀ c ∈ ref, c.toNat < 128`, because outside ASCII the correspondence breaks (Lean `Char.toLower` folds only U+0041–U+005A, while Python `str.lower()` applies full Unicode case mapping — e.g. `'Σ'.lower()='σ'`/final-sigma `'ς'`, and `'İ'.lower()` is TWO code points — so per-code-point `Char.toLower` ↔ `str.lower()` is a bijection only on ASCII). The fuzz alphabet (G-CONF) is restricted to the same domain. |
| `'.' in m` | `m.contains '.'` (`isQualified`) | membership of the separator |
| `m.split('.')` into `(app_label, model_name)` (valid only when `m` has exactly one dot) | `appPart = takeWhile (· ≠ '.')`, `namePart = (dropWhile (· ≠ '.')).drop 1` | the prefix before / suffix after the first dot. The Python tuple-unpacking `app_label, model_name = m.split('.')` SUCCEEDS only when `m` contains exactly one dot; the `require (ref.filter (· = '.')).length ≤ 1` pins the modeled domain to that (≤1 dot) — see §3. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point (a case fold + a separator
split).

## 3. Modeled domain (the `require`)

The patched branch is
```python
if '.' in model:
    app_label, model_name = model.split('.')   # unpacks to EXACTLY 2 -> needs exactly 1 dot
    to = '%s.%s' % (app_label, model_name.lower())
else:
    to = model.lower()
```
`model.split('.')` returns `len(dots)+1` parts; the two-target unpacking raises
`ValueError: too many values to unpack` when the reference has **more than one**
dot, and the `'.' in` guard already excludes the zero-dot case from the `if`
branch. The behaviour is therefore only defined for references with **at most
one** dot. `Solution.lean`'s `require (ref.filter (· = '.')).length ≤ 1` pins
exactly that domain; `normalizedRef`'s `appPart`/`namePart` (split on the FIRST
dot) coincide with `model.split('.')` precisely on that domain.

The second `require ∀ c ∈ ref, c.toNat < 128` pins the reference to the ASCII
domain, where the per-code-point `Char.toLower` fold used by `foldCase` is
exactly Python `str.lower()` (§2). Outside ASCII the two case folds genuinely
diverge (`'Σ'.lower()='σ'`, `'İ'.lower()` = 2 code points), so a spec without
this `require` would claim behaviour the model does not reproduce; with it, the
modeled domain is exactly where the R-refinement of §2 is a bijection. Real
Django model references — `app_label.ModelName` or a bare `ModelName`, built
from Python identifier characters used as app labels / model names in practice
(ASCII letters/digits/underscore) — satisfy it.

G-CONF fuzzes only references with ≤1 dot over the ASCII identifier alphabet
(mapping.md §4) so the bijection is exact on every tested input. (>1-dot
references are not valid Django model references.)

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13112`** so the
consumer-side verdict (§11.3) is reproducible. Its R/I shadow transliterates
`normalizedRef` (all R/I-tagged ops) to Python; there is no A-tagged callee to
leave as a real callee. The ORACLE is the REAL patched `ForeignKey.deconstruct`,
driven on a `ForeignKey` constructed with a string model reference and read back
from `kwargs['to']` (G-RESOLVE behaviour). Inputs are restricted to the modeled
domain (≤1 dot) over the identifier alphabet (§2, §3).

## 5. No axioms (G-AX)

This bundle declares no `axiom` and no A-reference. `axiom_check.py` is a skip
stub returning exit 0 with a skip status (`meta.json gates.G-AX.status = "skip"`).
The deep model's fidelity to the patched behaviour is exercised mechanically by
`conformance_check.py` (G-CONF) against the real patched method.
