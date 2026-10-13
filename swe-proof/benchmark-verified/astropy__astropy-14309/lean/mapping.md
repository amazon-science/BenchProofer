# mapping.md — symbol binding & type bijection (astropy__astropy-14309)

## Modeled function
- **Lean** `implementation_isFits : Option (List Char) → Option (List Char) → List Bool → Except Unit Bool`
- **Python** `astropy.io.fits.connect.is_fits(origin, filepath, fileobj, *args, **kwargs)`
  — `astropy/io/fits/connect.py:48-72 @ cdb6605` (the changed function).

`is_fits` decides whether the inputs denote a FITS source. It examines, in
priority order, a readable file-like object, then a path string, then the first
positional argument. The patch changes the path branch: a present path must
yield the suffix-test boolean as the *full* answer for that branch, rather than
only short-circuiting on a match and otherwise falling through to the
positional-argument probe (which raises when no positional argument exists).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `fileobj` (`None` or readable) | `Option (List Char)` | `none` ↔ `None`; `some content` carries the first 30 bytes that `fileobj.read(30)` returns (the only bytes the comparison observes). `tell`/`seek` are pure-positional and frame-invisible. |
| `filepath` (`None` or `str`) | `Option (List Char)` | `none` ↔ `None`; `some p` ↔ the path string as a code-point list. |
| `*args` (positional tuple) | `List Bool` | each entry pre-reduced to the `isinstance(_, (HDUList, TableHDU, BinTableHDU, GroupsHDU))` membership flag it would produce; `[]` ↔ empty tuple. See "args modeling" below. |
| `FITS_SIGNATURE` (`b"SIMPLE  =                    T"`, 30 bytes) | `fitsSignature : List Char` | byte-for-byte; ASCII so code-point list is faithful. |
| extension tuple | `fitsExtensions : List (List Char)` | the six recognised lower-case suffixes, in source order. |
| return `bool` | `Except.ok Bool` | the normal boolean answer. |
| `IndexError: tuple index out of range` (`args[0]` on empty `args`) | `Except.error ()` | the only exception the modeled control flow can raise. |

## args modeling (frame discipline)
The Python `args[0]` is `isinstance(args[0], (HDUList, TableHDU, BinTableHDU,
GroupsHDU))`. The *object identity* of `args[0]` is irrelevant to the modeled
behavior — only the resulting membership boolean is observable. We therefore
model `args` as the `List Bool` of those per-element membership flags. The
patched control flow only ever inspects `args[0]`; the tail is carried but
unobserved (it pins nothing, matching Python). The bug is precisely that an
empty tuple makes `args[0]` raise `IndexError`, modeled as `Except.error ()` on
`args = []`.

## Operations modeled deeply (A-reference) / identical (I)
- **Signature compare** `sig == FITS_SIGNATURE` → `content.take 30 == fitsSignature`.
  `fileobj.read(30)` reads at most 30 bytes; `take 30` is the faithful refinement.
  I-tagged (concrete equality).
- **Suffix test** `filepath.lower().endswith((...))` → `endsWithAny (p.map
  Char.toLower) fitsExtensions`. Modeled DEEPLY: `str.lower()` ↔ `List.map
  Char.toLower`, `str.endswith(tuple)` ↔ "some suffix `isSuffixOf`". Validated as
  an **A-reference** by G-AX against the real `str.lower()`/`str.endswith`.
- **Membership probe** `isinstance(args[0], (...))` → reading the head flag of
  `args`. I-tagged (the flag is the modeled carrier; see args modeling).

## Callee provenance
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.
  `FITS_SIGNATURE` is an in-module constant (`hdulist.py:43`), inlined as data.
  `str.lower`/`str.endswith` are standard-library string ops, deep-modeled and
  G-AX-validated, not axiomatized.

## Flag dependency
None. `is_fits` reads no boolean flags; `**kwargs` is ignored by the function.

## G-CONF fuzz seed
Pinned seed: **14309**. ≥10^5 fuzzed inputs spanning all three branches
(`fileobj` present / `filepath` present with oversampled FITS-suffix paths /
neither, with empty and non-empty `args`).
