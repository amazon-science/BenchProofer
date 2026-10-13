# refinement.md — astropy__astropy-14598

Maps every operation in `recoverSegmentText`'s `do` block to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op). Every step is R, A, or I; no kind-3
(changed inexpressible op).

## Modeled function: `Card._split` — the per-field value recovery (BOTH gold hunks)

The modeled `method` takes the per-field `vc` (the bookended, column-width-padded
record content, `m`'s subject) and produces the recovered per-field value. It
composes BOTH gold hunks:

Post-patch repo code:
```python
# card.py:67,69  (hunk 2 — which `'` CLOSES the content; how `value`'s span is chosen)
_strg = r"\'(?P<strg>([ -~]+?|\'\'|) *?)\'(?=$|/| )"
_strg_comment_RE = re.compile(f"({_strg})? *{_comm_field}?$")   # gained a trailing `$`
...
# card.py:858-865  (hunk 1 — the per-field recovery)
m = self._strg_comment_RE.match(vc)        # vc        -> method input `field`
if not m:
    return kw, vc                          # nothing appended -> `out = none`
value = m.group("strg") or ""              # captured content of `field`
value = value.rstrip()                     # was: .rstrip().replace("''", "'")
if value and value[-1] == "&":
    value = value[:-1]
values.append(value)                       # -> method output `out = some …`
```

Lean impl (`recoverSegmentText`, `impl` region):
```lean
let out : Option (List Char) :=
  (recordContent field).map (fun content =>
    let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse
    if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)
return out
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `field : List Char` (method input) | `vc` — the record content the recovery parses, in ANY shape `_itersubcards()` produces | **R** | `str` ↔ `List Char` per code point, over the WHOLE `str` domain (mapping.md). No domain restriction: the method has no `require`, and none is assumed — the reader API accepts arbitrary card text, so `vc` may carry characters outside `[ -~]` and the model answers those inputs as the real callee does rather than excluding them. |
| 2 | `recordContent field` (via `closesContent` / `onlyPaddingThenAnnotation` / `isContentChar` / `firstPrefix`) | `m = _strg_comment_RE.match(vc)`; `none` = `not m` (the early `return kw, vc`), else `value = m.group("strg") or ""` — with the **post-patch anchored** regex (hunk 2) | **R** | Under the trailing `$` the whole of `vc` must be consumed, so the `_strg` lookahead `(?=$\|/\| )` accepts as CLOSING only the `'` past which nothing but ` *` padding and at most the `/`-introduced comment field remains — that is `closesContent`/`onlyPaddingThenAnnotation`. Python's `$` also matches immediately before a SINGLE trailing newline (`re` semantics, no `MULTILINE`), which is the `breakCh` disjunct. The non-greedy body `([ -~]+?\|\'\'\|)` takes the SHORTEST such content and cannot cross a character outside `[ -~]` — that is `firstPrefix` together with its `isContentChar` guard, so a `vc` such as `"'<TAB>'"` takes the `if not m` early return exactly as the real code does. Validated == the real post-patch `_strg_comment_RE` + the `if not m` guard over ≈1.14×10⁵ inputs by conformance_check.py, `/`-bearing, malformed AND non-`[ -~]`-bearing segments INCLUDED (the oracle quotes the real regex; both sides total, nothing skipped), and over a further 2.5×10⁶ inputs of an offline exhaustive+random sweep with 0 divergences. The UNanchored regex (pre-patch) instead accepts ANY `'` followed by a space or `/`, and always matches — modeled by its ABSENCE here and its PRESENCE (`closesEarly`/`contentEarly`) in `Solution_prepatch_2.lean`. |
| 3 | `let trimmed := (body.reverse.dropWhile (· = spaceCh)).reverse` | `value = value.rstrip()` — **hunk 1: removing the trailing `.replace("''", "'")`** | **R** | `str.rstrip()` (no arg) drops trailing whitespace; `dropWhile (· = ' ')` from the end drops only spaces. They agree because step 2 can only ever yield a content of `[ -~]` characters (a consequence of the `isContentChar` guard, brute-force confirmed over 126766 `some`-answering inputs whose alphabet includes TAB/CR/LF/VT/FF), and the only whitespace in `[ -~]` is `' '` — so no domain restriction is being assumed to make this step line up. The deleted `.replace` is the discriminating change, modeled by its ABSENCE here and its PRESENCE (`collapseDoubledQuotes`) in `Solution_prepatch.lean`. |
| 4 | `if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed` | `if value and value[-1] == "&": value = value[:-1]` | **I** | strip a single trailing continuation marker `&` when present. Unchanged from pre-patch. |
| 5 | `return out` (`Option (List Char)`) | `values.append(value)` on the matching path; the early `return kw, vc` — where NO value is appended — on the non-matching one | **R** | `some` ↔ the per-field recovered value appended; `none` ↔ the early return, where the real code produces no per-field value at all. Reassembly (`''.join(values)`) and the single downstream whole-value `''`-collapse are the unchanged surrounding code and not part of this modeled op. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow (capture + rstrip + `&`-trim)
against the real post-patch regex + recovery over ≥1×10⁵ fuzzed fields.
`axiom_check.py` has no callee to validate (no axioms / no A-reference).

## The two modeled fixed behaviors (two prepatches)

The gold patch fixes TWO independently-observable behaviors of the per-field
recovery; one prepatch per behavior (SPEC_GUIDE §3, G-DIFF).

| prepatch | bug modeled (impl-only) | discriminating input | real-code edit it corresponds to |
|---|---|---|---|
| `Solution_prepatch.lean` | `collapseDoubledQuotes` rewrites `''`→`'` in the trimmed body before the `&`-trim | any field whose body contains a doubled quote `''` (e.g. `'…''…'`) | the deleted `.replace("''", "'")` at `card.py:862` (hunk 1) |
| `Solution_prepatch_2.lean` | `closesEarly`/`contentEarly` accept as closing ANY delimiter merely followed by padding or the annotation introducer, losing the tail past it, and treat every text as a record | a record whose content holds an interior delimiter followed by more content, e.g. `'a' x'` or `'…'''' xxx'` | the missing `$` anchor on `_strg_comment_RE` at `card.py:69` (hunk 2) |

Each prepatch carries the gold spec verbatim (`same_spec` holds) and the gold
proof body; against its buggy impl the `ensures out = recovered field` goal
cannot close — the goal reduces to `collapseDoubledQuotes trimmed = trimmed`
(prepatch 1, false whenever `trimmed` contains `''`) resp. an equality between the
weak-close content read and `recordContent` (prepatch 2, false whenever an
interior delimiter is followed by more content, and false in the `none` case
because the weak reading always answers `some`) — so G-VERIFY fails: the G-DIFF
signal. Each was machine-refuted at a concrete witness via the Velvet tester
(`recoverSegmentTextTester ['\'','a','\'','\'','\''] = false` for prepatch 1;
`… ['\'','a','\'',' ','x','\''] = false` for prepatch 2), and gold satisfies the
postcondition at both. Both discriminating differences were also confirmed against
the real regexes: the pre-patch (unanchored) reading drops the ` x` tail of
`'a' x'`, where the real post-patch capture keeps it.

### Why hunk 2 is load-bearing (why the previous single-hunk slice was broken)

The earlier bundle modeled only hunk 1 and declared hunk 2 "out of scope"
("upstream of `body`"). That was FALSE: in-container isolation showed hunk-1-alone
fails F2P assertion 3 (`testval = "x"*100 + "'' xxx"` round-trips to `…''`, the
` xxx` tail dropped). Hunk 2 changes WHICH span of `vc` becomes the body: for the
`'' <space> text` case the unanchored regex truncates the body before that text,
so the value the recovery returns is itself wrong regardless of hunk 1. A faithful
refinement must therefore reproduce both hunks; the modeled op now takes the raw
field `vc` as input and performs the (post-patch) capture as step 2, so a verifying
impl produces BOTH hunks. (See verdict.md DEFECT 1.)

## Soundness check (verify ⟹ correct)

- `ensures out = recovered field` pins the output EXACTLY (full structural
  equality to `(recordContent field).map (dropTrailingAmp ∘ rstripSpaces)`, both
  the `some`/`none` verdict and every output character determined by `field` —
  directive 8: no ungrounded oracle; the postcondition is dischargeable only by
  reading the content off the record grammar and then performing the rstrip and
  the `&`-trim). `field` is read-only, not `mut` (directive 5). The method carries
  NO `require`: the contract is asserted on every `vc` the real recovery can
  receive, including the comment-bearing ones, the malformed ones, and the ones
  carrying a character outside the record content set `[ -~]` — which the reader
  API can deliver. Because there is no `require`, the model owes the real
  callee's answer on ALL of those, and the content character set and the
  end-of-record line break are modeled for exactly that reason rather than
  assumed away by a narrowed domain.
- The changed ops (which delimiter closes the content, and the `rstrip` without
  the duplicate collapse) are modeled deeply, not axiomatized (directive 7);
  validated == the real post-patch regex + recovery by G-CONF over the FULL
  received-segment domain — `/`-bearing, malformed and non-`[ -~]`-bearing
  segments included (mapping.md).
- Each prepatch violates the spec at its discriminating clause, so its carried
  proof cannot close (G-DIFF), one per independently-fixed behavior.
- G-MUT additionally kills impl-region mutants, confirming spec tightness.
