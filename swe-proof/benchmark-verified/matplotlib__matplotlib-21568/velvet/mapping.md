# mapping.md — matplotlib__matplotlib-21568

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f0632c0fc7339f68e992ed63ae4cfac76cd41aad`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom / deep model.

Repo file under change: `lib/matplotlib/dates.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderTexLabel (text : List Char)` | `_wrap_in_tex(text)` — `lib/matplotlib/dates.py:594` (body lines 595–601) | the modeled changed function (math-label TeX wrapper) |
| `reSub` *(axiom — opaque unchanged callee)* | `re.sub(p, r'}$\1$\\mathdefault{', text)` — `dates.py:596` (CONTEXT line, unchanged) | letter-run pre-processor; opaque map on code points |
| `removeEmpty` *(axiom — opaque unchanged callee)* | `ret_text.replace('$\\mathdefault{}$', '')` — `dates.py:600` (CONTEXT line, unchanged) | empty-math-group collapse; opaque map on code points |
| `mathProtect (c : Char)` | the per-character mapping the chained `.replace` implements (`dates.py:599` post-patch) | pure spec: math-protection of one code point |
| `protectSeq (s : List Char)` *(deep model — A-reference)* | `ret_text.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')` — the changed `.replace` chain (`dates.py:599` post-patch) | pure spec: math-protection of a sequence; deep model of the CHANGED string op, validated `protectSeq == real chained-replace` by axiom_check.py (G-AX), NOT consumed as a behavioral axiom |

The pre-patch repo line the change replaces (refinement audit only, not in the
consumer spec view): `ret_text = '$\\mathdefault{'+ret_text.replace('-', '{-}')+'}$'`
(`dates.py:599` pre-patch) — protected ONLY the dash.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the `text` argument and `_wrap_in_tex`'s return) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| string literals `'$\\mathdefault{'`, `'}$'` | `"$\\mathdefault{".toList`, `"}$".toList` | concrete `List Char` literals; the wrap step is concrete (I), not refined |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the changed operation is per-code-point.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `protectSeq` deep model ↔ the chained `.replace` (A-reference)
**Operation:** the changed string op
`s.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')`. It is modeled
**deeply** by `protectSeq` (with `mathProtect`) in the `pure` region; there is
**no behavioral axiom** the proof consumes for it. The per-code-point map is:

```
'-' (45) -> '{-}'   ':' (58) -> '{:}'   ' ' (32) -> '\;'   else identity
```

The chained left-to-right `.replace` equals this single per-code-point
substitution because the three targets `{- : space}` are pairwise distinct and
**no replacement output contains a code point a later replacement targets**:
`'{-}'` and `'{:}'` contain only `{ - } :` and `'\;'` contains only `\ ;` — none
of which is `-`, `:` or ` ` consumed by a *subsequent* `.replace`. Hence order
is irrelevant and the chain collapses to `protectSeq` (mapping is exact). The
three protected code points are the single behavioural change the F2P tests
observe (`{-}`/`{:}`/`\;`).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL chained `.replace`
(genuine Python `str.replace`, the same operation the gold patch performs) on
boundary inputs over `- : space` (alone, doubled, combined, mixed, adjacent to
already-emitted braces) plus 20 000 randomized fuzz strings, asserting
`protectSeq == real chained-replace` (A-reference). Imports only stdlib. Exit 0
iff sound.

### 3.2 `reSub`, `removeEmpty` (opaque unchanged callees)
**Callees:** `re.sub(p, r'}$\1$\\mathdefault{', text)` (`dates.py:596`) and
`str.replace('$\\mathdefault{}$', '')` (`dates.py:600`). Both are CONTEXT lines
in the gold diff — **unchanged** by the patch. They are modeled as
**uninterpreted total functions** (axioms with NO `ensures`): the routine under
spec consumes their results but the spec asserts nothing about their behaviour,
so the contract is the weakest possible (directive 7) — just "a fixed function
of the input." Because they are identical in the spec and in any verifying
impl, and identical between `Solution.lean` and the gold (same real callees),
they cannot hide a discriminator (the patch did not touch them). G-AX confirms
they are deterministic functions of their input (vacuous w.r.t. behaviour).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`21568`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `mathProtect`/`protectSeq` (R/I-tagged ops) and the concrete wrap
to Python, and leaves the A-tagged callees `reSub`/`removeEmpty` as the REAL repo
callees (`re.sub` with the repo pattern; the real `'$\\mathdefault{}$'`
removal). The oracle is the patched `_wrap_in_tex` imported in-container.
