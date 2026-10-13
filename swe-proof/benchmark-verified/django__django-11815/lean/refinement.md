# refinement.md — operation correspondence (django__django-11815)

Maps every op in `implementation_serializeEnum` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`EnumSerializer.serialize`) renders the source text that
reproduces an enum member by formatting the literal template `'%s.%s[%r]'` with
the module path, the enum type name, and the member's identifier
(`self.value.name`). We model the template substitution as the equivalent
fixed-order concatenation, and `%r` of the identifier as `quoted`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `module : List Char` | `%s` ← `module` (`enum_class.__module__`) | R | str ↔ List Char bijection (mapping.md); module path passed through unchanged |
| 2 | `className : List Char` | `%s` ← `enum_class.__name__` | R | str ↔ List Char bijection; type name passed through unchanged |
| 3 | `quoted name` = `['\''] ++ name ++ ['\'']` | `%r` ← `self.value.name` | R | the **changed op** modeled deeply: the member is now referenced by its identifier; `%r` of a Python identifier (name chars only, no escapable char) is the identifier wrapped in single quotes. NOT axiomatized. |
| 4 | `module ++ ['.'] ++ className ++ ['['] ++ quoted name ++ [']']` | substitution into the literal template `'%s.%s[%r]'` | I | identical concrete op: substitution into a fixed literal template is fixed-order concatenation with the literal `.`, `[`, `]` separators |
| 5 | `let _ := payload` (payload discarded) | the deleted lines `v_string, v_imports = serializer_factory(self.value.value).serialize()` and the `(%s)` value-call rendering | A-consumed? **No** — the payload is DROPPED by the fix; discarding it consumes no callee property. Tag: **I** (the post-patch op simply does not read the payload) |
| 6 | `return …` (the rendered text) | the first element of the returned tuple | I | the returned `imports` set is unaffected by the rendered-text fix and is out of model scope (mapping.md scope note) |

No A-consumed rows: the proof discharges the concatenation directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub). The only
callee that appeared in the function (`serializer_factory(...).serialize()`) is
DELETED by the patch, so it is neither consumed nor referenced post-patch.
No A-reference rows: the only callee (`%`-substitution into the literal template
`'%s.%s[%r]'`) is reproduced concretely as an I op, not abstracted behind a model
that needs G-AX validation. No changed-inexpressible op.

The discriminating clause is rows 3+4: post-patch the member is rendered as the
quoted-identifier subscript `[' name ']` and the payload is not consulted; the
prepatch impl renders the payload as a positional call argument
`(payload)` and ignores the identifier. So the prepatch result is
`module ++ '.' ++ className ++ '(' ++ payload ++ ')'`, which differs from the
frozen `problem_spec_serializeEnum`
(`… ++ '[' ++ quoted name ++ ']'`) on essentially every input (the bracket vs
paren punctuation alone differs). Hence prepatch `correct_serializeEnum` cannot
close — the G-DIFF signal.
