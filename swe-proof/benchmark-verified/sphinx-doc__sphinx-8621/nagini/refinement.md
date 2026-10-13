# refinement.md — sphinx-doc__sphinx-8621

The operation-by-operation correspondence between `model.py`'s implementation
(the `split_keystrokes` / `keystroke_is_atomic` impl regions and the deep
`kparts` model) and `patch.diff` (the gold patch).  Each step is tagged **R**
(type refinement), **A** (axiomatized callee — split into **A-consumed**, where
the proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation).  The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The split site — `KeyboardTransform.pattern` / `.run` (`sphinx/builders/html/transforms.py:40,45`)

Gold hunk:
```
- pattern = re.compile(r'(-|\+|\^|\s+)')
+ pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')
```
The single changed line is the class attribute `pattern`; it is consumed one
line later by `parts = self.pattern.split(node[-1].astext())` (line 45), then
the unchanged loop builds a `<kbd>` literal node per keystroke part and a text
node per separator part, leaving the node untouched when `len(parts) == 1`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text: List[int]` (with `Requires` confining it to printable ASCII, code points 32..126) | the `str` `node[-1].astext()` argument of `self.pattern.split` | R | `str` ↔ `List[int]` code points (mapping.md §2). The domain `Requires` is the modelled-domain restriction, enforced in the spec (mapping.md §2.1). |
| A2 | `split_keystrokes` returns `kparts(ToSeq(text), False)`, the front-recursive flanked-split fold (including blank-run merging) computed by the backward loop | `self.pattern.split(node[-1].astext())` with the **post-patch** pattern `r'(?<=.)(-|\+|\^|\s+)(?=.)'` | A-reference | the changed string operation is modelled **deeply**: `kparts` (the spelled-out flanked-split fold in the `pure` region) and the verified backward loop in `split_keystrokes` ARE the split. There is no consumed `split` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `re.compile(NEW).split` on boundary + 200 000 fuzz inputs over the WHOLE modelled domain (printable ASCII, blank runs included) and asserts `re.split == kparts`, **0 mismatch**, plus the literal F2P/P2P keystroke strings. The lookbehind/lookahead `(?<=.)…(?=.)` makes a separator match only when flanked, and the greedy `\s+` collapses a flanked blank run into one token — exactly `kparts`'s per-code-point rule on the printable-ASCII domain (mapping.md §3.1). |
| A3 | the part sequence is a `PSeq[PSeq[int]]`; each inner `PSeq` is one substring | `parts`, a `List[str]` of substrings (alternating keystroke / separator) | R | substring ↔ inner code-point `PSeq`; list-of-substrings ↔ `PSeq[PSeq[int]]` (mapping.md §2). |
| A4 | `keystroke_is_atomic` returns `len(split_keystrokes(text)) == 1` | the decision `if len(parts) == 1: continue` (the node is left as a single `<kbd>`) | I + R | the single-part test is the identical concrete `len(...) == 1`; the carrier of `parts` is refined per A3. The unchanged node-construction loop below it (build a `<kbd>` per keystroke part, a text node per separator part) is not part of the fix and is not modelled. |

The discriminating content of the change — a separator at the boundary of the
text is NOT a separator — lives in `kparts`'s flanking guard (`lead` ⇒ a
preceding character; `len(s) >= 2` ⇒ a following character) ⇔ the
`(?<=.)…(?=.)` lookarounds of the real pattern.  The pre-patch pattern
`(-|\+|\^|\s+)` split on EVERY separator occurrence; `model_prepatch.py`
reproduces that (the split branch fires on `is_sep(c)` / `is_space(c)` with no
flanking guard) and **fails** the loop invariant
`result == kparts(ToSeq(text).drop(i), i > 0)`, which is exactly the spec
sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I.  The one operation that genuinely
*changed* — the keystroke split — is modelled **deeply** (the spelled-out
flanked-split fold `kparts`, including blank-run merging, consumed by both
modeled functions; an **A-reference**), not hidden behind an axiom about the
function under change: there is **no consumed `split` axiom**.  There is no
A-consumed axiom in this bundle at all; the changed `re...split` callee appears
only as the **A-reference** that G-AX validates the deep model against.

## B2. Termination obligation (total correctness)

Nagini is a partial-correctness verifier by default: a non-terminating
implementation (bare self-recursion, an endless loop) satisfies every
`Ensures` vacuously while sharing the spec byte-for-byte — a wrong
implementation the spec would otherwise admit. The real split always answers:
one `re.split` pass over a finite keystroke string plus a length test is a
bounded computation. The spec therefore carries
`Requires(MustTerminate(1))` on `split_keystrokes` (consumed in the impl loop
by `Invariant(MustTerminate(i))`, with `i` the strictly decreasing,
bounded-below measure) and `Requires(MustTerminate(2))` on
`keystroke_is_atomic` (2 > 1 covers its call into `split_keystrokes`). With
termination required and the exact functional postconditions
`Result() == kparts(ToSeq(text), False)` /
`Result() == (len(kparts(ToSeq(text), False)) == 1)`, any verifying same-spec
implementation must terminate and return exactly the pinned part sequence /
atomicity verdict — the spec is functionally complete on its domain.

## C. verify(model) ⇒ resolved

`split_keystrokes` verifies only if its output equals the exact flanked-separator
split `kparts(ToSeq(text), False)` (A2), and `keystroke_is_atomic` verifies only
if it reports a single part exactly when `len(kparts(...)) == 1` (A4).  By R
(`str` ↔ `List[int]`, `List[str]` ↔ `PSeq[PSeq[int]]`) the verified split equals
`self.pattern.split(node[-1].astext())` with the post-patch pattern on the whole
modelled domain; by G-AX the deep model `kparts` equals the real
`re.compile(NEW).split` (A-reference) on EVERY input of that domain (printable
ASCII, blank runs included — 200 000 fuzz, 0 mismatch — plus the literal
F2P/P2P keystroke strings).  Therefore a model satisfying this spec, refined by
the map above, computes the same `parts` list as the gold patch on **every
tested keystroke input**, and the unchanged node-construction loop turns that
identical `parts` list into identical HTML.  In particular:

- the two new FAIL_TO_PASS cases (`:kbd:`-`` → one `<kbd>`; `:kbd:`Alt+^`` →
  `Alt`/`+`/`^` with no empty `<kbd>`) pass, because `kparts` reproduces them
  exactly (`['-']`, `['Alt','+','^']`);
- the PASS_TO_PASS blank-run case `:kbd:`M-x  M-s`` is INSIDE the verified
  guarantee: it is printable ASCII, so the domain `Requires` holds, and the
  deep model collapses the doubled blank into one separator token
  (`['M','-','x','  ','M','-','s']`) exactly as the real `\s+` branch does.
  An impl that drops the `\s+` branch (the whitespace-less candidate the panel
  flagged) therefore FAILS the loop invariant and does NOT verify — so the spec
  no longer licenses any refinement that regresses this P2P input.

The whitespace-less "regressing refinement" counterexample that previously broke
`verify ⟹ resolved` is now killed: the blank-run merging is part of `kparts`, so
the postcondition is a positive, CORRECT claim on the blank-run input rather than
a wrong one.  No "unchanged branch shipped verbatim" argument is needed — the
blank branch is modelled in the spec, not waved through.

The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX, here
the A-reference, 0 mismatch over the whole modelled domain) and refinement
fidelity (this document, G-EQ).
