# mapping.md — astropy__astropy-14598

## Symbol binding (file:line @ base_commit 80c3854a)

- Changed function: `Card._split`, `astropy/io/fits/card.py:830` (the CONTINUE
  branch, lines ~855–868). The two changed lines:
  - `astropy/io/fits/card.py:69` — `_strg_comment_RE` pattern: an anchoring
    metacharacter was appended so the pattern must consume the whole field.
  - `astropy/io/fits/card.py:862` — the per-subcard value cleanup line.
- Supporting (unchanged) repo regex fragments used by the model:
  - `_strg` = `\'(?P<strg>([ -~]+?|\'\'|) *?)\'(?=$|/| )` (card.py:67)
  - `_comm_field` = `(?P<comm_field>(?P<sepr>/ *)(?P<comm>(.|\n)*))` (card.py:68)

The modeled function takes the value/comment substring `vc` of a single
(sub)card (after the keyword indicator is removed and the field stripped) and
produces the *value* contributed by that subcard. This is exactly the body that
the gold patch edits; the surrounding `_split` accumulation/`join` over subcards
is unchanged and framed out.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | notes |
|---|---|---|
| `vc : str` (printable ASCII field) | `vc : List Char` | per-code-point parse; Lean indexing total |
| `m.group("strg") or ""` then cleanup → `value : str`, or early `return kw, vc` | `Option (List Char)` | `some v` = matched, contributed value `v`; `none` = regex did NOT match (caller takes `vc` verbatim — only reachable under the fixed, anchored pattern) |
| `str.rstrip()` | `dropTrailingWs` (drop trailing ASCII whitespace ` \t\n\r\x0b\x0c`) | |
| `value[:-1]` when `value[-1]=="&"` | `dropTrailingAmp` (`dropLast` if last char is `&`) | single trailing marker |
| `re.match` capture of `strg` group | `matchQuoted` (fixed) / `matchTokenLoose` (pre-patch) | deep model of the regex, NOT an axiom |
| `str.replace("''","'")` (pre-patch only) | `collapseDoubledQuote` | left-to-right non-overlapping |

`Char` bijection: ASCII code point ↔ `Char.toNat`. Inputs are printable ASCII
(FITS card images are space-padded printable ASCII per `_ascii_text_re`); the
model's `isPrintable` is `32 ≤ toNat ≤ 126`, matching Python `[ -~]`.

## Regex model (the deep model, reverse-engineered & validated)

The fixed pattern `({_strg})? *{_comm_field}?$` extracts the `strg` group. Validated
EXACTLY (0 mismatches) against the real `re.compile(...).match(...).group("strg")`
over all printable strings of length ≤ 6 across a 11-char alphabet incl.
`' ' '/' '&' '~'` (~10^7 inputs). Operational rule (fixed):

- If `vc` begins with `'`: scan the body left→right accumulating printable
  chars; accept the first `'` that has a non-empty accumulator AND whose suffix
  is `spaces*` then optional `/…` to end-of-string (`remainderOk`) — the captured
  group is the accumulator. Else if body starts with `'` and `remainderOk` holds
  on the rest, the group is empty. Else NO match (`none`).
- If `vc` does not begin with `'`: matches with empty group iff `remainderOk vc`,
  else NO match.

Pre-patch pattern `({_strg})? *{_comm_field}?` (no anchor) differs in two ways,
both validated exactly: (1) the closing quote needs only the lookahead
`(?=$|/| )` — NOT that the remainder reaches end-of-string (`lookaheadOk`); the
match always succeeds (group defaults to empty). (2) the value is then passed
through `.replace("''","'")`.

## Callee provenance / flag deps

No unchanged external callee is consumed as an axiom. `re.match` behavior on the
specific (changed) pattern is the operation under change, so it is modeled deeply
(A-reference, validated by G-CONF differential test), not axiomatized.
`str.rstrip`/`str.replace`/slicing are deeply modeled. ⇒ axiom_check.py is a skip
stub.

## G-CONF fuzz seed

Pinned seed: `14598`. Fuzz domain: strings over alphabet
`{ x ' / space & ~ A B 1 2 - }`, lengths 0..12, with leading-prefix variants
`{ ' , x , / , space , "" }`, ≥10^5 draws; oracle = the two real regexes +
Python cleanup pipeline (fixed vs pre-patch) reproduced in conformance_check.py.
