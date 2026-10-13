# mapping.md — sphinx-doc__sphinx-8551

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 57ed10c68057c96491acbd3e62254ccfaf9e3861`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
resolver checked by G-AX / axiom_check.py).

Repo files under change: `sphinx/domains/python.py`, `sphinx/util/docfields.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `make_field_ref(target, cur_module, cur_class, objs)` | `PyXrefMixin.make_xref` — `sphinx/domains/python.py:269-284` (the changed hunk: lines 274-275 add `result['py:module']`/`result['py:class']`); together with the call-site fix `DocFieldTransformer.transform` — `sphinx/util/docfields.py:293-298` (the changed hunk adds `env=self.directive.state.document.settings.env`) | the modeled changed function: build the implicit field xref node carrying the surrounding namespace context |
| `RefNode` (`target`, `specific`, `ctx_mod`, `ctx_cls`) | the `addnodes.pending_xref` node built in `make_xref` (`reftarget`, `refspecific`, `py:module`, `py:class` attributes) | minimal node carrying only the touched attributes |
| `resolve_count` / `resolve_name` / `has_ctx_candidate` / `first_suffix` / `member` / `count_suffix` / `suffix_eq` *(deep model — A-reference)* | `PythonDomain.find_obj(env, modname, classname, name, type, searchmode=1)` — `sphinx/domains/python.py:1236-1290`, prefer-specific branch lines 1252-1273; called from `resolve_xref` (`searchmode = 1 if node.hasattr('refspecific')`, lines 1295-1299) | pure spec: the prefer-specific name-resolution cascade; the deep model of the unchanged resolver, validated `resolve_* == find_obj` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo state (for the refinement audit, not referenced from the
consumer spec view): `make_xref` set `result['refspecific'] = True` but did NOT
copy `env.ref_context.get('py:module')`/`('py:class')` onto the node; and the
type-link branch of `DocFieldTransformer.transform` (`docfields.py:289-307`)
called `typed_field.make_xrefs(..., contnode=content[0])` WITHOUT `env=...`, so
the implicit xref was built with `env=None` and no context at all. The resolver
therefore received `modname=None, classname=None` (line 1295-1296) and fell
straight through to the suffix ("fuzzy") fallback (lines 1269-1273).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a dotted qualified name, e.g. `"mod.submod.A"` (the `str` `reftarget`, `py:module`, `py:class`, and the keys of `self.objects`) | `PSeq[int]` of segment tokens, e.g. `PSeq(1,2,3)` | each dotted name ↔ the sequence of its segments; `"a.b" + "." + "c"` (string join) ↔ `PSeq(a)+PSeq(b)+PSeq(c)` sequence concatenation; an unqualified name is a length-1 (or the bare) sequence. Distinct segment strings ↔ distinct ints (an injective interning); equality/`endswith('.'+name)`/prefix tests are preserved exactly. |
| `py:module` / `py:class` context, which may be absent | `Optional[PSeq[int]]` (`None` ↔ `env.ref_context.get(...)` returning `None`) | `None` ↔ no surrounding module/class; a present context ↔ its segment sequence |
| `self.objects` dict (`fullname -> ObjectEntry`) | `PSeq[PSeq[int]]` of the registered qualified names | only the *key set* (and, for the fuzzy fallback, its iteration order) is observed by `find_obj` in searchmode 1; `objtype ∈ objtypes` is constant `True` for the modeled `class`/`obj` role lookups (all registered objects are class-like in the F2P scenario), so the objtype filter is the identity and is omitted |
| `find_obj`'s return list of `(name, ObjectEntry)` tuples | the count (`resolve_count`) + the single resolved name (`resolve_name`) | `find_obj` returns 0, 1, or ≥2 matches; the observable the issue cares about is "exactly one match (the contextual object)" vs "≥2 matches (ambiguous → WARNING)". `resolve_count` is `len(find_obj(...))`; `resolve_name` is the single match when count == 1. |

`str` indexing/iteration is banned in Nagini, so qualified names are carried as
`PSeq[int]` of segment tokens; the cascade is phrased over `PSeq`/`PSeq[PSeq]`.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### `resolve_*` deep model ↔ `PythonDomain.find_obj(searchmode=1)`

**Callee:** `PythonDomain.find_obj` (`sphinx/domains/python.py:1236-1290`),
prefer-specific branch (`searchmode == 1`, lines 1252-1273). The patch does NOT
change `find_obj`; it changes *what context is fed to it* by attaching
`py:module`/`py:class` to the node. The resolution cascade is therefore an
**unchanged callee**, modeled DEEPLY (there is no consumed `find_obj` axiom).

Source (verbatim, lines 1252-1273):

```python
if searchmode == 1:
    ...
    if objtypes is not None:
        if modname and classname:
            fullname = modname + '.' + classname + '.' + name
            if fullname in self.objects and self.objects[fullname].objtype in objtypes:
                newname = fullname
        if not newname:
            if modname and modname + '.' + name in self.objects and \
               self.objects[modname + '.' + name].objtype in objtypes:
                newname = modname + '.' + name
            elif name in self.objects and self.objects[name].objtype in objtypes:
                newname = name
            else:
                # "fuzzy" searching mode
                searchname = '.' + name
                matches = [(oname, self.objects[oname]) for oname in self.objects
                           if oname.endswith(searchname) and
                           self.objects[oname].objtype in objtypes]
```

This is exactly the model's cascade:

  `module.class.name` (if both present) → `module.name` (if module present) →
  `name` → suffix fallback `{ o : o.endswith("."+name) }`.

`has_ctx_candidate` ⇔ a `newname` is set by one of the three qualified branches;
`resolve_count` ⇔ `len(matches)` (`1` when `newname` is set, else the size of
the fuzzy set); `resolve_name` ⇔ the single `matches[0][0]` when there is one
(`newname`, or the unique suffix match). Note `modname and classname` (line
1258) means the class-qualified candidate is only tried when the **module** is
also present — `resolve_*` gate the `mod+cls+name` branch on `mod is not None`,
matching this exactly.

**Flag/config dependency:** the relevant path is `searchmode == 1`, set by
`resolve_xref` iff the node `hasattr('refspecific')` (line 1297); the patched
`make_xref` sets `result['refspecific'] = True` (unchanged line 274), so the
implicit field xrefs always resolve in prefer-specific mode. The objtype filter
(`self.objects[...].objtype in objtypes`) is the identity for the class-like
objects the F2P scenario registers; G-AX registers objects as `class` objtype
and looks them up with `type='class'` (objtypes = `['class', 'exception']`),
exercising the real filter.

**Soundness check (G-AX):** `axiom_check.py` constructs a REAL `PythonDomain`
(populating only the attributes `find_obj` reads — `objects`, `object_types`,
`objtypes_for_role`), runs the unmodified `find_obj` with `searchmode=1`, and
asserts that for every input `len(find_obj(...)) == resolve_count(...)` and,
when that is 1, the single returned qualified name equals `resolve_name(...)`.
Coverage: the issue scenario (same simple class name under `mod` and
`mod.submod`, looked up with/without module + class context), 20000 randomized
multi-segment fuzz cases, and an exhaustive subset sweep. Exit 0 iff sound.
Validated here against the worktree sphinx: 0 mismatches.
