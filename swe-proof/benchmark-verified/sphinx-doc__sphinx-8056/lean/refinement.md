# refinement.md — sphinx-doc__sphinx-8056

Operation correspondence between `implementation_normalizeEntries` (Lean) and the
gold `patch.diff` modification of `_consume_fields` /
`_parse_parameters_section` (`sphinx/ext/napoleon/docstring.py`).

Tags: **R** type refinement · **A-consumed** proof uses this axiom · **A-reference**
deep-modeled, validated == real callee by G-AX/G-CONF · **I** identical concrete op.

| # | `implementation_normalizeEntries` op | `patch.diff` counterpart | tag | note |
|---|---|---|---|---|
| 1 | `splitGrouped : Bool` parameter | `multiple: bool = False` param of `_consume_fields`, set `True` by `_parse_parameters_section` under `napoleon_use_param` | R | Python `bool` ↔ Lean `Bool`. The flag dependency (`napoleon_use_param`) is recorded in mapping.md. |
| 2 | `raws : List FieldEntry` input | the entries yielded by the `while not self._is_section_break(): _name,_type,_desc = self._consume_field(...)` loop | R | Each `(name,type,desc)` tuple ↔ `FieldEntry = List Char × List Char × List (List Char)`. Entry-reading + boundary detection are UNCHANGED bookkeeping, abstracted into the input list (not modeled — they are identical pre/post-patch). |
| 3 | `for f in raws do` | `while not self._is_section_break(): ...` | I | In-order iteration over the read entries. |
| 4 | `if splitGrouped && (name != [])` | `if multiple and _name:` | I | The new guard introduced by the patch. |
| 5 | `commaPieces name` | `_name.split(",")` | A-reference | Delimiter split on `','`; always ≥1 piece. Modeled deeply by `commaPieces`; validated == `str.split(",")` by G-CONF. |
| 6 | `trim piece` | `name.strip()` | A-reference | Strip leading/trailing whitespace — exactly Python's `str.isspace()` set (U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000). Modeled deeply by `trim`/`isBlank`; validated == `str.strip()` on all inputs (Unicode whitespace incl. NBSP) by G-CONF. |
| 7 | `fields := fields ++ [(trim piece, typ, desc)]` (per piece) | `fields.append((name.strip(), _type, _desc))` | I | One emitted entry per comma piece, sharing `typ`/`desc`. |
| 8 | `else if (name != []) \|\| (typ != []) \|\| (desc != [])` | `elif _name or _type or _desc:` | I | The unchanged keep-if-nonempty branch. |
| 9 | `fields := fields ++ [(name, typ, desc)]` | `fields.append((_name, _type, _desc,))` | I | Keep the whole entry. |
| 10 | `return fields` | `return fields` | I | |

Every op is R, A-reference, or I. No A-consumed axiom (nothing the proof assumes
about an opaque callee). No changed op is inexpressible: the comma-split and the
blank-trim — the entire behavioral delta — are spelled out and differential-tested.

The R/I legs (and the A-reference `commaPieces`/`trim`) are mechanically refuted
by `conformance_check.py` over ≥10⁵ fuzzed inputs (zero disagreements required).
