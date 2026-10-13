# refinement.md — sympy__sympy-16886

The operation-by-operation correspondence between `model.py`'s implementation
(the `encode_morse` and `morse_list` impl regions and the deep `morse_of` /
`encoded_seq` definitions in the `pure` region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed**, the proof uses the axiom's `Ensures`; or **A-reference**, a deep
model validated == the real callee/table by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The modelled unit is the **per-word encoding step**,
`word ↦ sep.join(char_morse[letter] for letter in word)`
(`crypto.py:1574-1580`); mapping.md §1 gives the binding and §2.1 the repository
guard behind every domain restriction.

## A. The behavioural hunk — the Morse table (`sympy/crypto/crypto.py:1523`)

The gold patch changes one entry of the module-level dict `morse_char`:

```
-    "-----": "0", "----": "1",
+    "-----": "0", ".----": "1",
```

`morse_char` maps Morse code strings to characters; the encoder uses its inverse
`char_morse = {v: k for k, v in morse_char.items()}` (`crypto.py:1536`). The
edit therefore changes `char_morse['1']` from `'----'` (four dashes) to
`'.----'` (dot + four dashes), the standard International Morse code for the
digit one. The per-word step of `encode_morse` (`crypto.py:1539`, step at
`:1574-1580`) maps each character `letter` of a word to `mapping[letter]`
(`:1577`) and joins the per-symbol codes by `sep` (`:1580`).

The modelled domain (mapping.md §2) is one word — a possibly-empty plaintext all
of whose symbols the table represents — with an accepted single-character
separator. Every restriction is a real repository guard (mapping.md §2.1): the
deletion of unrepresented characters (`:1570`), the whitespace split (`:1573`)
and the separator assertion (`:1560`). The word join, the trailing-whitespace
suffix and the whitespace normalisation (`:1563`, `:1566`, `:1583`) are outside
the modelled unit and are untouched by any refinement of this model.

| # | model.py impl op | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `msg: List[int]`, every element `represented` | the `word: str` the per-word loop is handed (`crypto.py:1574`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). The element restriction is the deletion at `:1570`, proved mechanically by the recorded-`mapping` check in axiom_check.py (mapping.md §2.1(1)); the absence of whitespace is `msg.split()` at `:1573`. |
| A2 | parameter `sep: int`, required `sep_accepted(sep)` (hence ≠ `dot()`, ≠ `dash()`) | the `sep` argument (default `'|'`) and the guard `assert sep not in mapping` (`crypto.py:1560`) | R | the real encoder REJECTS (raises `AssertionError` on) a separator that is itself a represented plaintext symbol — digit, upper-case letter, punctuation mark (including `'.'`/`'-'`) — or the space character (a mapping key from the second call on, `:1562`). `sep_accepted` spells out that reject set and the precondition keeps rejected separators OUTSIDE the modelled domain, so the model claims a normal return only where the real function returns normally. `'|'` is code point 124, accepted and distinct from both signal code points; `sep.join` ↔ inserting `PSeq(sep)` between symbol codes. |
| A3 | `morse_list(c)` returns `morse_of(c)`, built by 52 ordered conditionals with an empty-list fall-through; in the spec `morse_of` IS the table | the lookup `mapping[letter]` where `mapping == char_morse` (`crypto.py:1577`, `:1559`, `:1536`) | A-reference | the changed operation is a **data table**, modeled DEEPLY: `morse_of` (the spelled-out per-symbol signal sequences in the `pure` region) and the matching `morse_list` impl ARE the table. There is no consumed table axiom — the proof never depends on one. The deep model is validated **== the real `char_morse` on all 52 keys** out-of-band by G-AX (axiom_check.py), which also checks that the model's key set (`represented`) is exactly the real one and that every other code point maps to no signals. |
| A4 | `morse_of(c) == no_signals()` for every unrepresented `c`, and `morse_list` returns `[]` there | such a character never reaches the lookup: it is DELETED by `translate(msg, None, ''.join(chars - ok))` (`crypto.py:1568-1570`), so it contributes nothing to the output | A-reference + I | totality is what leaves no unconstrained branch in `morse_list` (there is no `Requires` on `c`). Its real counterpart is checked both as a set identity and observationally by G-AX: `encode_morse(msg) == encode_morse(msg with its unrepresented characters removed)`. |
| A5 | the join: `result = morse_list(msg[n-1]); ...; result = morse_list(c) + [sep] + result` (backward fold), specified by `encoded_seq(s, sep)` | `morseword.append(mapping[letter])` per symbol (`crypto.py:1577-1578`) then `word = sep.join(morseword)` (`:1580`) | R + I | `sep.join` of the per-symbol codes ↔ `encoded_seq` (codes interleaved with one `PSeq(sep)` between adjacent symbols). The concrete control flow (one code per symbol, separators between) is identical; only the carrier type differs. The backward loop matches the front-recursive `encoded_seq` (a single unfold per step), the canonical fold pattern. |
| A6 | the empty-word case `if n == 0: return []`, specified by `encoded_seq` of the empty sequence being `no_signals()` | `''.join(...)` over an empty `morseword` — reachable only as a WIDENING, since `msg.split()` (`crypto.py:1573`) never yields an empty word | R | a widening of the real input set adds an obligation and removes none (mapping.md §2.1(3)); it is carried so that no implementation has a free branch on the empty input. |

The discriminating content of the change — `'1'` (code point 49) →
`'.----'` rather than `'----'` — lives in `morse_of(49) == PSeq(dot(), dash(),
dash(), dash(), dash())` (model) ⇔ the gold `char_morse['1'] == '.----'`
(real). The pre-patch table mapped `'1'` to `'----'` (four dashes);
`model_prepatch.py` reproduces that (`morse_list` returns four dashes for
`c == 49`) and **fails** the postcondition `ToSeq(Result()) == morse_of(c)` of
`morse_list` — because the frozen-spec `morse_of(49)` is the five-signal
`.----`. That is exactly the spec sensing the change (G-DIFF):

```
model_prepatch.py:339:13:339:43: error: Postcondition of morse_list might not
hold. Assertion (ToSeq(Result()) == morse_of(c)) might not hold.
```

The encoder's postcondition `ToSeq(Result()) == encoded_seq(ToSeq(msg), sep)`
then carries the per-symbol correctness to the whole word: for `'12345'`
the first symbol's code is `morse_of(49) == .----`, so the joined result begins
`.----|...`, matching the F2P expectation; the buggy four-dash code would
produce `----|...` and fail the test.

## B. No second prepatch needed

There is a single independently-fixed behaviour (the Morse code of the digit
`'1'`). One `model_prepatch.py` exercises it, failing on the `morse_list`
postcondition for `c == 49`. The other 51 table entries are unchanged and
correct on both sides of the patch, so they are not separately modeled as fixed
behaviours — but they ARE pinned by the spec (A3), which is what stops an
implementation from carrying a corruption of one of them; properties.py attacks
one entry of each class (letter `'A'`, digit `'0'`, punctuation `'!'`, and an
unrepresented code point).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-symbol Morse table entry for `'1'` — is modeled **deeply**
(the explicit `morse_of` definition in the `pure` region and the matching
`morse_list` impl), not hidden behind an axiom about the thing that changed.
There is **no consumed `@ContractOnly` axiom** in this bundle: the per-word step
calls nothing Nagini cannot express once the table is spelled out, and the
unchanged plumbing is outside the modelled unit (each exclusion licensed by a
repository guard, mapping.md §2.1). The table is the **A-reference** that G-AX
validates the deep model against.

## D. verify(model) ⇒ resolved

`morse_list` verifies only if it returns exactly `morse_of(c)` — for EVERY code
point, since it carries no precondition on `c` (A3, A4). `encode_morse` verifies
only if its result equals the per-symbol codes joined by the separator, for every
word over the represented alphabet including the empty word (A5, A6). Both carry
a `MustTerminate` obligation (mapping.md §2), matching the real step's bounded
single pass: a verifying implementation must actually DELIVER the encoding — a
diverging body cannot discharge the obligation, so the value postconditions
cannot be satisfied vacuously. `Requires/Ensures(Acc(list_pred(msg), 1/2))`
additionally forbids writing to the word being encoded.

So a verifying `model.py`, refined by the map above, yields a patch that differs
from gold in at most (i) the entries of the representation table and (ii) the
body of the per-word encoding step — and the spec pins BOTH exactly:

* the table, on all 52 represented code points *and* on the complement (an
  implementation may neither corrupt an entry nor add one, because
  `morse_of(c) == no_signals()` off the key set and G-AX certifies that key set
  is the real one);
* the per-word step, on every word of represented symbols and every accepted
  separator (`encoded_seq` fixes the codes, their order, and the single
  separator between adjacent symbols).

**The F2P oracle is the whole test function**, so the argument has to cover all
ten of its assertions (`sympy/crypto/tests/test_crypto.py::test_encode_morse`,
the last two added by the test patch):

| # | assertion | how it is decided |
|---|---|---|
| 1 | `encode_morse('ABC') == '.-\|-...\|-.-.'` | one word `'ABC'`, in the modelled domain → pinned |
| 2 | `encode_morse('SMS ') == '...\|--\|...\|\|'` | one word `'SMS'` → pinned; the trailing double separator is the untouched suffix rule (`crypto.py:1563`, `:1583`) |
| 3 | `encode_morse('SMS\n')`, same expectation | as (2) |
| 4 | `encode_morse('') == ''` | **no word at all** (`''.split() == []`): the per-word step never runs, so no refinement of this model can change the result — *and* the empty word is INSIDE the modelled domain, pinned to `no_signals()` by A6, so the coarser reading of `msg` (the whole plaintext) cannot special-case it either. Decided identically under both readings (§E) |
| 5 | `encode_morse(' ') == '\|\|'` | as (4) — `' '.split() == []`; the space never reaches the modelled step (`:1573`), the one narrowing for which the binding is load-bearing (§E) |
| 6 | `encode_morse(' ', sep=<backquote>)` == two backquotes | as (5) |
| 7 | `encode_morse(' ', sep=<two backquotes>)` == four backquotes | as (5); also the only call with a multi-character separator, the one declared residual narrowing (mapping.md §2) — and it has no word, so the narrowing is unreachable |
| 8 | `encode_morse('!@#$%^&*()_+') == '-.-.--\|.--.-.\|...-..-\|-.--.\|-.--.-\|..--.-\|.-.-.'` | one word `'!@$()_+'` after the deletion at `:1570`, in the modelled domain → pinned (and the deletion itself is pinned by A4: a rival that gives `'#'`, `'%'`, `'^'`, `'&'` or `'*'` a representation is refuted) |
| 9 | `encode_morse('12345') == '.----\|..---\|...--\|....-\|.....'` | one word, in the modelled domain → pinned; the discriminating assertion |
| 10 | `encode_morse('67890') == '-....\|--...\|---..\|----.\|-----'` | one word, in the modelled domain → pinned |

Six of the ten assertions are inside the modelled domain and are therefore fixed
by the postconditions; the other four encode a message with **no words**, so the
step this model binds never executes for them and they are decided by
plumbing no refinement of this model touches. Measured at `base_commit`: only
assertion 9 fails, and it is the one the gold table entry flips; with the gold
patch all ten pass. (Measured for contrast: a table whose `'A'` entry is
corrupted to `'--'` fails assertion 1 alone while both digit assertions pass —
which is why the spec pins the letter branches too.)

`PASS_TO_PASS` is likewise safe: it is decided by the same table (and its
inverse `morse_char`, which `decode_morse` consumes) plus untouched code. Since
`char_morse` is a bijection and the spec pins it entry for entry, a verifying
implementation's table IS the gold table, hence so is its inverse.

By R (`str` ↔ `List[int]`, `'.'/'-'/'|'` ↔ their code points, `sep.join` ↔ the
`encoded_seq` interleave) the verified step equals the gold per-word step on
every input the repository can hand it; by G-AX the deep model `morse_of` equals
the real post-patch `char_morse` table (A-reference) and the real `encode_morse`
produces the exact F2P strings. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited table
— and the gold patch resolves (G-RESOLVE). The only trust point is refinement
fidelity (this document, G-EQ) plus the table-soundness check (G-AX); there is
no consumed-axiom trust point.

## E. The refinement rule, and every input the domain excludes

A precondition always leaves branches that verify without being constrained, so
"verify ⇒ resolve" needs a statement of **where an implementation branch lands
in the repository** and **what the repository does with each excluded input**.
Both are fixed here; neither is left to taste.

### E.1 Which repository site an impl region refines to

`model.py` has exactly two impl regions, and mapping.md §1 binds each to one
repository site:

* a branch in **`morse_list`'s impl region** refines to an **entry of the table**
  `char_morse` (`crypto.py:1536`, consumed at `:1577`) — e.g. the gold patch
  itself, and e.g. `char_morse['%'] = '..'`. This region has **no excluded
  input at all**: `morse_list` carries no `Requires` on `c` and `morse_of` is
  total on `int` (A3, A4), so every code point of the whole space is pinned. A
  rival that corrupts an entry, or adds one, is refuted by the verifier — for a
  letter (`rival-dead-branch-letter-A`), a digit (`rival-wrong-digit0`,
  `rival-prepatch-digit1-four-dash`), a punctuation mark
  (`rival-wrong-punctuation-bang`) or a code point the table must NOT represent
  (`rival-unrepresented-emits-signals`); all four are battery cases in
  properties.py.
* a branch in **`encode_morse`'s impl region** refines to a statement **inside
  the per-word loop body** (`crypto.py:1575-1580`) — the unit this model binds.
  It does **not** refine to a guard at the top of the repository function
  `encode_morse` (`:1539`): that function's parameter is the whole plaintext,
  which is not this model's `msg` (mapping.md §1, §2 row 1; `meta.json`
  `modeled_functions[0].repo_location`; the "Modelled domain" paragraph of
  model.py's docstring). Nor may a refinement edit `:1560-1573` or `:1583` at
  all — no model symbol binds there.

Consequently the plumbing that decides assertions 4-7 is not defended by the
claim that it is "the identity on these inputs" (it is not, for a message with
whitespace); it is defended by being **outside the refined patch**.

### E.2 The excluded inputs, and the guard behind each

| excluded input | model restriction | repository guard making it unreachable in the per-word loop | mechanical evidence |
|---|---|---|---|
| a word symbol that is whitespace (code points 9, 10, 11, 12, 13, 32) | the `represented(msg[k])` `Forall` | `words = msg.split()` (`:1573`); `str.split()` with no argument never yields a piece containing whitespace, so `mapping[' ']` — the key installed by `mapping[" "] = word_sep` at `:1562` — is never looked up, and `'\t'`, `'\n'` are not keys at all (the lookup would raise `KeyError`) | G-AX A-reference 4: a recording `dict` subclass passed as `mapping=` shows every key the real encoder looks up is non-whitespace, over a 17-message corpus containing runs of `' '`, `'\t'`, `'\n'` |
| a word symbol that is not represented and not whitespace (`'#'` 35, `'%'` 37, `'&'` 38, `'*'` 42, `'^'` 94, lower case, …) | the same `Forall` | `msg = translate(msg, None, ''.join(chars - ok))` (`:1568-1570`) DELETES it before any word is formed | G-AX A-reference 4 (every recorded key is represented) and the observational deletion check in A-reference 2 |
| a rejected separator (a represented character, or `' '` from the second call on) | `Requires(sep_accepted(sep))` | `assert sep not in mapping` (`:1560`) RAISES before the loop is reached, so the real function has no normal return to disagree with | G-AX A-reference 3: set identity over all 128 ASCII code points plus the observed `AssertionError` |
| a multi-character separator | `sep: int` | no `int`-valued expression of a model implementation can tell `'|'` from `'||'`; declared residual narrowing (mapping.md §2) | the only two F2P calls that pass one have an empty word list (§D rows 6-7) |

**Measured, not argued.** The residual is real on both sides and both sides were
measured. A same-spec implementation carrying the space-keyed dead branch
(`if n >= 1 and msg[0] == 32: return [dot()]` at the head of `encode_morse`'s
impl region; `same_spec` True) DOES verify against this spec — measured, 104.9s
— because the precondition makes its guard infeasible. What that branch cannot
do is change the repository: the refinements were built and run. Each tree is
`base_commit` + the gold patch, plus the refined guard(s) inside the per-word
loop; every tree was fingerprinted over one seeded corpus of 100 033
`(plaintext, separator)` pairs drawn from represented symbols, runs of
whitespace, unrepresented characters, the empty plaintext, rejected separators
and multi-character separators (a `sha256` over
`(msg, sep, result-or-exception)`, so a raise is compared too):

| tree | inserted at `crypto.py:1574` | fingerprint |
|---|---|---|
| gold | nothing | `46d30c57a9284375…` |
| the space-keyed dead branch, refined | `if len(word) >= 1 and word[0] == ' ': morsestring.append('.'); continue` | `46d30c57a9284375…` — **identical** |
| all three residual classes at once | the same, plus `word[0] == '%'` and `sep == 'A'` guards | `46d30c57a9284375…` — **identical** |
| pre-patch table (`'1'` → `'----'`) | nothing | `5760019b76845da9…` — differs |
| `char_morse['A']` corrupted to `'--'` | nothing | `e3617f25d31afe5a…` — differs |

Both refined trees also pass `test_encode_morse` 10/10 assertion by assertion
and `test_decode_morse`. The fingerprint separates gold from both table
corruptions, so the identity above is a measurement with a live control, not a
tautology.

A branch of `encode_morse`'s impl region whose guard only an excluded input can
satisfy therefore refines to a statement of the loop body that **no repository
execution reaches**: the patched repository is behaviourally identical to gold,
so the patch resolves. The criterion is the one the previous audit of this cell
applied to the separator narrowing and accepted — *the excluded input never
reaches the modelled unit* — evaluated at the modelled unit rather than at the
enclosing function, and certified by G-AX A-reference 4 instead of by reading
the surrounding code.

### E.3 What was brought inside the domain rather than defended

Two boundaries are NOT defended by reachability, because a coarser reading of
`msg` could exploit them. They are inside the domain and pinned:

* **the empty input.** `Requires(len(msg) >= 1)` and the matching
  `Ensures(len(ToSeq(msg)) >= 1)` are gone; the empty word is pinned to
  `no_signals()` (A6), so an implementation that special-cases it is refuted
  (`rival-empty-word-emits-signals`).
* **every non-digit table entry.** `Requires(48 <= c and c <= 57)` on
  `morse_list` is gone; `morse_of` is total, so an implementation that
  special-cases a letter, a punctuation mark, or an unrepresented code point is
  refuted (E.1).

Both changes only *remove* a precondition and *widen* a pinned domain — no
obligation of the previous spec was dropped or weakened (mapping.md §2.1(3) for
the widening's licence).

### E.4 If the reader binds `msg` to the whole plaintext anyway

The two readings **agree on the modelled domain**: on a possibly-empty word of
represented code points with an accepted single-character separator the
surrounding pass is the identity, and G-CONF measures exactly that — the shadow
of this model's impl equals the real *top-level* `encode_morse` on 102 664
inputs (2 664 boundary + 100 000 fuzz, seed 16886), and disagrees on both
corrupted tables. They differ only in where an off-domain branch lands, which
is what E.1 settles. Under the coarser reading the whitespace row of E.2 would
be the one exploitable narrowing left, which is why the binding is stated in
four places (mapping.md §1, `meta.json` `modeled_functions`, model.py's
docstring, and E.1) and why the whitespace-free-ness of a word is proved
mechanically in G-AX rather than asserted.

### E.5 A table-*key* patch is not the refinement of an off-domain branch

`morse_of` is total on `int` (E.3): on an unrepresented code point it yields
`no_signals()`, so an impl-region branch such as `if c == 37: return []`
(`'%'`) verifies. Two repository edits can be proposed as that branch's
refinement, and only one of them is one.

1. A guard inside the per-word loop (`crypto.py:1573`ff) keyed on the symbol
   `'%'`. It is unreachable: `'%'` is not a key of `char_morse`, so it is
   removed from the plaintext at `crypto.py:1570` before the loop runs, and the
   patch is a no-op. Measured, not argued: the G-EQ role of 2026-08-16 resolved
   exactly this patch, `resolved=True`
   (`atk_9_dead_branch_word_percent`; `atk_13_explicit_empty_branch_pct` in the
   role before it).

2. `char_morse["%"] = ""` -- adding a *key* to the table. This is not a
   refinement of the branch. The key set of `char_morse` is itself modelled, by
   `represented` in the pure region, and the spec regions are frozen for an
   attack (`same_spec`), so no admissible impl can move it. Both A-reference
   legs reject that tree, measured on a worktree carrying gold + this line:

   - `axiom_check.py` (G-AX) stops at `check_table` with
     `AssertionError: real char_morse has 53 entries, the deep model spells out
     52`, before `check_totality`'s `model_keys == real_keys` over the whole
     code space is even reached;
   - `conformance_check.py` (G-CONF) stops with `AssertionError` raised by the
     real encoder at `assert sep not in mapping` (`crypto.py:1560`) for
     `sep='%'` -- a separator this model accepts, `sep_accepted(37)` -- so the
     on-domain equality G-CONF measures is lost as well.

   Its oracle outcome (`resolved=False`, FAIL_TO_PASS `test_encode_morse`) is
   therefore a statement about an unfaithful patch and not about this spec. An
   unrepresented code point contributes no signals *because it is deleted*
   (A-reference 2, `check_deletion`), not because it carries an empty code.
