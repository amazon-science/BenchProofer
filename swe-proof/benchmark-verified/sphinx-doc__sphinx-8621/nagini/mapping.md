# mapping.md — sphinx-doc__sphinx-8621

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 21698c14461d27933864d73e6fba568a154e83b3`, states the type
abstraction, and gives the provenance of the one kind-A reference (the changed
split operation, modelled deeply and validated against the real callee by
axiom_check.py / G-AX).

Repo file under change: `sphinx/builders/html/transforms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `split_keystrokes(text)` | the splitting step `parts = self.pattern.split(node[-1].astext())` in `KeyboardTransform.run` — `sphinx/builders/html/transforms.py:45`, where `self.pattern` is the class attribute `pattern` defined at line 40 | the modeled changed behaviour: how a keystroke text is broken into the alternating keystroke / separator parts |
| `keystroke_is_atomic(text)` | the decision `if len(parts) == 1: continue` in `KeyboardTransform.run` — `sphinx/builders/html/transforms.py:46-47` | the modeled observable consequence: a text is rendered as one indivisible `<kbd>` exactly when the split yields a single part |
| `kparts(s, lead)` *(deep model — A-reference)* | `KeyboardTransform.pattern.split(...)` with the **post-patch** pattern `re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')` — `sphinx/builders/html/transforms.py:40` (post-patch) | pure spec: the flanked-separator split (including blank-run merging); the deep model of the changed `re...split` callee, validated `kparts == re.split` by axiom_check.py (G-AX) over the WHOLE modelled domain, NOT consumed as an axiom |
| `is_sep(c)` | the single-character separator alternation `-|\+|\^` of the pattern (the three compound-key separators) | pure spec: single-separator-character test |
| `is_space(c)` | the `\s+` alternation of the pattern, restricted to the modelled domain where the only blank-space code point is the ordinary space (32) | pure spec: blank-space test (a blank run is a maximal run of these) |
| `in_domain(c)` | (no repo counterpart) | pure spec: the modelled-domain predicate (printable ASCII, 32..126), enforced as a `Requires` clause on both modeled functions |
| `emit_sep / single_part / empty_seq` | (no repo counterpart) | pure spec plumbing: the part-sequence constructors used by the fold |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the class attribute
`pattern = re.compile(r'(-|\+|\^|\s+)')` (`transforms.py:40`), which splits on
EVERY separator occurrence with no flanking requirement.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the keystroke text `node[-1].astext()`) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the result `parts` of `pattern.split(...)` — a `List[str]` of substrings, alternating keystroke / separator / keystroke | `PSeq[PSeq[int]]` (a sequence of code-point sequences) | the `k`-th substring ↔ the `k`-th inner `PSeq`; even indices are keystrokes, odd indices are single-character separator tokens |
| `len(parts) == 1` (the single-part decision) | `len(kparts(...)) == 1` | identity on the part count |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` / `PSeq[PSeq[int]]`.

**Termination (total correctness):** the real split always answers — one
`re.split` pass over a finite string plus a length test is a bounded
computation. The spec carries `Requires(MustTerminate(1))` on
`split_keystrokes` (consumed in the impl loop by `Invariant(MustTerminate(i))`,
with `i` the strictly decreasing, bounded-below measure) and
`Requires(MustTerminate(2))` on `keystroke_is_atomic` (the 2 > 1 measure covers
its call into `split_keystrokes`). Nagini is a partial-correctness verifier by
default, so without the obligation a diverging implementation would satisfy
every `Ensures` vacuously while sharing the spec.

### 2.1 Modelled domain restriction — ENFORCED by `Requires` (recorded for G-AX / G-EQ)

The recognised separators in the real alternation `(-|\+|\^|\s+)` are the three
single characters `- + ^` PLUS a maximal run of whitespace (`\s+`).  The deep
model `kparts` covers the **printable-ASCII domain**: every code point is in
`32..126`.  This restriction is **enforced as a `Requires` clause** on both
modeled functions — `Forall k: 0 <= k < len(text) ⇒ in_domain(text[k])` — NOT
left in prose.  A documented restriction that is not in the precondition is an
unsound spec; here the precondition is the restriction (this is the lesson the
adversarial panel surfaced on the earlier iteration).

The printable-ASCII domain is chosen because the only whitespace code point in
`32..126` is the ordinary space `' '` (32), which matches the engine's `.` in
both lookbehind `(?<=.)` and lookahead `(?=.)`.  All OTHER whitespace code
points — `\t \r \f \v` (9, 11–13), the C0 separators (28–31), and every Unicode
space (≥133) — are excluded by the bound, and the newline `\n` (10) is the one
whitespace code point that does NOT match `.` (so it would trigger an engine
subtlety where a separator adjacent to `\n` is suppressed).  Confining the
domain to `32..126` removes that subtlety entirely, so `kparts` (with blank-run
merging) is exactly the real `re.split` on the WHOLE domain — verified by G-AX
at 0 mismatch over 200 000 fuzz inputs drawn from all of `32..126`.

Crucially this domain **contains every tested keystroke input**: the issue's
reproductions (`-`, `+`, `Shift-+`), both new FAIL_TO_PASS cases
(`:kbd:`Alt+^``, `:kbd:`-``), and — importantly — the blank-run PASS_TO_PASS
case `:kbd:`M-x  M-s`` (printable ASCII, blank run of two spaces).  No
FAIL_TO_PASS or PASS_TO_PASS input falls outside the precondition.  Because the
blank-run branch is now part of the verified `kparts` (the two-space run
collapses into one separator token), a verifying impl MUST reproduce
`['M','-','x','  ','M','-','s']`; an impl that drops the `\s+` branch fails to
verify.  So the guarantee, not merely the gold patch, covers `M-x  M-s`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `kparts` deep model ↔ `re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split` (A-reference)

**Callee:** CPython `re.Pattern.split` applied to the post-patch pattern
`r'(?<=.)(-|\+|\^|\s+)(?=.)'`.  Because the pattern has a single capturing
group, `re.split` returns the text between matches interleaved with the captured
separators (CPython docs: `re.split` — "If capturing parentheses are used in
pattern, then the text of all groups in the pattern are also returned as part of
the resulting list").  Docs: https://docs.python.org/3/library/re.html#re.split.

The lookbehind `(?<=.)` and lookahead `(?=.)` require that a matched separator
have at least one character before AND after it.  Therefore a separator at the
very start or the very end of the text does NOT match and is left attached to
its neighbouring keystroke; an interior separator still matches.  On the
printable-ASCII domain this is exactly the per-code-point rule `kparts` encodes,
for BOTH separator kinds:

  a single character `c ∈ {-,+,^}` at index `i` of a length-`n` text splits  ⟺
  `0 < i < n-1` (and becomes its own one-character separator token; two adjacent
  single separators do NOT merge — an empty keystroke sits between them);

  a blank space at index `i` splits ⟺ `0 < i < n-1`, and a maximal run of such
  flanked spaces collapses into ONE separator token (the greedy `\s+`
  run-merging) — modelled in `kparts` by prepending a flanked space to the
  already-open blank token of the remainder rather than opening a new one.

The maximal runs between split points become keystroke parts (front-recursive in
`kparts`, one unfold per code point).  In particular a lone separator (`-`)
yields a single part, a trailing separator (`Alt+^`) keeps its final `^` as a
keystroke rather than spawning an empty neighbour, and a doubled interior blank
(`M-x  M-s`) yields one two-space separator token, not two.

**Soundness check (G-AX):** `axiom_check.py` constructs the real pattern,
runs `re.split` on 63 boundary inputs (each single separator / blank alone,
doubled, every adjacent pair, the issue's compound examples, leading/trailing
separators, blank-run cases) plus 200 000 randomized fuzz strings drawn from the
WHOLE printable-ASCII domain `32..126` (a 55% bias toward `{- + ^ space}` ∪
ordinary letters, the rest arbitrary printable ASCII, so blank runs and every
branch character are exercised), and asserts `kparts(codepoints, False) ==
re.split(text)` on every one (0 mismatch).  It also confirms the literal
FAIL_TO_PASS / PASS_TO_PASS keystroke strings exactly — `'-' → ['-']`,
`'Alt+^' → ['Alt','+','^']`, and the blank-run `'M-x  M-s' →
['M','-','x','  ','M','-','s']` (now INSIDE the verified guarantee, not a side
sanity sweep).  It imports only the standard-library `re` module — the very
module the patch uses.  Exit 0 iff sound.

There is **no consumed `@ContractOnly` axiom** in this bundle: the only changed
operation (the split) is modelled deeply and checked as an A-reference.
