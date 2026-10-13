# refinement.md — astropy__astropy-14598

The operation-by-operation correspondence between `model.py`'s implementation
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-reference** (a deep model validated `== the real callee/op` by
`axiom_check.py` / G-AX, NOT a consumed axiom), **A-consumed** (the proof uses an
axiom's `Ensures`; there are NONE here), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim**; it applies at `base_commit` and is
the real correctness oracle (G-RESOLVE).

The gold patch has TWO hunks fixing TWO independently-observable behaviours; the
model has TWO contracted functions, one per hunk, each with its own failing
prepatch (`model_prepatch_2.py` for site A, `model_prepatch.py` for site B).

## A. The regex anchor — site A (`card.py:69`, observed in `_split` `card.py:857,861`)

Gold hunk:
```
- _strg_comment_RE = re.compile(f"({_strg})? *{_comm_field}?")
+ _strg_comment_RE = re.compile(f"({_strg})? *{_comm_field}?$")
```

Modelled by `recover_payload(segment)` (obligation A): the captured payload is
the COMPLETE carried text (`Ensures ToSeq(Result()) == ToSeq(segment)`).

| # | model.py impl op (`recover_payload`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `segment: List[int]` (no code point 47) | the segment value-comment string `vc` whose `strg` group is captured by `_strg_comment_RE` | R | `str` ↔ `List[int]` code points (mapping.md §2); the no-`/` precondition is the domain on which the `$`-anchored regex recovers the full payload (mapping.md §3.3). |
| A2 | the forward copy loop yields `ToSeq(Result()) == ToSeq(segment)` (full payload) | `m.group("strg")` of the `$`-anchored regex | A-reference | the changed operation is a regex; its *changed property* — the match must reach end-of-string, so `strg` captures the whole payload rather than truncating at an interior space — is modelled deeply as the full copy. G-AX asserts the `$`-anchored regex's `strg` group equals the full payload on every no-`/` escaped payload (120 000+ fuzz, 0 mismatch). |

The discriminating content of site A — the regex no longer stops at an interior
space — lives in `recover_payload`'s `Result == segment`. `model_prepatch_2.py`
reverts to the unanchored regex behaviour (truncate at the first single quote
immediately followed by a space) and **fails** the postcondition
`ToSeq(Result()) == ToSeq(segment)` on a segment carrying `'' ` + text — exactly
the spec sensing the change (G-DIFF). G-AX additionally confirms that
truncation model is faithful to the real PRE-PATCH regex.

## B. The double un-escape — site B (`card.py:862`)

Gold hunk:
```
  value = m.group("strg") or ""
- value = value.rstrip().replace("''", "'")
+ value = value.rstrip()
```

Modelled by `unescape_value(captured, witness)` (obligation B): the recovered
text is un-escaped EXACTLY ONCE (`Ensures ToSeq(Result()) == unescape_quotes(ToSeq(captured))`).

| # | model.py impl op (`unescape_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `captured: List[int]` | `value = m.group("strg") or ""` (the recovered segment text) | R | `str` ↔ `List[int]` (mapping.md §2). The `.rstrip()` is the unchanged trailing-blank trim; modelled as the identity on the no-trailing-blank carrier (the formatted words carry no trailing blanks before the closing quote). |
| B2 | single un-escape loop: `ToSeq(Result()) == unescape_quotes(ToSeq(captured))` | the remaining single un-escape `re.sub("''","'", strg)` performed once in `_parse_value` (`card.py:771`), the patch having removed the extra `.replace("''","'")` here | A-reference + I | `unescape_quotes` is the deep model of the single `''`→`'` collapse; G-AX asserts it `== re.sub("''","'",.)` / `str.replace("''","'")`. The patch makes the collapse happen exactly once (here it is dropped; the unchanged `_parse_value` still applies it once). |
| B3 | `witness: List[int]` read-only ghost original value; clause `captured == escape_quotes(witness) ⟹ Result == witness` | the round-trip obligation the change restores: a value carried as `value.replace("'","''")` is recovered unchanged | A-reference + I | discharged by `rt_lemma` (`unescape_quotes(escape_quotes(v)) == v`); ties site B to the FAIL_TO_PASS round-trip identity. `witness` is `Acc(...,1/2)` Required AND Ensured (directive 5). |

The discriminating content of site B — the un-escape happens once, not twice —
lives in `Ensures ToSeq(Result()) == unescape_quotes(ToSeq(captured))`.
`model_prepatch.py` reverts to applying the un-escape TWICE (the removed
`.replace("''","'")` plus the kept `_parse_value` `re.sub`), so a genuine
embedded `''` is wrongly collapsed to `'`; it **fails** that postcondition on a
captured payload containing a quote pair (G-DIFF).

## C. The serialisation escape — supporting (`card.py:1060`, UNCHANGED)

`escape_quotes` (deep model) ↔ `self._value.replace("'", "''")`
(`_format_long_image`, `card.py:1060`). This op is UNCHANGED by the patch; it is
modelled deeply only to state the round-trip identity (`rt_lemma`, the `witness`
clause B3). It is an **A-reference** validated `== str.replace("'","''")` by G-AX,
not a consumed axiom. The skeleton calls it nowhere at runtime; it appears only
inside the proof of the round-trip clause.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two genuinely *changed* operations
— the regex anchor (site A) and the double-vs-single un-escape (site B) — are
modelled **deeply** (the full-capture copy and the single `''`→`'` collapse),
not hidden behind an axiom about the function under change. There are NO consumed
`@ContractOnly` axioms (the `axioms` region is empty). The three deep models
(`escape_quotes`, `unescape_quotes`, full `recover_payload`) are A-references
validated against the real `card.py` regex/escape/unescape by `axiom_check.py`.

## E. verify(model) ⇒ resolved

`recover_payload` verifies only if it recovers the full payload (A2), and
`unescape_value` verifies only if it un-escapes exactly once (B2) and the round
trip is the identity (B3). By R (str ↔ List[int]; `.rstrip()` identity on the
carrier) the verified functions equal the gold-patched `_split`/`_parse_value`
on the tested no-`/` inputs; by G-AX the deep models equal the real regex /
`re.sub` / `str.replace`. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and audited operations — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ).
