# refinement.md — sympy__sympy-20916

The operation-by-operation correspondence between `model.py`'s implementation
(the `split_trailing_digits` impl region, the deep `splits` / `split_point`
model, and the `is_letter` / `is_digit` classification axioms) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (kind-A
callee — split into **A-consumed**, where the proof uses the axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — the trailing-digit exception of `split_super_sub`

Gold hunk (`sympy/printing/conventions.py:10`):
```
- _name_with_digits_p = re.compile(r'^([a-zA-Z]+)([0-9]+)$')
+ _name_with_digits_p = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)
```
plus a comment-capitalisation hunk at `conventions.py:63` (a no-op for
behaviour). The recogniser is consumed at `conventions.py:65-68`:
```
m = _name_with_digits_p.match(name)
if m:
    name, sub = m.groups()
    subs.insert(0, sub)
```

| # | model.py impl op (`split_trailing_digits`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name: List[int]` | the `name` local of `split_super_sub` (a `str`) passed to `_name_with_digits_p.match` | R | `str` ↔ `List[int]` of code points (mapping.md §2). |
| A2 | the leading-letter scan `while k < n and is_letter(name[k])` computing `num_leading_letters` | the greedy first group `[^\W\d_]+` of the patched regex | A-reference | the per-code-point letter class `[^\W\d_]` (under `re.U`) is modeled by the `is_letter` axiom; the greedy `+` over it is modeled deeply by `num_leading_letters` (mapping.md §3.1, §3.2). G-AX validates `is_letter` == the real class and `split_point` == the real group-1 boundary. |
| A2b | the name-proper bound `m = n; if n≥1 and name[n-1]==10: m = n-1`, i.e. `m == core_len(name)` | the anchoring `$` of the patched regex under non-`MULTILINE` matching: `$` matches at end-of-string OR just before a single terminating `'\n'` | A-reference | Python's `$` tolerates exactly one terminating line feed, which lands in neither capture group (mapping.md §3.2, with the docs link). `core_len` sets aside exactly that one code point; a second `'\n'`, or a `'\r'`, stays inside the name proper and defeats the match. UNCHANGED by the gold patch (the anchor is byte-identical pre- and post-patch). G-AX/G-CONF validate the decision == the real regex on `'\n'`-bearing names. |
| A3 | the all-digit tail check `while j<m …: if not is_digit(name[j]): bad` computing `all_digits(take(m).drop(k))` | the second group `\d+` of the patched regex, bounded by the anchoring `$` (the rest of the name PROPER must be wholly digits) | A-reference | the decimal-digit class `\d` (under `re.U`) is modeled by the `is_digit` axiom; the deep `all_digits` fold over `take(core_len)` models the `\d+$` suffix, the `$` per A2b. G-AX validates `is_digit` == the real class and the whole `splits`/`groups()` split == the real regex. |
| A4 | `matched = splits(ToSeq(name))` (the conjunction `k≥1 ∧ k<core_len ∧ all_digits(take(core_len).drop k)`) | `m = _name_with_digits_p.match(name)` succeeding (`m is not None`) | A-reference + I | the match succeeds iff the deep `splits` holds (mapping.md §3.2). The `k≥1`, `k<m`, conjunction control flow is identical (I); the predicate content is the A-reference deep model. |
| A5 | when `matched`: `Result()` is built as `take(split_point)`; the peeled `digit_run = take(core_len).drop(split_point)` is `len ≥ 1 ∧ all_digits` | `name, sub = m.groups()` (group 1 → new bare name, group 2 → `sub`) | R + A-reference | `m.group(1)` ↔ `take(split_point)` and `m.group(2)` ↔ `digit_run` under the `str`↔`List[int]` bijection (mapping.md §2). Group 2 is bounded by `core_len`, not `len`, because the `$`-tolerated line feed is captured by neither group (A2b). The split point is the A-reference boundary (A2). |
| A6 | when not `matched`: `Result() == ToSeq(name)` (name returned unchanged, no subscript) | `if m:` is false → `name` is left as is and no `subs.insert` happens | I | the no-match branch leaves the name and subscript list untouched. |
| A7 | (no node — `subs` is not modeled) | `subs.insert(0, sub)` | I | a plain list insertion of the peeled digit run at position 0 of the subscripts; identical pre- and post-patch (the *content* `sub` is the only thing that changed, and that is fully captured by A5's `drop(split_point)`). The surrounding `split_super_sub` while-loop that produces `name`/`supers`/`subs` is unchanged (mapping.md §1) and is not re-modeled. |

The discriminating content of the change — recognising letters/digits by the
**Unicode** classes (`[^\W\d_]`, `\d` + `re.U`) rather than the **ASCII**
subsets (`[a-zA-Z]`, `[0-9]`) — lives in the `is_letter` / `is_digit` axioms
(Unicode semantics) consumed by the deep `splits` model. The pre-patch regex
matched only ASCII letters/digits; `model_prepatch.py` reproduces that (the
impl recognises runs with the explicit ASCII ranges `65..90/97..122` for
letters and `48..57` for digits) and **fails** the postcondition
`Implies(splits(name), ToSeq(Result()) == take(split_point))`, which is exactly
the spec sensing the change (G-DIFF): for a name like a Greek omega followed by
a digit, `splits` is True under the Unicode spec but the ASCII impl leaves the
name unsplit.

## B. No A-consumed whole-callee axiom; the one consumed axiom clause

There is **no** consumed `@ContractOnly` axiom about the *whole* regex match —
the changed recogniser is modeled **deeply** (`splits` / `split_point` spelled
out over the per-code-point classes), an **A-reference** validated by G-AX. The
only thing the proof CONSUMES from the kind-A layer is the single disjointness
clause on the classification axioms:

| # | model.py construct | patch.diff fact | tag | justification |
|---|---|---|---|---|
| B1 | `is_letter`'s `Ensures(Implies(Result(), not is_digit(c)))` | the regex classes `[^\W\d_]` and `\d` are disjoint (a Unicode letter is never a decimal digit) | A-consumed | the deep `splits` proof needs that the greedy letter group and the digit group cannot overlap, so the split boundary `split_point = num_leading_letters` is well-defined. This single clause is the weakest fact the proof consumes; G-AX validates it over ≈ 65 792 code points (mapping.md §3.1). |

`is_letter` and `is_digit` are otherwise A-**reference** (their per-code-point
extension is checked == the real `re` classes by axiom_check.py), not consumed
beyond B1. They are `@Pure @ContractOnly` because they appear inside the
`Ensures`/`Invariant` measures of the pure folds.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
the recogniser switching from ASCII to Unicode letter/digit classes — is
modeled **deeply** (the spelled-out per-code-point folds `num_leading_letters`
/ `all_digits` / `splits` consumed in `split_trailing_digits`, steps A2–A5, an
**A-reference**), not hidden behind an axiom about the function under change.
The `$`-anchor rule of A2b (`core_len` / `digit_run`) is modeled deeply for the
same reason, but it is an **unchanged** property of the recogniser: both the pre-
and the post-patch pattern end in `$`, so `model_prepatch.py` carries the same
`core_len` bound and still fails P1 on the ASCII-vs-any-script discriminator.
The only A-consumed fact is the disjointness clause B1 on the *unchanged*
per-code-point classes. The whole regex match appears only as the
**A-reference** that G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`split_trailing_digits` verifies only if its output is the exact deep split:
the bare name is the maximal leading run of Unicode letters and the peeled
subscript is the trailing run of Unicode decimal digits WITHIN the name proper
(the input with one `$`-tolerated terminating line feed set aside, A2b), applied
iff such a non-empty/non-empty split exists (A2–A6). By R (`str` ↔ `List[int]`,
slice ↔ `take`/`drop`, `m.group(i)`) the verified split equals
`_name_with_digits_p.match(name).groups()` of the patched regex on the tested
inputs; by G-AX the deep model `splits`/`split_point` equals the real `re`
recogniser (A-reference) and the disjointness clause holds for the real classes
(A-consumed B1). The unchanged `subs.insert(0, sub)` (A7) and the unchanged
`split_super_sub` parsing loop carry the peeled run into the subscript list
exactly as before. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited classes — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ).
