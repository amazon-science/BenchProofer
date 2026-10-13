# refinement.md — operation correspondence (astropy__astropy-14309)

Maps every op in `implementation_isFits` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python `is_fits` is:
```
if fileobj is not None:
    pos = fileobj.tell(); sig = fileobj.read(30); fileobj.seek(pos)
    return sig == FITS_SIGNATURE
elif filepath is not None:
    return filepath.lower().endswith((".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz"))
return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if let some content := fileobj then …` | `if fileobj is not None:` | R | `None`/value ↔ `Option`; the `tell/read(30)/seek` positional dance is frame-invisible — only the 30 read bytes are observed (mapping.md). |
| 2 | `return Except.ok (content.take 30 == fitsSignature)` | `return sig == FITS_SIGNATURE` | I | `read(30)` ↔ `take 30`; `FITS_SIGNATURE` inlined as `fitsSignature`; boolean equality. |
| 3 | `if let some p := filepath then …` | `elif filepath is not None:` | R | `None`/value ↔ `Option`. The `elif` is reached only when `fileobj` is `None`, matched by the early `return` above. |
| 4 | `return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)` | `return filepath.lower().endswith((...))` | A-reference | the CHANGED branch: a present path returns the suffix-test boolean as the full answer. `str.lower()` ↔ `map Char.toLower`, `str.endswith(tuple)` ↔ `isSuffixOf` over `fitsExtensions`; validated == real string ops by G-AX. NOT axiomatized. |
| 5 | `match args with \| [] => return Except.error ()` | `args[0]` on empty tuple → `IndexError` | I | the out-of-range access modeled as `Except.error ()`; reached only when both `fileobj` and `filepath` are `None` (mirrors the trailing `return`). |
| 6 | `\| a :: _ => return Except.ok a` | `return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))` | I | head membership flag (mapping.md args modeling); tail unobserved, as in Python. |

No A-consumed rows: the proof discharges the structural `match` directly; no
UNCHANGED callee property is assumed. No changed-inexpressible op.

## Discriminating clause (G-DIFF)
Row 4 is the fix. Post-patch, a present non-matching path returns
`Except.ok false`. The prepatch impl instead only short-circuits on a *match*
(`if endsWithAny … then return ok true`) and otherwise falls through to the
`args` probe; with `filepath = some p` (non-FITS suffix) and `args = []` it
yields `Except.error ()`, while the frozen `problem_spec_isFits` pins
`Except.ok false`. Hence the prepatch `correct_isFits` is unclosable — the
G-DIFF signal. This is exactly the issue's `IndexError: tuple index out of
range` (`identify_format("write", Table, "bububu.ecsv", None, [], {})`).
