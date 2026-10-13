# mapping.md — sphinx-doc__sphinx-10449

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 36367765fe780f962bba861bf368a765380bbc68`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. Spec provenance: **cold** (derived from `problem_statement`,
gold `patch`, and the real source only).

Repo file under change: `sphinx/ext/autodoc/typehints.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `emitReturnTypeEntry (hasReturnAnno returnInArgs : Bool) (returnAnnotation : List Char) (omitNoneReturnType : Bool)` | `modify_field_list(node, annotations, suppress_rtype=False)` — `sphinx/ext/autodoc/typehints.py:86` (the trailing `if 'return' in annotations and 'return' not in arguments:` block, body lines 128-138 post-patch) | modeled changed function #1: the return-type entry builder |
| `emitReturnTypeForKind (kind : List Char) (hasReturnAnno returnInArgs : Bool) (returnAnnotation : List Char)` | the `autodoc_typehints_description_target == "all"` dispatch arm of `merge_typehints(app, domain, objtype, contentnode)` — `sphinx/ext/autodoc/typehints.py:61` (post-patch lines 61-65) | modeled changed function #2: the kind-aware dispatcher that selects `suppress_rtype` |
| `isClassKind (kind : List Char)` | the predicate `objtype == 'class'` (`typehints.py:62` post-patch) | pure spec: whether the documented object is a class |
| `returnTypeEntry` / `returnTypeEntryForKind` (pure region) | the data assembled by the `nodes.field()/field_name('','rtype')/field_body('', paragraph('', annotation))` construction and its guard | pure spec: the appended return-type entry, abstracted to the text it carries (`some text`) or its absence (`none`) |

No pre-patch repo symbol is removed by the change; both hunks are additive
(`modify_field_list` gains a `suppress_rtype` parameter and an early-return
guard; `merge_typehints` gains an `if objtype == 'class'` branch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the rendered return-annotation string `annotations['return']` (a `str`, e.g. `"None"`, `"int"`) | `List Char` (`returnAnnotation`) | `s` (Python str) ↔ `s.toList`-shaped `List Char`; equality of texts ↔ `==` on `List Char`; the literal `"None"` ↔ `"None".toList` |
| the descriptor kind `objtype` (a `str`, e.g. `"class"`, `"function"`, `"method"`) | `List Char` (`kind`) | `objtype` str ↔ its `.toList`; `objtype == 'class'` ↔ `kind == "class".toList` (`isClassKind`) |
| `'return' in annotations` — the object has a return annotation | `Bool` (`hasReturnAnno`) | direct: present ↔ `true` |
| `'return' in arguments` — the description already declares a return type (an `rtype`/`returns` field was parsed) | `Bool` (`returnInArgs`) | direct: already-declared ↔ `true` |
| `suppress_rtype` (the new keyword arg) | `Bool` (`omitNoneReturnType`) | direct: suppress ↔ `true` |
| the appended `nodes.field` carrying the rtype (`field_name('','rtype')` + `field_body('', paragraph('', annotation))`), or no append | `Option (List Char)` | append-with-text-`t` ↔ `some t.toList`; no-append ↔ `none`. The entry's only content the F2P test observes is the rendered text (`"None"`); the surrounding `rtype` field/field_name structure is constant (I), so the entry is abstracted to its carried text. |

`modify_field_list`'s earlier loop (which fills `arguments` and appends
per-parameter `type`/`param` fields) is **unchanged** by the patch; the modeled
slice is exactly the final `if 'return' in annotations and 'return' not in
arguments:` block, whose two inputs (`'return' in annotations`,
`'return' not in arguments`) are carried as `hasReturnAnno`/`returnInArgs` (R).
The rendered annotation text `annotation = annotations['return']` is carried as
`returnAnnotation` (R). G-CONF exercises the real block to validate these R legs.

## 3. Callee provenance

**No axioms, no deep-model references.** Both modeled functions are closed
decisions over their inputs; the patch adds only control flow (`if objtype ==
'class'` and `if annotation == 'None' and suppress_rtype: return`) plus a passed
flag. There is **no unchanged library callee whose contract the proof must
axiomatize** and **no changed string/numeric operation modeled deeply** — the
entry-construction (`nodes.field()` …) is identical pre/post-patch and is an I
op carried as the `Option (List Char)` entry text. Hence `axiom_check.py` is a
no-axiom stub (G-AX = skip, mirroring the green sphinx-9229 bundle).

`'return' in annotations` and `'return' not in arguments` are dict/membership
reads on data the unchanged earlier code populates; they are R-carried Booleans,
exercised end-to-end against the real patched `modify_field_list` by G-CONF, not
axiomatized.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10449`** so the
consumer-side verdict is reproducible. The shadow transliterates
`returnTypeEntry`/`returnTypeEntryForKind` (R/I ops) to Python and diffs against
the REAL gold-patched `modify_field_list` (driven on a synthetic docutils
`field_list` whose appended rtype field, if any, is read back) — there are no
A-tagged callees, so the whole shadow is in scope for G-CONF.
