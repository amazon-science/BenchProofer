# mapping.md — sphinx-doc__sphinx-9711

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 81a4fd973d4cfcb25d01a7b0be62cdb28f82406d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `sphinx/extension.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `anyRequirementUnmet (reqs : List Requirement)` | `verify_needs_extensions(app, config)` — `sphinx/extension.py:42` (loop body line 47-58) | the modeled changed function: returns whether ANY loaded extension fails its minimum-version requirement (the boolean the function turns into a raised `VersionRequirementError`) |
| `Requirement` (structure) | one entry `(extname, reqversion)` of `config.needs_extensions` together with `app.extensions.get(extname)` | the per-requirement carrier (see §2) |
| `verGt (a b : List Char)` *(deep model — A-reference)* | `Version(reqversion) > Version(extension.version)` — `packaging.version.Version`, imported by the gold patch (`sphinx/extension.py:13` post-patch) | pure spec: the numeric component-wise version ordering; deep model of the **unchanged** stdlib-grade callee `packaging.version.Version.__gt__`, validated `verGt == Version-compare` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `unmet (r : Requirement)` | the per-requirement branch: `extension.version == 'unknown version' or reqversion > extension.version` (post-patch: `fulfilled` flag) | pure spec: is this one requirement unmet? |
| `anyUnmet (rs : List Requirement)` | the `for … in config.needs_extensions.items()` loop's disjunctive accumulation of the per-requirement test | pure spec: does any requirement fail? |
| `splitDots`, `parseComp`, `relGt`, `numericVer`, `compOk`, `reqWellFormed` | internals of `packaging.version.Version`'s release-segment parse + tuple compare | pure spec helpers spelling out the numeric ordering on the modeled domain |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the textual comparison `reqversion > extension.version`
(`extension.py:54`), a lexicographic `str` ordering. Post-patch this becomes the
`Version(reqversion) > Version(extension.version)` numeric comparison guarded by
`try/except InvalidVersion` (which falls back to the old textual ordering).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a version `str` (`reqversion`, `extension.version`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; per-character via `Char.ofNat (ord ch)`; on the numeric domain every char is an ASCII digit or `'.'` |
| one `(extname, reqversion)` ↔ `app.extensions.get(extname)` pair | one `Requirement` | `required` ↔ `reqversion`; `present` ↔ `extension.version` (the loaded version, meaningful only when present & known); `isPresent` ↔ `app.extensions.get(extname) is not None`; `isKnown` ↔ `extension.version != 'unknown version'` |
| `config.needs_extensions` dict + `app.extensions` dict | `List Requirement` | each dict entry → one `Requirement`; order-insensitive because the model is a disjunction (`anyUnmet`) — matches the function's "raise iff any item fails" semantics |
| `extname` (the key) | (omitted) | the extension name is observationally irrelevant to whether the requirement is *unmet* (it only personalises the warning/error message text, which `test_needs_extensions` does not assert on). Identity / dropped. |
| raising `VersionRequirementError` | the returned `Bool = true` | the function raises iff the disjunction is true; G-CONF observes "did the real patched function raise?" against the shadow boolean |
| `app.extensions.get(extname) is None` → `logger.warning(...); continue` | `isPresent = false` ⇒ `unmet = false` | an absent extension is warned-and-skipped, never a raise — modeled as imposing no obligation |

The modeled **numeric-version domain** (`reqWellFormed` / `numericVer`): every
dotted component of `required` (and of `present` when present & known) is a
non-empty run of decimal digits. This is the domain on which the gold patch's
`Version(...)` comparison is total and where the new behaviour the issue/F2P
demand lives. Outside it the gold patch catches `InvalidVersion` and falls back
to the old textual ordering — behaviour the spec deliberately does not model;
the `require reqs.all reqWellFormed` precondition pins the modeled scope and the
G-AX / G-CONF fuzzers stay inside it.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `verGt` deep model ↔ `packaging.version.Version` comparison (A-reference)
**Callee:** `packaging.version.Version.__gt__` (via `Version(a) > Version(b)`),
the comparator the gold patch imports (`from packaging.version import
InvalidVersion, Version`). The changed comparison operation is modeled **deeply**
by `verGt` (with `splitDots`/`parseComp`/`relGt`) in the `pure` region; there is
**no `versionGt` axiom** the proof consumes.

`packaging.Version` parses a version into a *release segment* — a tuple of
non-negative integers from the dot-separated numeric components — and orders two
versions by comparing those tuples component-wise, **numerically**, with the
shorter tuple zero-extended (so `1.0 == 1.0.0`, and leading zeros like `01` are
absorbed to `1`). On the modeled numeric domain `verGt`/`relGt` reproduce exactly
this: `splitDots` recovers the dotted components, `parseComp` reads each as a
base-10 numeral (absorbing leading zeros), and `relGt` is the zero-extended
component-wise strict order. The headline discriminator the issue names —
`Version('0.10') > Version('0.6')` is **true** (numeric) though `'0.10' > '0.6'`
is **false** (textual), and symmetrically `Version('3.9') > Version('3.10')` is
**false** though `'3.9' > '3.10'` is **true** — is exactly the `9 < 10`
component comparison `relGt` performs. Docs:
https://packaging.pypa.io/en/stable/version.html

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`packaging.version.Version` comparator on 19 boundary version pairs (the issue's
`3.9/3.10` and `0.6/0.10`, trailing-zero equalities `1.0/1.0.0`, leading-zero
absorption `01.2/1.2`, multi-digit components `10/9`, reflexive equals) plus
50 000 randomized numeric-domain pairs, asserting `verGt(a,b) == (Version(a) >
Version(b))` every time (and that `Version()` never raises inside the modeled
domain). Imports only `packaging` — the same module the gold patch calls. Exit 0
iff sound.

### 3.2 No consumed axioms
There are no `axiom`-region facts the proof consumes. The only kind-A construct
is the A-reference deep model of §3.1. The `unknown version` sentinel and the
absent-extension branch are modeled directly as `Requirement` flags
(`isKnown`/`isPresent`), not axiomatized.

## 4. G-CONF / G-AX fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9711`**; `axiom_check.py`
seeds its fuzz with **`9711`** as well, so both consumer-side verdicts are
reproducible. The R/I shadow `conformance_check.py` builds transliterates
`verGt`/`unmet`/`anyUnmet` (R/I-tagged ops) to Python and observes the **real
patched** `verify_needs_extensions` (raises ⇔ shadow boolean) through duck-typed
`app`/`config` mocks (the A-reference comparator `Version` runs for real inside
that callee). All fuzz stays inside the modeled numeric domain (`reqWellFormed`).
