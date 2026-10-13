# refinement.md — operation correspondence (psf__requests-2931)

Maps every op in `implementation_encodeParams` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python branch under spec is:
```python
if isinstance(data, (str, bytes)):
    return data
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `return data` (inside `Id.run do`) | `return data` (str/bytes branch of `_encode_params`) | I | identical pass-through: the str/bytes payload is returned unchanged. `Datum` (text/binary) is the R-refinement of Python `str`/`bytes` (mapping.md); the operation itself is the concrete identity on that carrier. |

No op is A-consumed or A-reference: the post-patch modeled branch calls no
unchanged callee. The pre-patch impl's `toNativeString` is a deep model of the
removed coercion, used only to exhibit the bug in `Solution_prepatch.lean`; it is
not part of the shipped `Solution.lean` impl and consumes no axiom.

The impl region is all-R/I (one I op), so **G-CONF runs a real fuzz**
(`conf_skip=false`); the differential shadow is the identity and is diffed
against the post-patch Python branch.

## Changed-op inexpressibility check
The only changed op is "return the str/bytes payload unchanged". It is fully
expressible as the identity on `Datum`; nothing changed-but-inexpressible
remains. Hunk 2 (`prepare_url` compensating coercion) is out of the modeled F2P
scope — see mapping.md "Scope".
