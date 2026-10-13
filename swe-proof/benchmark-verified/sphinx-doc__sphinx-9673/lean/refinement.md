# refinement.md — sphinx-doc__sphinx-9673

Every op in `implementation_augment` mapped to its `patch.diff` counterpart.
Tags: **R** (type-only refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

There are NO A-consumed axioms and NO A-reference deep models in this bundle:
the impl is pure control flow over abstract inputs. Every row is R or I.
`meta.json conf_skip = false` (the impl region is NOT all-A-tagged).

## implementation_augment ↔ augment_descriptions_with_types

The gold has TWO coupled hunks, both inside this one function:

```python
 # classification loop:
-        elif parts[0] == 'return':              # hunk 1 (pre)
+        elif parts[0] in ('return', 'returns'): # hunk 1 (post)
             has_description.add('return')
 ...
 # back-fill loop:
     for name in annotations:
-        if name == 'return':                    # hunk 2 (pre)
+        if name in ('return', 'returns'):       # hunk 2 (post)
             continue
```

### Classification loop (`for parts in fields`)

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `let p0 := parts.headD ""` | `parts[0]` | R | `parts` is the env-supplied `re.split(' +', field_name)` token list; `headD ""` mirrors `parts[0]` (a non-empty split always has ≥1 token) |
| `if p0 == "param" then …` | `if parts[0] == 'param':` | I | same guard |
| `if parts.length == 2 then hasDesc ++ [parts.getD 1 ""]` | `if len(parts)==2: has_description.add(parts[1])` | R | set-add ↔ list-append; membership is the only observable |
| `else if parts.length > 2 then name := joinSp (parts.drop 2); hasDesc++[name]; hasType++[name]` | `elif len(parts)>2: name=' '.join(parts[2:]); has_description.add(name); has_type.add(name)` | R | `joinSp = String.intercalate " "` ↔ `' '.join` |
| `else if p0 == "type" then hasType ++ [joinSp (parts.drop 1)]` | `elif parts[0]=='type': has_type.add(' '.join(parts[1:]))` | R | as above |
| **`else if p0 == "return" \|\| p0 == "returns" then hasDesc ++ ["return"]`** | **`elif parts[0] in ('return','returns'): has_description.add('return')`** | **R** | **gold hunk 1 — the two-spelling synonym; the plural marker now records a result description** |
| `else if p0 == "rtype" then hasType ++ ["return"]` | `elif parts[0]=='rtype': has_type.add('return')` | R | set-add ↔ list-append |
| `else pure ()` | (no matching `elif`) | I | unrecognized marker ignored |

### Back-fill loop (`for entry in annotations`) + trailing rtype

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `for entry in annotations` | `for name in annotations:` | R | `OrderedDict` iteration order ↔ list order; preserved |
| **`if name == "return" \|\| name == "returns" then pure ()`** | **`if name in ('return','returns'): continue`** | **R** | **gold hunk 2 — skip BOTH spellings when back-filling per-name `type` fields** |
| `else if hasDesc.contains name && !hasType.contains name then out ++ [("type "++name, ann)]` | `if name in has_description and name not in has_type: <append type field>` | R | set membership ↔ `.contains`; appended `nodes.field` ↔ `("type "++name, ann)` |
| `else pure ()` | (loop falls through) | I | |
| `match annotations.lookup "return" with \| some ann => if hasDesc.contains "return" && !hasType.contains "return" then out ++ [("rtype", ann)]` | `if 'return' in annotations: if 'return' in has_description and 'return' not in has_type: <append rtype field>` | R | dict lookup ↔ `List.lookup`; appended rtype `nodes.field` ↔ `("rtype", ann)` |
| `\| none => pure ()` | (outer `if` false) | I | |

## The two hunks: hunk 1 is observable, hunk 2 is defensive

The F2P documents a function whose docstring's `:returns:` field (plural) is the
ONLY result marker. **Hunk 1 (classification loop)** is the observable fix:
without it, `"returns"` is an unrecognized marker → `"return"` is never added to
`has_description` → the trailing `rtype` guard (`'return' in has_description`) is
false → no return-type field is emitted (the reported bug). Hunk 1 normalizes
BOTH spellings to the canonical key `'return'`.

**Hunk 2 (back-fill skip loop)** is a defensive, symmetric edit with NO
observable effect on the reachable input domain: the back-fill loop iterates the
ANNOTATION TABLE keys, and the result annotation is ALWAYS stored under the
literal key `'return'` (set by `record_typehints` as
`annotation['return'] = typing.stringify(sig.return_annotation)`) — an
annotation key is never the plural `'returns'`. So `if name in
('return','returns')` and the pre-patch `if name == 'return'` are observably
identical on every reachable input; hunk 2 cannot fire its `'returns'` arm in
practice. (The model still mirrors hunk 2 literally — `outStep` skips both
spellings — and G-CONF fuzzes a synthetic `"returns"` annotation key to confirm
the shadow and the patched function agree on it too.)

Both edits sit inside one function with one observable output (the appended
fields). Because only hunk 1 changes reachable behavior, a SINGLE prepatch
reverting BOTH hunks to the literal pre-patch source captures the
independently-fixed behavior, and its divergence from the gold is driven by
hunk 1 (see G-DIFF below).

## Frame discipline (SPEC_GUIDE §0.5)
The spec pins `result` to the FULL deterministic appended-field list
`augmentSpec fields annotations` (exact equality), not a partial property. There
is no unconstrained output component — every appended field, its kind, its text,
and the append order are fixed by the inputs. A wrong impl cannot leave any part
of the result free.

### Consequence for spec-too-weak auditing (note for G-EQ / G-PANEL-1)
Because `problem_spec_augment fields annotations result := result = augmentSpec
fields annotations` is EXACT equality to a TOTAL COMPUTABLE function with no
oracle, no free component, and no axioms, a closing clean-axiom
`correct_augment` for ANY same-spec impl proves `∀ inputs, impl = augmentSpec`
— extensional identity on the whole input domain. Therefore:
- a same-spec impl that verifies is necessarily extensionally CORRECT (its
  faithful refined patch is behaviorally the gold widening and resolves the
  F2P) — it is a positive control, not a wrong-impl counterexample;
- the "ungrounded-oracle echo" attack class (`implementation_augment :=
  augmentSpec`, provable by `rfl`) verifies BY CONSTRUCTION here precisely
  because `augmentSpec` is the grounded deep model, not an unconstrained
  oracle; the echo is a correct impl, and submitting it (or any other
  extensionally-equal variant) in the `attacks` list would mechanically
  misrecord a correct impl as a spec weakness;
- a genuinely wrong impl (one differing from `augmentSpec` on any input, e.g.
  either prepatch hunk reverted) makes `correct_augment` FALSE on a concrete
  input (`fields=[["returns"]], annotations=[("return","int")]`: gold
  `[("rtype","int")]` vs buggy `[]`, distinguishable by `decide`), so no
  honest tactic can close it.
Wrong-impl attacks must be extensionally wrong; verifying attacks belong in
`positive_control` (or, for G-EQ, must carry their faithful patch, which will
resolve).

## G-DIFF: one failing prepatch per independently-fixed behavior
- `Solution_prepatch.lean`: reverts BOTH hunks (`p0 == "return"` only;
  `name == "return"` only) — the literal pre-patch source. On an input whose only
  result marker is the plural `["returns"]` with `annotations` carrying a
  `"return"` type, the gold appends `("rtype", ann)` but the prepatch appends
  nothing, so `correct_augment` is unprovable on the exact-equality clause.
  (Both hunks are observable through the same single output; reverting either
  alone already diverges on a plural-only docstring, and reverting both is the
  true pre-patch state, so one prepatch suffices.)

## Relaxed leakage
This instance is a documented `problem_statement ↔ gold` mismatch
(RELAXED_LEAKAGE.md): the plural `:returns:` reST-field discriminator the
F2P pins is absent from the public `problem_statement` (whose only `Returns`
token is the Google-style docstring SECTION HEADER `Returns:`, a homograph of —
not — the reST field marker) and lives only in `hints_text`/gold/`test_patch`.
A faithful spec must name the two-spelling synonym. See RELAXED_LEAKAGE.md.
