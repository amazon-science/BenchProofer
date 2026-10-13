# refinement.md — operation correspondence (django__django-11133)

Maps every op in `implementation_toBytestring` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python `make_bytes`:
```python
if isinstance(value, (bytes, memoryview)):
    return bytes(value)
if isinstance(value, str):
    return bytes(value.encode(self.charset))
return str(value).encode(self.charset)
```
We model `value` as the four-way `PyValue` (bytes / memoryview / str / other),
mirroring the three `isinstance` branches plus the final fall-through, and pin
the result of each branch in `problem_spec_toBytestring`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `match value with …` (4-way dispatch) | the chained `isinstance` tests + final fall-through | R | `PyValue` ↔ Python value-kind dispatch (mapping.md); each constructor is one runtime type-test outcome |
| 2 | `.bytesV b => return b` | `isinstance(value, bytes)` → `return bytes(value)` | I | `bytes(value)` of a `bytes` is the same buffer; modeled as identity onto `List UInt8` |
| 3 | `.memoryviewV b _ => return b` | `isinstance(value, memoryview)` (NEW) → `return bytes(value)` | I | `bytes(value)` of a memoryview copies the underlying buffer bytes verbatim; modeled as identity onto the underlying `List UInt8`. **This is the discriminating clause** (the added `memoryview` arm). |
| 4 | `.strV s => return encode charset s` | `isinstance(value, str)` → `return bytes(value.encode(self.charset))` | I | identical str→bytes encoding; `encode` applied to the same charset/string |
| 5 | `.otherV text => return encode charset text` | `return str(value).encode(self.charset)` | I | identical render-to-text then encode |

No A-consumed rows: `encode` is an UNCHANGED callee applied identically on both
sides of each str/other branch, so the proof discharges those branches by
reflexivity — no callee property is assumed. No A-reference rows: nothing is
deeply modeled against a real callee that needs G-AX validation (G-AX is a skip
stub). No changed-inexpressible op.

The discriminating clause is **row 3**: the memoryview arm. The frozen spec pins
`problem_spec_toBytestring charset (.memoryviewV b _) = (result = b)`. The
prepatch impl routes `.memoryviewV _ r` to `encode charset r` (the textual
rendering), so its `correct_toBytestring` cannot close the memoryview goal
`encode charset r = b` against the frozen spec. That is the G-DIFF signal, and it
mirrors exactly the F2P failure (`b'<memory at 0x...>' != b'memoryview'`).

Frame discipline (directive 5): the three unchanged branches (bytes / str /
other) are pinned to their inputs identically in both spec and impl, so a wrong
impl cannot quietly alter a non-memoryview branch and still verify.
