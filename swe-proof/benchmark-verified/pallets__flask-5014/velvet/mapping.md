# mapping.md — pallets__flask-5014

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7ee9ceb71e868944a46e1ff00b506772a53a4f1d`, states the Lean↔Python
type bijection (used by G-CONF), and records the absence of any consumed axiom.

Repo file under change: `src/flask/blueprints.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateBlueprintName (s : List Char) → Bool` | `Blueprint.__init__(self, name, import_name, ...)` — `src/flask/blueprints.py:172` (the name-validation prologue, body lines 185–194) | the modeled changed function: the constructor's name acceptance decision (accept = construction proceeds; reject = a `ValueError` is raised). |
| `containsDot (s : List Char) → Bool` | the `"." in name` membership test — `src/flask/blueprints.py:193` | pure spec helper: does the candidate name contain the dot code point U+002E. |
| `validName (s : List Char) → Bool` | the conjunction of the two reject guards (post-patch): accept iff `name` is non-empty AND dot-free | pure spec predicate: the post-patch accept/reject decision, expressed structurally over the input. |

The repo line the patch ADDS (for the refinement audit; never referenced from the
consumer spec view): a guard
`if not name: raise ValueError("'name' may not be empty.")` inserted between the
`super().__init__(...)` call (`blueprints.py:185`) and the pre-existing
`if "." in name:` dot check (`blueprints.py:193`).

## 2. Type abstraction (R-refinements)

| repo reality | Lean carrier | bijection |
|---|---|---|
| `name: str` (the blueprint name argument) | `s : List Char` (Unicode code points) | `s[k]` ↔ the `k`-th code point of `name`; `s.length` ↔ `len(name)`; the empty `str` `""` ↔ the empty list `[]` (`s.isEmpty`). |
| `not name` (Python truthiness of a `str`) | `s.isEmpty` | a `str` is falsy **iff** it is `""`; for the `str` carrier the only falsy value is the empty string, i.e. zero code points. (`name` is always a `str` at this call — the F2P/P2P tests pass `str` literals.) |
| `"." in name` (single-char membership on `str`) | `containsDot s` — `'.' ∈ s` | `"." in name` for the one-character needle `"."` is exactly "the code point U+002E occurs in `name`"; the front-recursive fold `containsDot` decides that membership. |
| accept (constructor proceeds) vs reject (`raise ValueError(msg)`) | `out = true` (accept) vs `out = false` (reject) | the constructor either proceeds to build the object (accept) or raises a `ValueError` (reject); the harness/F2P test observes only *that a `ValueError` is raised vs not*, not its message. Two distinct `ValueError`s in the post-patch code (empty, dot) are both "reject" = `out = false`. |
| `import_name: str` + the base initialiser `super().__init__(...)` → `Scaffold.__init__` run before the name decision | abstracted away (no Lean carrier) | the base init is unchanged by the patch, never inspects/validates `name` (`name` is not even a parameter of `Scaffold.__init__`), and so cannot alter the accept/reject decision. The Bool decision spec observes none of its state, so it is not modeled (and not axiomatized — see §3). |

`str` is modeled as `List Char` throughout (Lean indexing is total/sound); the
acceptance predicate is decided by a backward per-code-point fold over `s`.

## 3. Axioms / callee provenance

**None.** There is no consumed axiom and no deep-model reference (`axioms` region
is empty). The acceptance decision is a pure property of the candidate name's
code points (emptiness ∧ dot-freeness), modeled deeply in the `pure` region
(`containsDot` / `validName`). The unchanged base initialiser the constructor
delegates to before the decision (`Scaffold.__init__`, `src/flask/scaffold.py`)
is independent of `name` and observes no state this spec measures, so it is
abstracted away rather than axiomatized (cf. LESSONS "abstracted-input-not-axiom";
the Nagini port modeled it as an `init_base` axiom only to carry Viper fractional
permissions, which Lean — having no aliasing — does not need). Consequently there
is no `axiom_check.py` (G-AX skips).

## 4. G-CONF fuzz seed

`conformance_check.py` pins `SEED = 5014`, `N_FUZZ = 100_000`, biased toward the
discriminating empty / dotted / boundary cases. The R/I shadow
`validName(s) = (s != "") and ("." not in s)` is diffed against the live
post-patch `flask.Blueprint(name, __name__)` behaviour (raises `ValueError`
== reject == `False`; constructs == accept == `True`), with a documented
re-free fallback that transliterates the post-patch guards directly.
