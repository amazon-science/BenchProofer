# mapping.md — scikit-learn__scikit-learn-15100

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = af8a6e592a1a15d92d77011856d5aa0ec4db4c6c`, states the type
abstraction (the Lean↔Python bijection G-CONF uses to bridge values), and
gives the provenance of each opaque callee.

Repo file under change: `sklearn/feature_extraction/text.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `stripDiacritics (s : List Char)` | `strip_accents_unicode(s)` — `sklearn/feature_extraction/text.py:114` (body lines 132-137) | the modeled changed function (unicode accent stripper) |
| `canonicalDecompose` *(opaque — free, no contract)* | `unicodedata.normalize('NFKD', s)` — CPython stdlib `unicodedata`, called at `text.py:132` (pre-patch) / `text.py:140` (post-patch) | UNCHANGED stdlib callee: canonical (compatibility) decomposition |
| `isCombiningMark` *(opaque — free, no contract)* | `unicodedata.combining(c)` (read as `!= 0`) — CPython stdlib `unicodedata`, called at `text.py:137` (pre-patch) / `text.py:141` (post-patch) | UNCHANGED stdlib callee: combining-class test for one code point |
| `markFreeSeq (xs : List Char)` *(deep model — I)* | the list comprehension `''.join([c for c in normalized if not unicodedata.combining(c)])` (`text.py:137/141`) | pure spec: keep non-combining code points, drop combining marks; the changed-application structure, modeled concretely (not axiomatized) |

The pre-patch behaviour the change removes (refinement audit only, not in the
consumer spec view): the early-out `if normalized == s: return s` guard
(`text.py:133-134`) that returns the input UNCHANGED whenever the string already
equals its NFKD decomposition — the source of the bug.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the `s` argument and the return value) | `List Char` | `s` (Python str) ↔ `List Char` of its code points; `len(s)` ↔ `l.length`; `str` concat / `''.join` ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `unicodedata.combining(c)` (an `int`, the combining class) | `isCombiningMark c : Bool` | `combining(c) != 0` ↔ `isCombiningMark c = true`; only the zero/non-zero distinction is observed (`not unicodedata.combining(c)`) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is strictly per-code-point.

## 3. Callee provenance — opaque free functions (G-AX skip)

Both callees are UNCHANGED standard-library routines whose *application* the
patch reorganises but whose *behaviour* it never touches. Each is modeled as an
OPAQUE free function (`opaque canonicalDecompose`, `opaque isCombiningMark`)
with **no asserted `ensures`** — i.e. the WEAKEST possible contract: none. The
frozen spec pins the result purely as `markFreeSeq (canonicalDecompose s)`,
making no behavioural claim about either callee beyond their (uninterpreted)
identity. Because nothing is asserted about their values, there is nothing to
validate against the real callees: **no consumed axioms, no axiom_check.py, G-AX
status `skip`** (the django-12276 precedent for opaque/free unchanged callees).

The soundness obligation that DOES remain — that the deep model `markFreeSeq`
composed with these callees reproduces the patched function — is a refinement-
fidelity claim over the I leg, checked mechanically by **G-CONF**
(`conformance_check.py`), which runs the *real* `unicodedata.normalize`/
`unicodedata.combining` in the shadow.

### 3.1 `canonicalDecompose` ↔ `unicodedata.normalize('NFKD', ·)`
The 'NFKD' (Normalization Form Compatibility Decomposition) form expands every
precomposed character into base + combining marks. Pinned constant `'NFKD'` in
both pre- and post-patch source. No flag dependency.

### 3.2 `isCombiningMark` ↔ `unicodedata.combining(·) != 0`
`unicodedata.combining(c)` returns the canonical combining class of `c` (a
non-negative int), `0` for non-combining code points. The comprehension keeps a
code point iff `not unicodedata.combining(c)`, i.e. iff the class is `0`. So the
keep predicate is exactly `isCombiningMark c = false`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15100`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`markFreeSeq` (the I-tagged keep/drop fold) to Python and leaves the two opaque
callees as the REAL `unicodedata.normalize('NFKD', ·)` / `unicodedata.combining`
(A-tagged → run the real callee, not a model). The fuzz alphabet is weighted
toward accented Latin letters, standalone combining marks (U+0300..U+036F), and
already-decomposed sequences — exactly the inputs the bug concerns.
