# mapping.md — sphinx-doc__sphinx-10449

## Symbol binding (file:line @ base_commit)

base_commit: `c4b9af9f7f5c081a86d9b69cc1da3 ...` (the materialized worktree at
`$SCRATCH`).

- Modeled function: the field-list population routine in
  `sphinx/ext/autodoc/typehints.py` — `modify_field_list`
  (`sphinx/ext/autodoc/typehints.py:86-130` @ base_commit). It scans an existing
  docutils `field_list`, then APPENDS `type`/`param` fields for every recorded
  type-hint annotation, and finally a `rtype` field for the return annotation.
- The gold fix adds a boolean parameter to that routine; when the parameter is
  set and the return annotation is the unit/`None` annotation, the `rtype` field
  is NOT appended. The caller (`merge_typehints`,
  `sphinx/ext/autodoc/typehints.py:37-70`) sets that boolean exactly when the
  documented object is a class.
- The Lean name `render_typehint_fields` is a de-narrated alias for that routine
  (it does NOT echo the patched repo symbol). The Lean parameter
  `suppressTrivialReturn` is a de-narrated alias for the new gold parameter (it
  does NOT echo the gold-diff identifier `suppress_rtype`).

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

A docutils `nodes.field` is observed only through its `field_name` text (the
first child, `field[0].astext()`) and its `field_body` paragraph text. We model
a field as `Field := { name : String, body : String }`.

| Lean | Python |
|---|---|
| `Field.name` | `field[0].astext()` — the field-name text, e.g. `"type x"`, `"param x"`, `"rtype"` |
| `Field.body` | the field body paragraph text (`field[1].astext()` of the appended `nodes.paragraph`) |
| `existing : List Field` | the fields already present in `node` before the routine appends, captured `[ {name: f[0].astext(), body: f[1].astext()} for f in list(node) ]` |
| `annotations : List (String × String)` | `annotations` dict (an `OrderedDict`) as ordered `(name, annotation)` pairs; keys unique |
| `suppressTrivialReturn : Bool` | the new gold boolean parameter (`= (objtype == 'class')` at the call site) |
| `result : List Field` | the field list of `node` AFTER the routine returns, as `[ {name,body} ]` in order |
| `tokenize s` | `[p for p in re.split(' +', s) if p]` (runs of spaces ⇒ empty tokens dropped) |
| `declaresType existing nm` | name `nm` has `arguments[nm]['type']` set by the scan loop |
| `declaresParam existing nm` | name `nm` has `arguments[nm]['param']` set |
| `hasReturnField existing` | `'return' in arguments` — true for an `rtype` field, and ALSO for any `type return`, `param return`, or `param <kind> return` field (the scan records those under the name `'return'` too) |
| `lookupReturn annotations` | `annotations.get('return')` |

### Scan-loop bijection (`arguments` dict)

The Python scan loop classifies each existing field by `parts = re.split(' +',
field_name)` and `parts[0]`:
- `param` with exactly 2 parts → `arguments[parts[1]]['param']=True`;
- `param` with >2 parts → name = `' '.join(parts[2:])`, sets both `param` and `type`;
- `type` → name = `' '.join(parts[1:])`, sets `type`;
- `rtype` → `arguments['return']={'type':True}`.

Because the dict is keyed by NAME, a field whose declared name is literally
`return` (`type return`, `param return`, `param <kind> return`) also populates
`arguments['return']`, so the final `'return' not in arguments` guard treats it
as an already-declared return type. `isReturnField` therefore matches `rtype …`
OR `declaresTypeField f "return"` OR `declaresParamField f "return"` — exactly
mirroring which fields make `'return' in arguments` true. (`param return` with
only 2 tokens sets only `['param']`, but key `'return'` still enters the dict,
which is all the guard tests.)

`declaresType existing nm` is true iff some existing field is a `type nm` field
or a 3+-token `param … nm` field. `declaresParam existing nm` is true iff some
existing field is a `param nm` (2-token) or `param … nm` (3+-token). These
mirror the dict exactly.

Domain note (G-CONF fuzz restriction): field names contain no leading/trailing
spaces (docutils builds them from `nodes.field_name('', 'type ' + name)` etc.),
so `tokenize` = `re.split(' +', ·)` agree. Annotation keys are unique (dict).

## Callee provenance + flag deps

- No unchanged callee is consumed as an axiom. The scan/parse and the
  type/param/rtype generation are all modeled deeply (element-wise). The docutils
  `nodes.field`/`field_name`/`paragraph` constructors are pure data builders whose
  result we observe as `Field` records — taken as the modeled output, not
  axiomatized.
- Flag dependency: the new boolean is `True` exactly for `objtype == 'class'`
  (caller `merge_typehints`). G-CONF drives the routine directly with the boolean
  fuzzed 50/50; the `objtype == 'class'` derivation is documented here and exercised
  by the gold patch / harness (G-RESOLVE).
- The latent pre-fix bug where the `rtype` body used the loop-leftover
  `annotation` variable instead of `annotations['return']` is also corrected by
  the gold patch (`annotation = annotations['return']`); the modeled routine uses
  the return annotation directly (`lookupReturn`). It is not an independently
  F2P-tested behavior, so it is folded into the (R) rtype-body mapping rather than
  given its own prepatch.

## G-CONF fuzz seed

Pinned seed: `10449` (`random.Random(10449)`), N = 100000.
