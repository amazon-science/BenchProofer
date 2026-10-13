# mapping.md — sphinx-doc__sphinx-9673

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 5fb51fb1467dc5eea7505402c3c5d9b378d3b441
- changed file: `sphinx/ext/autodoc/typehints.py`, function `augment_descriptions_with_types`
- spec_provenance: cold

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_augment` / `problem_spec_augment` / `correct_augment` | `augment_descriptions_with_types(node, annotations)` | `sphinx/ext/autodoc/typehints.py:130-173` |
| `classify` / `classifyStep` (pure) | the marker-classification loop building `has_description` / `has_type` | `typehints.py:137-155` |
| `outStep` / `augmentSpec` (pure) | the back-fill loop appending `type <name>` fields + the trailing `rtype` field | `typehints.py:157-173` |
| `joinSp` (pure) | `' '.join(parts[k:])` | `typehints.py:146,151` |

## Callee provenance / inputs

`augment_descriptions_with_types` is invoked from `merge_typehints` (same file,
line 67) with `node = field_list` and `annotations = annotations[fullname]`
(an `OrderedDict[str, str]`). The function:

```python
def augment_descriptions_with_types(node, annotations):
    fields = cast(Iterable[nodes.field], node)
    has_description = set(); has_type = set()
    for field in fields:
        field_name = field[0].astext()
        parts = re.split(' +', field_name)
        if parts[0] == 'param':
            if len(parts) == 2:        has_description.add(parts[1])
            elif len(parts) > 2:       name=' '.join(parts[2:]); has_description.add(name); has_type.add(name)
        elif parts[0] == 'type':       has_type.add(' '.join(parts[1:]))
        elif parts[0] in ('return','returns'):  has_description.add('return')   # <-- gold hunk 1
        elif parts[0] == 'rtype':      has_type.add('return')
    for name in annotations:
        if name in ('return','returns'):  continue                              # <-- gold hunk 2
        if name in has_description and name not in has_type:
            <append a `type <name>` field carrying annotations[name]>
    if 'return' in annotations:
        if 'return' in has_description and 'return' not in has_type:
            <append an `rtype` field carrying annotations['return']>
```

The two inputs the modeled logic reads are produced by the caller/environment,
NOT computed by the fix:
- the **field markers** — each `field[0].astext()` already split by
  `re.split(' +', …)` into whitespace-separated tokens. Modeled as the abstract
  input `fields : List (List String)` (one inner list per marker, already split).
  `re.split(' +', s)` is the environment-supplied tokenizer; the fix does not
  change it, so the tokenization is supplied, not modeled.
- the **annotations table** — the `OrderedDict[str,str]` name→type-text mapping
  built earlier by `record_typehints`. Modeled as the abstract ordered input
  `annotations : List (String × String)` (insertion order preserved, as the
  `OrderedDict` iteration order is observable in the output field order).

No `opaque`/`axiom` callee is declared: `re.split`, `set.add`, `nodes.field*`,
`astext` are not modeled as callees — only the classification + back-fill
decision logic is the fix, and it is modeled DEEPLY. The constructed
`nodes.field` objects are observed only by their *kind* and *text*; the result
is modeled as the ordered list of appended `(field_name, text)` pairs
`result : List (String × String)`.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| one field marker, `re.split(' +', field[0].astext())` | inner `List String` of `fields` | token list, identity |
| the field list (markers) | `fields : List (List String)` | order-preserving |
| `annotations : OrderedDict[str,str]` | `annotations : List (String × String)` | insertion order preserved |
| `has_description : set[str]` | `hasDesc : List String`, membership via `.contains` | set membership ↔ `List.contains`; order irrelevant to membership |
| `has_type : set[str]` | `hasType : List String`, membership via `.contains` | as above |
| `' '.join(parts[k:])` | `joinSp (parts.drop k)` = `String.intercalate " "` | identity |
| appended `type <name>` field carrying `annotations[name]` | `("type " ++ name, ann)` | field-name string ↔ `"type "++name`; body text ↔ `ann` |
| appended `rtype` field carrying `annotations['return']` | `("rtype", ann)` | identity |
| the appended-field list | `result : List (String × String)` | order-preserving |

Note: `has_description`/`has_type` are Python **sets** — duplicate adds collapse
and order is irrelevant. The Lean model uses `List` with `.contains` for the
only observable (membership), so it is a faithful set model for the queries the
fix performs (`name in has_description`, `name not in has_type`).

## Flag dependencies
None. `augment_descriptions_with_types` is the branch taken when
`autodoc_typehints_description_target != "all"` (caller `merge_typehints`); within
it, no configuration flag selects which marker keyword is recognized — the gold
simply widens the return-keyword match from one spelling to two.

## G-CONF fuzz seed
`SEED = 9673` (pinned in conformance_check.py).
