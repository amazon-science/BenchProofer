# refinement.md — pytest-dev__pytest-5809

The operation-by-operation correspondence between `model.py`'s implementation
(the three field-producing functions and the `text_token`/`expiry_token` deep
constants) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed**, the proof uses the
axiom's `Ensures`; or **A-reference**, a deep model validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The request-parameters site — `create_new_paste()` (`src/_pytest/pastebin.py:80-84`)

Gold hunk:
```
- params = {
-     "code": contents,
-     "lexer": "python3" if sys.version_info[0] >= 3 else "python",
-     "expiry": "1week",
- }
+ params = {"code": contents, "lexer": "text", "expiry": "1week"}
```

Only the `lexer` value changed (`"python3"/"python"` → `"text"`); the `code` and
`expiry` entries are byte-for-byte identical across the hunk. The dict is
modeled as its three independent field values.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `paste_mode_field` returns `[116,101,120,116]` (`"text"`), independent of the `py_major` parameter | `"lexer": "text"` (post-patch) | I | the same concrete constant token `"text"`, refined `str` → `List[int]` of code points; the model returns it unconditionally, mirroring the constant dict value (no branch on version). |
| A2 | the postcondition `ToSeq(Result()) == text_token()` holds for EVERY `py_major` | the value `"text"` does not reference `sys.version_info[0]` | I/R | `py_major` models `sys.version_info[0]`; the post-patch value is version-invariant, captured by the postcondition quantifying over all `py_major`. (mapping.md §1.) |
| A3 | `paste_body_field(contents)` returns `list(contents)`, with `ToSeq(Result()) == ToSeq(contents)` | `"code": contents` (unchanged) | R+I | identity on the body; `str`/bytes ↔ `List[int]` (mapping.md §2). Unchanged entry, modeled for hunk fidelity. |
| A4 | `paste_expiry_field()` returns `[49,119,101,101,107]` (`"1week"`) | `"expiry": "1week"` (unchanged) | I | the same concrete constant token, refined `str` → `List[int]`. Unchanged entry, modeled for hunk fidelity. |
| A5 | (no node) the `params` dict assembly, `url`, `urlencode(...).encode("ascii")`, `urlopen`, `re.search`, return | `params = {...}`; the surrounding serialise/POST/parse lines | A-reference | the surrounding serialisation/transport is UNCHANGED by the patch; the only changed value is the `lexer` token (A1/A2). The serialiser `urllib.parse.urlencode` is validated against the modeled constant tokens by G-AX (mapping.md §3.1): the post-patch `params` serialises to `lexer=text`, `expiry=1week`, `code=<contents>` — exactly the F2P assertions. |

The discriminating content of the change — the mode field is the plain-text
token `"text"` rather than a version-derived `"python3"`/`"python"` token —
lives in `paste_mode_field`'s postcondition `ToSeq(Result()) == text_token()`
holding for every `py_major`. `model_prepatch.py` reproduces the pre-patch
version-branch (`py_major >= 3 → "python3"`, else `"python"`) and **fails** that
postcondition at `model_prepatch.py:58` (`paste_mode_field`), which is exactly
the spec sensing the change (G-DIFF). The `paste_body_field` / `paste_expiry_field`
impls are unchanged across the twin (their dict entries did not change).

## B. No consumed axiom

There is **no `@ContractOnly` axiom** in this bundle (the `axioms` region is
empty): the changed operation is a concrete constant-token selection, modeled
deeply (`text_token`, A1/A2). The only kind-A relationship is the **A-reference**
of step A5: the unchanged serialiser `urllib.parse.urlencode`, against which the
deep-model token constants are validated by axiom_check.py / G-AX. No proof
obligation consumes an axiom's `Ensures`; nothing is claimed load-bearing that
isn't.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the mode-field value — is modeled **deeply and concretely** (the
constant `text_token` returned by `paste_mode_field`, A1), not hidden behind an
axiom about the function under change.

## D. verify(model) ⇒ resolved

`paste_mode_field` verifies only if it returns the `"text"` token for every
`py_major` (A1/A2); `paste_body_field`/`paste_expiry_field` verify only if they
forward `contents` and the `"1week"` token (A3/A4). By R (str/bytes ↔
`List[int]`) these are the exact post-patch dict values; by the A-reference
(G-AX) the unchanged `urllib.parse.urlencode` serialises that dict to the
`lexer=text` / `expiry=1week` / `code=<contents>` wire form the F2P test
asserts. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited serialiser — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (here: the A-reference serialiser, G-AX) and refinement fidelity
(this document, G-EQ).
