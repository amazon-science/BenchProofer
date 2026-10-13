# mapping.md — sympy__sympy-20916

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 82298df6a51491bfaad0c6d1980e7e3ca808ae93`, states the type
abstraction, and gives the provenance of each kind-A reference (callee source +
the exact behaviour it encodes).

Repo file under change: `sympy/printing/conventions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `split_trailing_digits(name)` | the trailing-digit exception block of `split_super_sub(text)` — `sympy/printing/conventions.py:63-68` (the `m = _name_with_digits_p.match(name); if m: name, sub = m.groups(); subs.insert(0, sub)` step), together with the module-level pattern `_name_with_digits_p` at `sympy/printing/conventions.py:10` | the modeled changed behaviour: peel a trailing digit run off the parsed name into a subscript |
| `is_letter(c)` *(A-reference)* | the regex class `[^\W\d_]` (the first capture group of `_name_with_digits_p`), evaluated by the stdlib `re` engine under `re.U` | unchanged per-code-point primitive: is `c` a Unicode letter (word char, not a decimal digit, not underscore)? Validated == real `re` by axiom_check.py (G-AX) |
| `is_digit(c)` *(A-reference)* | the regex class `\d` (the second capture group of `_name_with_digits_p`), evaluated by the stdlib `re` engine under `re.U` | unchanged per-code-point primitive: is `c` a Unicode decimal digit? Validated == real `re` by axiom_check.py (G-AX) |
| `core_len(s)` | the `$` anchor of `_name_with_digits_p` under non-`MULTILINE` matching (`sympy/printing/conventions.py:10`): `$` matches at end-of-string OR immediately before a single terminating `'\n'` | pure spec: the length of the name proper, i.e. `name` with one terminating line feed set aside. Unchanged by the gold patch (the `$` anchor is identical pre- and post-patch) |
| `num_leading_letters(s)`, `all_digits(s)`, `splits(s)`, `split_point(s)`, `digit_run(s)` | the recognise/split decision computed by `_name_with_digits_p.match(name).groups()` | pure spec: the deep model of the regex match (greedy letter prefix, all-digit suffix, `$` tolerating one terminating line feed) — the CHANGED behaviour, modeled deeply |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the module-level pattern
`_name_with_digits_p = re.compile(r'^([a-zA-Z]+)([0-9]+)$')`
(`sympy/printing/conventions.py:10`), an ASCII-only `[a-zA-Z]+`/`[0-9]+`
recogniser, changed to `re.compile(r'^([^\W\d_]+)(\d+)$', re.U)`.

The unchanged surrounding code of `split_super_sub` — the `while` loop that
splits the symbol text into the leading `name` and the explicit `^`/`_`/`__`
super-/subscript parts (`conventions.py:35-61`), and the `subs.insert(0, sub)`
list insertion (`conventions.py:68`) — is identical pre- and post-patch and is
NOT where the bug lives; it is therefore not re-modeled. The model's input
`name` is exactly the `name` local that loop produces (the symbol text left of
any explicit script marker); the model's `Result()` is the post-exception bare
`name`, and the peeled `drop(split_point)` digit run is the `sub` inserted at
`subs[0]`. See refinement.md for the operation-by-operation correspondence.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `name` local; the regex groups `name`/`sub`) | `List[int]` of Unicode code points | `s[k]` ↔ `name[k] == ord(s[k])`; `len(s)` ↔ `len(name)`; `str` slice `name[:p]`/`name[p:]` ↔ list/`PSeq` `take(p)`/`drop(p)`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `take`/`drop`/`len`/`[i]` mirror `str` slice/`len`/index |
| `re` match `_name_with_digits_p.match(name)` returning a 2-group match or `None` | the pure `splits(s)` (match succeeds) + `split_point(s)` (the group boundary) + `digit_run(s)` (group 2) | `match is not None` ↔ `splits(ToSeq(name))`; `m.group(1)` ↔ `take(split_point)`; `m.group(2)` ↔ `digit_run` = `take(core_len).drop(split_point)`. Note group 2 is bounded by `core_len`, NOT by `len`: the `$` anchor lets the match succeed with one terminating `'\n'` left over, and that line feed is in neither group |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Reference provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `is_letter` / `is_digit` per-code-point classes (A-reference)
**Callee:** the standard-library `re` engine evaluating, under `re.U`, the two
character classes the patched pattern is built from:

* `is_letter(c)`  ↔  the class `[^\W\d_]` — a single word character that is
  neither a decimal digit nor underscore, i.e. a Unicode letter.
* `is_digit(c)`   ↔  the class `\d` — a single Unicode decimal digit.

These are the per-code-point primitives the operation rests on; they did NOT
change in meaning between the pre- and post-patch regex *as character classes*
— what changed is that the recogniser now USES the Unicode classes
(`[^\W\d_]`, `\d` with `re.U`) instead of the ASCII subsets (`[a-zA-Z]`,
`[0-9]`). model.py models the per-code-point classification as `@Pure
@ContractOnly` axioms (with only the consumed disjointness clause
`is_letter(c) ⇒ ¬is_digit(c)`) and models the recognise/split DECISION deeply.

**Flag dependency:** the classes are evaluated with `re.U` (Unicode matching),
which is the patched call's mode (`re.compile(..., re.U)`) and is also the
default for `str` patterns on Python 3. axiom_check.py compiles with `re.U`
explicitly so G-AX fuzzes the correct configuration. Docs:
https://docs.python.org/3/library/re.html#index-31 (`\w`, `\d`, the `re.U`
flag, and the Unicode-property semantics of `\d`/`\w`).

### 3.2 The recognise/split decision (A-reference, deep model)
**Callee:** the compiled pattern
`_name_with_digits_p = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)` and its
`.match(name).groups()`. The CHANGED behaviour — recognise a non-empty leading
run of Unicode letters followed by a non-empty run of Unicode decimal digits,
and split there — is modeled **deeply** by `splits` / `split_point` over the
per-code-point classes (there is no consumed axiom about the whole regex).
Because the letter and digit classes are **disjoint** (the consumed axiom
clause, validated in §3.1), the greedy first group `[^\W\d_]+` and the second
group `\d+` meet at exactly the end of the leading-letter run: the match
succeeds iff that run is non-empty, does not consume the whole **name proper**,
and the remainder of the name proper is wholly digits — which is exactly
`splits`, and the boundary is `split_point = num_leading_letters`.

The **name proper** is `core_len`'s subject, and it is where the `$` anchor
lives. Under non-`MULTILINE` matching Python's `$` matches at end-of-string OR
immediately before a single terminating `'\n'`
(https://docs.python.org/3/library/re.html#regular-expression-syntax, `$`), so
`\d+$` accepts a digit run followed by at most one line feed, and that line
feed lands in NEITHER group. Hence `core_len(s)` sets aside exactly one
terminating line feed and the whole decision is taken on `s.take(core_len(s))`,
with `m.group(2) = digit_run(s) = s.take(core_len(s)).drop(split_point(s))`.
Exactly one is set aside: `'\n\n'` leaves a non-digit `'\n'` inside the name
proper, so the match fails, and no other code point (`'\r'` included) is
tolerated. This `$` behaviour is **unchanged** by the gold patch — the anchor is
identical in the pre- and post-patch pattern — so it is not the discriminator;
it is a property of the recogniser the model must nonetheless get right to be
faithful. Verified against the real engine: `.match("w1\n").groups() == ('w',
'1')` while `.match("w1\n\n")` and `.match("w1\r")` are both `None`.

**Soundness check (G-AX):** `axiom_check.py` runs the real `re` engine:
(a) over an exhaustive Basic-Multilingual-Plane sweep plus the astral
mathematical-digit blocks (≈ 65 792 code points) it asserts the disjointness
axiom `is_letter ⇒ ¬is_digit` holds for the real classes; (b) over 35 boundary
names (the F2P cases incl. Greek + astral-digit examples, plus structural edge
cases) and 60 000 randomized fuzz names drawn from a mixed
letter/digit/other/astral alphabet, it asserts the deep model
(`splits` / `split_point`) reproduces the real compiled regex's match /
`groups()` split exactly. It imports only the standard-library `re` module —
the very module the patched code uses. Exit 0 iff sound.

## G-CONF (differential conformance: MODEL vs the REAL patched repo code)

`conformance_check.py` embeds the `# impl-start` / `# impl-end` region of
`model.py` verbatim (only the contract calls `Requires` / `Ensures` /
`Invariant` / `Assert` / `Acc` / `MustTerminate` and the
`# invariants-start`/`-end` markers deleted), together with the four `@Pure`
helpers of the `# pure-start` region (`num_leading_letters`, `all_digits`,
`splits`, `split_point`) stripped the same way. `PSeq[int]` is realized by an
immutable-tuple shim (`len`/`[]`/`==`/`take`/`drop`/`+`) and `ToSeq` materializes
one.

**Oracle (called, not reimplemented):** the real gold-patched
`sympy/printing/conventions.py` — the module pattern `_name_with_digits_p`
(`conventions.py:10`, the gold-patched line) driven as `.match(name)` /
`.groups()`, and its consumer `split_super_sub` (`conventions.py:13`) driven
end-to-end on separator-free names. The script hard-errors if the loaded
`_name_with_digits_p.pattern` is not the post-patch pattern, so a patch-apply
failure cannot be mistaken for agreement. The two `@ContractOnly` axioms
`is_letter` / `is_digit` call the real `re` engine on the character classes
EXTRACTED at run time from the real patched pattern's own group bodies
(`[^\W\d_]`, `\d` under `re.U`), so §3.1's axioms are exercised, not assumed.

**Type bridge (§2, inverted):** `str` ↔ `List[int]` of Unicode code points via
`[ord(ch) for ch in s]` / `"".join(chr(c) for c in cps)`; `s[:p]`/`s[p:]` ↔
`take(p)`/`drop(p)`. Generation happens on the `str` side, so every input is a
genuine code-point list and satisfies the model's `Requires` (`Acc(list_pred,
1/2)` + `MustTerminate`, i.e. any int list, read-only).

**Inputs:** 100 059 Requires-satisfying names — 59 boundary (empty, singletons,
every `test_super_sub` FAIL_TO_PASS name, each impl branch, multi-script
letters/digits, word-but-not-decimal code points, and the `$`-anchor probes)
plus 100 000 seeded fuzz names of length 0..7. **Pinned seed: `SEED = 20916`.**
The shadow records which of its ten branches were taken and the check fails if
any went unexercised (all ten are reached, the terminating-line-feed arm
`lf_set_aside` among them).

**History — the `$`-anchor faithfulness defect, and its repair.** An earlier
revision of this bundle modeled the recogniser with no notion of the name
proper: `splits` required `all_digits(s.drop(num_leading_letters(s)))` over the
WHOLE sequence. That diverged from the real patched code on names ending in
exactly one line feed. On `name = "w1\n"` the real patched pattern matches with
`groups() == ('w', '1')` and the real `split_super_sub("w1\n")` returns
`('w', [], ['1'])`, because Python's non-`MULTILINE` `$` also matches just
before a single terminating newline; the old model computed
`all_digits(['1', '\n']) == False`, hence `splits("w1\n") == False`, and the
no-split postcondition forced the name back unchanged. G-PANEL-2 and G-CONF both
recorded that as a fail (meta.json, `agent_verdict: UNFAITHFUL`).

The repair is the `core_len` / `digit_run` pair now in the `# pure-start` region
and the `m` bound in the impl: the decision is taken on the name proper and the
peeled group-2 run is bounded by `core_len`, which is what §3.2 shows the real
`$` anchor to do. The input domain was deliberately NOT narrowed to route around
the witness — `Requires` still admits any code-point list, `Symbol("w1\n")`
still reaches `split_super_sub`, and the shadow still generates `'\n'` — the
MODEL was corrected to compute the real function. The sibling bundles encode the
same rule independently (`lean`'s shadow admits `trailer == "" or trailer ==
"\n"`, `velvet`'s has an explicit `stripFinalNewline` step), which corroborates
the direction of the fix. Note this `$` behaviour is identical pre- and
post-patch, so correcting it does not touch the ASCII→any-script discriminator:
`model_prepatch.py` still fails postcondition P1 on a Greek-letter name with a
trailing digit.
