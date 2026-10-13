# refinement.md — django__django-13112

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`normalizeRef` `do` block and the deep `normalizedRef` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are no A legs (no consumed axiom, no A-reference deep model of an
outside callee). The narrative is audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The normalization site — `ForeignObject.deconstruct` (`related.py:584-587`)

Gold hunk:
```
  if isinstance(self.remote_field.model, str):
-     kwargs['to'] = self.remote_field.model.lower()
+     if '.' in self.remote_field.model:
+         app_label, model_name = self.remote_field.model.split('.')
+         kwargs['to'] = '%s.%s' % (app_label, model_name.lower())
+     else:
+         kwargs['to'] = self.remote_field.model.lower()
```

| # | Solution.lean impl op (`normalizeRef`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `ref : List Char` | `self.remote_field.model` (the `str` branch) | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `require (ref.filter (· = '.')).length ≤ 1` | the implicit domain of `app_label, model_name = model.split('.')` (unpacking needs exactly 2 ⇒ ≤1 dot; the `else` covers 0 dots) | R | pins the modeled domain to where the patched branch is defined (mapping.md §3). G-CONF fuzzes only this domain. |
| A2b | `require ∀ c ∈ ref, c.toNat < 128` | the ASCII domain of real model references (`app_label.ModelName` identifiers), on which per-code-point `Char.toLower` == Python `str.lower()` | R | pins the modeled domain to where the `foldCase` ↔ `str.lower()` leg of the §2 bijection is exact: outside ASCII Python's full Unicode case mapping diverges from Lean's ASCII-only `Char.toLower` (`'Σ'.lower()='σ'`, `'İ'.lower()` = 2 code points) (mapping.md §2–§3). G-CONF fuzzes only this domain. |
| A3 | `if ref.contains '.'` | `if '.' in self.remote_field.model` | I | concrete membership of the separator (mapping.md §2). |
| A4 | qualified branch: `appPart ref ++ ['.'] ++ foldCase (namePart ref)` = app-label prefix (verbatim) ++ `'.'` ++ folded model-name suffix | `app_label, model_name = model.split('.'); '%s.%s' % (app_label, model_name.lower())` | I + R | on the ≤1-dot domain, `appPart`/`namePart` (split on first dot) == `model.split('.')`'s two parts (mapping.md §3); `foldCase` == `str.lower()` over the ASCII domain pinned by A2b (R, mapping.md §2); `++ ['.'] ++` == the `'%s.%s'` format. All concrete, transliterated by G-CONF. |
| A5 | unqualified branch: `foldCase ref` | `kwargs['to'] = self.remote_field.model.lower()` | I + R | `foldCase` == `str.lower()` over the ASCII domain pinned by A2b (R). Concrete. |

Discriminating content of the change — for a **qualified** reference the
application-label prefix keeps its original case and only the model-name suffix
is folded (`appPart ref` is NOT folded), whereas the pre-patch unconditionally
folds the whole reference. This lives in step A4 (`appPart ref ++ ['.'] ++
foldCase (namePart ref)`) vs the pre-patch `foldCase ref`. `Solution_prepatch.lean`
reproduces the pre-patch `model.lower()` (`ref.map Char.toLower`) and **fails**
`out = normalizedRef ref` on any qualified ref whose app label has an uppercase
character (G-DIFF) — exactly the `MiXedCase_migrations` scenario the F2P test
`test_reference_mixed_case_app_label` exercises.

## B. No additional change sites

The gold patch touches one branch in one function. There is no second
independently-fixed behaviour and no callee swap; B is empty.

## C. No axioms and no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the
case-normalization of a (possibly application-qualified) model reference — is
modeled **deeply** (the spelled-out `normalizedRef` with `foldCase`/`appPart`/
`namePart`, steps A3–A5, all I + R), not hidden behind an axiom about the
function under change. There is **no consumed axiom** and **no A-reference deep
model of an outside callee**: `str.lower`, `'.' in`, and `str.split('.')` are
language-level string primitives modeled directly by total Lean list/char
operations whose equivalence over the identifier alphabet is fixed by the
mapping.md §2 bijection and checked mechanically by G-CONF. `axiom_check.py` is a
skip stub (`meta.json gates.G-AX.status = "skip"`).

## D. verify(Solution) ⇒ resolved

`normalizeRef` verifies only if its output equals `normalizedRef ref` — i.e. the
qualified branch preserves the application label's case and folds only the model
name (A4), and the unqualified branch folds the whole reference (A5). By R
(`str ↔ List Char`, `str.lower` ↔ `Char.toLower` over the ASCII domain pinned
by A2b) and the ≤1-dot domain (A2), the verified normalization equals the patched
`kwargs['to'] = ...` branch on the tested string references; by G-CONF the R/I
transliteration agrees with the real patched `deconstruct` on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The one
trust point of plan §1.1 that applies is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point (no axioms).
