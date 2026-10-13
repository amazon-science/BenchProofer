# refinement.md — operation correspondence (pytest-dev__pytest-7205)

Maps every op in `implementation_actionLine` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom/opaque callee ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

Post-patch Python (the modeled tail of `_show_fixture_action`):

```python
# header already written: step/scope/fixture (+ optional "fixtures used: …")
if hasattr(fixturedef, "cached_param"):
    tw.write("[{}]".format(saferepr(fixturedef.cached_param, maxsize=42)))
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut out := header` | the header text already written to `tw` before the bracket | R | the unchanged framing prefix; `List Char` ↔ accumulated terminal text (mapping.md). Pinned to input verbatim (directive 5 frame). |
| 2 | `match param with … | none => pure ()` | `if hasattr(fixturedef, "cached_param"):` false branch — nothing appended | I | present/absent guard; absent ⇒ header unchanged |
| 3 | `some p => out := out ++ ['['] ++ … ++ [']']` | `tw.write("[{}]".format(...))` — wrap in `[` … `]` | I | identical bracket-delimited concatenation; `'['`/`']'` literals unchanged |
| 4 | `safeDisplay p` | `saferepr(fixturedef.cached_param, maxsize=42)` | A-consumed | the UNCHANGED callee the fix newly invokes (`_pytest._io.saferepr.saferepr`, applied with the reporter's fixed size budget — the budget is absorbed into the opaque symbol as an internal detail of the callee application), declared `opaque safeDisplay` (signature only). The proof uses only the opaque symbol's identity (same term in spec and impl); no behavioral `_prop` is asserted. G-AX validates the signature against the real `saferepr` application (accepts a value, returns text) on boundary + fuzz. |
| 5 | `return out` | end of the appends written to `tw` | I | identity return |

No A-reference rows (no changed op is modeled deeply). No changed-inexpressible
op.

## Discriminating clause (G-DIFF)
Row 4. The prepatch skeleton inserts the parameter value **verbatim**
(`out ++ p`, the implicit `str()` coercion), whereas the frozen
`problem_spec_actionLine` pins the bracket contents to `safeDisplay p`. Since
`safeDisplay` is opaque, there is no equation `p = safeDisplay p`, so the
prepatch `correct_actionLine` cannot close on the `some p` branch. That is the
G-DIFF signal and it is exactly the F2P observation: a string parameter `foo`
must render as `'foo'` (the safe representation), not `foo` (the bare value), and
a `bytes` parameter must be rendered safely (no `BytesWarning`). The `none`
branch (header unchanged) is common to both, so it is not the discriminator.
