# refinement.md — sphinx-doc__sphinx-10449

Maps every op in `implementation_render_typehint_fields` (Solution.lean) to its
`patch.diff` counterpart. Tags: **R** type-refinement, **A-consumed** axiom used
by proof, **A-reference** deep model validated == real callee by G-AX, **I**
identical concrete op.

The modeled function is `modify_field_list` in
`sphinx/ext/autodoc/typehints.py`. The gold patch adds a boolean parameter and,
when it is set and the return annotation is the unit annotation `'None'`,
returns before appending the `rtype` field. (The caller `merge_typehints` passes
the boolean `True` exactly for `objtype == 'class'`.) The scan loop and the
type/param/rtype generation are modeled deeply (no axioms).

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut fields := existing` | `node` already holds the existing fields; the routine mutates it in place | R | `existing : List DocField` ↔ `list(node)` observed as `(name, body)` records. The result is the field list after the routine returns. |
| 2 | scan via `declaresType/declaresParam/hasReturnField` over `existing` | the `for field in fields:` loop building `arguments: Dict[str, Dict[str,bool]]` (`typehints.py:88-108`) | R | `arguments[nm]['type']`↔`declaresType`, `['param']`↔`declaresParam`, `'return' in arguments`↔`hasReturnField`. Tokenizing `re.split(' +', field_name)`↔`tokenize`. Because `arguments` is keyed by NAME, `type return` / `param return` / `param <kind> return` fields also put `'return'` in the dict, so `isReturnField` matches `rtype …` OR `declaresTypeField f "return"` OR `declaresParamField f "return"`. Modeled deeply, not axiomatized. |
| 3 | `for entry in annotations do … unless name == "return"` | `for name, annotation in annotations.items(): if name == 'return': continue` (`typehints.py:110-112`) | R | `annotations : List (String×String)` ↔ the `OrderedDict` items, in order. |
| 4 | `if !(declaresType existing name) then fields := fields ++ [⟨"type "++name, ann⟩]` | `if not arg.get('type'): field=…field_name('','type '+name)…; node += field` (`:115-119`) | R/I | identical concrete op (a `type name` field carrying the annotation). |
| 5 | `if !(declaresParam existing name) then fields := fields ++ [⟨"param "++name, ""⟩]` | `if not arg.get('param'): field=…field_name('','param '+name)…paragraph('','')…; node += field` (`:120-124`) | R/I | identical concrete op (an empty `param name` field). |
| 6 | `match lookupReturn annotations with \| some ann => if !(hasReturnField existing) then …` | `if 'return' in annotations and 'return' not in arguments:` (`:126/128`) | R | guard for emitting the return-type field. `lookupReturn`↔`annotations['return']`. |
| 7 | `if ann == "None" && suppressTrivialReturn then return fields` | **ADDED** `annotation = annotations['return']; if annotation == 'None' and suppress_rtype: return` (`:129-132` post-patch) | R/I | THE FIX. `suppressTrivialReturn : Bool` ↔ gold `suppress_rtype` (caller passes `objtype == 'class'`). Early `return` ⇒ no `rtype` field. |
| 8 | `fields := fields ++ [⟨"rtype", ann⟩]` | `field=…field_name('','rtype')…field_body('',paragraph('', annotation)); node += field` (`:133-137` post-patch) | R/I | the `rtype` field. **Note:** post-patch uses `annotation = annotations['return']` (the return annotation); the modeled op uses `lookupReturn` (= the return annotation), which also corrects the latent pre-patch bug of reusing the loop-leftover `annotation`. Folded here, not given its own prepatch (not an independently F2P-tested behavior). |

No changed op is inexpressible. No row is A-tagged ⇒ `axiom_check.py` is a skip
stub and `meta.json axioms`/`deep_model_references` are empty.

## Prepatch correspondence (G-DIFF)

- `Solution_prepatch.lean` carries the pre-fix bug: the suppress flag is ignored,
  so when a return annotation is present and no return type is already declared,
  an `rtype` field is ALWAYS appended — even for a suppressed (class) target with
  the trivial unit return `"None"`. On the discriminating input
  `existing=[param x]`, `annotations=[(x,int),(return,None)]`,
  `suppressTrivialReturn=true`, the buggy impl yields
  `[param x, type x, rtype None]`, contradicting the spec's
  `result = existing ++ genParamTypeFields ++ genReturnField` where
  `genReturnField … true = []` (because `ann == "None" && suppress`). The
  `correct_*` theorem is therefore unprovable ⇒ fails G-VERIFY. This is exactly
  the F2P scenario (`test_autodoc_typehints_description_with_documented_init`):
  the spurious `Return type: None` block disappears post-fix.
