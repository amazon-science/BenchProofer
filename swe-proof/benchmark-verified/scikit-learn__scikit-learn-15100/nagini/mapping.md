# mapping.md — scikit-learn__scikit-learn-15100

Binds every `model.py` symbol to its repository counterpart at
`base_commit = af8a6e592a1a15d92d77011856d5aa0ec4db4c6c`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sklearn/feature_extraction/text.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `strip_marks(s)` | `strip_accents_unicode(s)` — `sklearn/feature_extraction/text.py:114` (body 132-136) | the modeled changed function |
| `decompose(s)` *(axiom — A-consumed, runtime carrier of `nfkd`)* | `unicodedata.normalize('NFKD', s)` — CPython stdlib, called at `text.py:132` (pre) / `text.py:139` (post) | unchanged callee: canonical decomposition |
| `nfkd(s)` *(axiom — A-consumed, pure spec of decomposition)* | `unicodedata.normalize('NFKD', s)` — CPython stdlib `Lib/unicodedata` | pure spec face of the same callee |
| `is_combining(c)` *(axiom — A-consumed)* | `unicodedata.combining(c)` — CPython stdlib, called at `text.py:136` (pre) / `text.py:141` (post) | unchanged callee: combining-mark classifier |
| `is_fixed_form_guard(s)` *(axiom — runtime guard)* | `s.encode("ASCII", errors="strict")` (try/except `UnicodeEncodeError`) — `text.py:137` (post-patch only) | the new short-circuit guard: succeeds iff `s` is pure ASCII |
| `all_ascii(s)` | the success condition of `s.encode("ASCII", errors="strict")` | pure spec: every code point < 128 |
| `strip_combining(s)` *(deep model — A-reference)* | the list comprehension `''.join([c for c in normalized if not unicodedata.combining(c)])` — `text.py:136`/`141` | pure spec: drop every combining mark, order-preserving; deep model of the UNCHANGED selection, validated == real transform by axiom_check.py (G-AX) |
| `lemma_ascii_is_fixed_point(s)` | (proof artifact, no repo counterpart) | discharges that the ASCII fast path is behaviour-preserving |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the guard `if normalized == s: return
s` at `text.py:133-134`, replaced by the strict-ASCII encodability test.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `s` argument and the return) | `List[int]` of Unicode code points | `s[k]` ↔ `ord(str[k])`; `len(s)` ↔ `len(str)`; concatenation/join ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` | `ToSeq(list)` materializes the list as a `PSeq`; `+`/`take`/`drop`/`len`/`[i]` mirror `str`/slice/`len`/index |
| `return s` (ASCII fast path) | a fresh code-point copy of `s` (built by the copy loop) | `str` is **immutable**: returning the input object is observationally identical to returning a value-equal fresh string. Modeled as a copy so the read-only input keeps fractional permission (directive 5) while the result carries full permission. |
| `unicodedata.normalize('NFKD', s) == s` (pre-patch guard) | `ToSeq(normalized) == ToSeq(s)` | sequence equality on code points |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `nfkd` / `decompose` ↔ `unicodedata.normalize('NFKD', .)` (A-consumed)
**Callee:** CPython `unicodedata.normalize('NFKD', s)` — returns the canonical
decomposition (NFKD: compatibility decomposition, no recomposition) of `s`.
Docs: https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize.

**Weakest contract the proof consumes:**
`Ensures(Implies(all_ascii(s), Result() == s))` — NFKD is the identity on any
sequence of 7-bit code points (ASCII has no compatibility decompositions). This
is the only `nfkd` property consumed (it discharges the ASCII fast path: the
returned-unchanged input equals the decomposition). The general path uses
`decompose` only as "the fixed function whose output we then filter" — it needs
no value property of `nfkd` beyond functionality.

**Soundness (G-AX):** `axiom_check.py` runs the real `normalize('NFKD', .)` on
the full ASCII range, empty, words, and asserts identity; it never claims any
value on non-ASCII input (no over-claim).

### 3.2 `is_combining` ↔ `unicodedata.combining(.)` (A-consumed)
**Callee:** CPython `unicodedata.combining(ch)` — returns the canonical
combining class (an int) of `ch`; non-zero iff `ch` is a combining mark. The
model predicate is `combining(ch) != 0`.
Docs: https://docs.python.org/3/library/unicodedata.html#unicodedata.combining.

**Weakest contract the proof consumes:**
`Ensures(Implies(c < 128, not Result()))` — every 7-bit code point has
combining class 0 (ASCII contains no combining marks). This is the only
`is_combining` property consumed (it discharges the lemma that an ASCII
sequence is a fixed point of `strip_combining`). No value is claimed for
non-ASCII code points.

**Soundness (G-AX):** `axiom_check.py` runs the real `combining` exhaustively
over all 128 ASCII code points (boundary) and asserts class 0; non-ASCII
classifications are exercised by the deep-model reference check, not constrained
by the axiom.

### 3.3 `is_fixed_form_guard` ↔ `str.encode("ASCII", errors="strict")` (runtime guard)
**Callee:** CPython `str.encode("ASCII", errors="strict")` — raises
`UnicodeEncodeError` iff any code point is ≥ 128; the patch's `try/except`
turns this into a boolean fast-path test. Modeled as
`Ensures(Result() == all_ascii(ToSeq(s)))`.

**Soundness (G-AX):** `axiom_check.py` runs the real encode in a `try/except`
and asserts success ⇔ `all(ord(ch) < 128)` over boundary + fuzz.

### 3.4 `strip_combining` deep model ↔ the list comprehension (A-reference)
The UNCHANGED selection `[c for c in normalized if not combining(c)]` is modeled
**deeply** by the `@Pure` front-recursive fold `strip_combining` (paired with
the backward loop in `strip_marks`). There is **no consumed axiom about the
function under change** — `strip_combining` is spelled out. Its composition with
`nfkd` is validated **== the real post-patch transformation**
`''.join(c for c in normalize('NFKD', s) if not combining(c))` out-of-band by
`axiom_check.py` (G-AX) over 25 boundary + 40 000 fuzz inputs (including the
already-decomposed F2P discriminators `chr(110)+chr(771)`, `"ö"`,
`"̀́̂̃"`, `"ȫ"`). 0 mismatches.

`axiom_check.py` imports only the standard-library `unicodedata` module (the
very module the patch calls); nothing repo-specific.

## 4. Conformance (G-CONF)

`conformance_check.py` diffs the contract-stripped impl region (shadow, with
the three modeled callees delegated to the real stdlib functions per section 3)
against the real patched `strip_accents_unicode` in-container over >= 1e5
inputs (boundary + per-code-point sweep + fuzz). Pinned fuzz seed: **15100**
(the instance number).
