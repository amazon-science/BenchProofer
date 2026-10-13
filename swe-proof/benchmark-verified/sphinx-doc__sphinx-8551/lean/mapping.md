# mapping.md — sphinx-doc__sphinx-8551

## Symbol binding (file:line @ base_commit 57ed10c68057c96491acbd3e62254ccfaf9e3861)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_makeXref` / `problem_spec_makeXref` | `PyXrefMixin.make_xref` — the node-building step that turns an info-field type annotation into a cross-reference node | `sphinx/domains/python.py:269-284` |
| `RefContext` (pure type) | the relevant slice of `env.ref_context`: the values under keys `'py:module'` and `'py:class'` | `sphinx/domains/python.py:273-274` (post-patch), read from `env.ref_context.get(...)` |
| `XrefNode` (pure type) | the `result` node returned by `make_xref` (a `pending_xref`/refnode), restricted to the four attributes the modeled step writes: `reftarget`, `refspecific`, `py:module`, `py:class` | `sphinx/domains/python.py:271-284` |
| `XrefNode.refspecific` | `result['refspecific']` | `sphinx/domains/python.py:274` |
| `XrefNode.reftarget` | `result['reftarget']` | `sphinx/domains/python.py:271` (set by `super().make_xref`) / `:276` (rewritten on a sigil) |
| `XrefNode.pyModule` | `result['py:module']` | `sphinx/domains/python.py:273` (post-patch) |
| `XrefNode.pyClass` | `result['py:class']` | `sphinx/domains/python.py:274` (post-patch) |
| `hasSigil` / `strippedTarget` (pure helpers) | `if target.startswith(('.', '~')): prefix, result['reftarget'] = target[0], target[1:]` | `sphinx/domains/python.py:275-276` |

The modeled step is the construction of the cross-reference node for a type name
appearing in an object's info field. The patch makes this node record the
current namespace context (`py:module`, `py:class`) drawn from `env.ref_context`,
threading `env` into the call so that context is available.

### What the modeled step does

Base_commit `PyXrefMixin.make_xref`:
```python
result = super().make_xref(rolename, domain, target, innernode, contnode, env)
result['refspecific'] = True
if target.startswith(('.', '~')):
    prefix, result['reftarget'] = target[0], target[1:]
    ...
return result
```
`super().make_xref` builds a `pending_xref` whose `reftarget` is `target`.
`refspecific` is set, requesting scope-aware (`searchmode == 1`) resolution. At
base_commit the node carries NO namespace context (no `py:module` / `py:class`
key), so when the resolver (`PythonDomain.find_obj`, searchmode 1) sees an
unqualified name it skips the module/class-prefixed lookups and falls into the
"fuzzy" branch that matches the name in EVERY (sub)module — producing the
spurious "more than one target found" ambiguity the issue reports.

Post-patch adds:
```python
result['py:module'] = env.ref_context.get('py:module')
result['py:class'] = env.ref_context.get('py:class')
```
so the node records the current module and enclosing class. `find_obj` then
tries `modname + '.' + name` and `modname + '.' + classname + '.' + name` first,
resolving the unqualified name within the current scope exactly as an explicit
xref role does. (The second changed file, `sphinx/util/docfields.py:298`, only
threads `env=self.directive.state.document.settings.env` into the
`make_xrefs`→`make_xref` call so this `env` is non-`None`; it adds no behavior of
its own — see "Callee provenance".)

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| `env.ref_context.get('py:module')` | `ctx.module : Option String` | a string module name ↔ `some s`; a missing key / `None` ↔ `none`. |
| `env.ref_context.get('py:class')` | `ctx.cls : Option String` | enclosing class name ↔ `some s`; missing / `None` ↔ `none`. |
| the `target` string passed to `make_xref` | `target : String` | identity (UTF-8 string). |
| `result['refspecific']` | `XrefNode.refspecific : Bool` | `True` ↔ `true`. |
| `result['reftarget']` | `XrefNode.reftarget : String` | identity. |
| `result['py:module']` | `XrefNode.pyModule : Option String` | string ↔ `some`; `None` ↔ `none`. |
| `result['py:class']` | `XrefNode.pyClass : Option String` | string ↔ `some`; `None` ↔ `none`. |
| `target.startswith(('.', '~'))` | `hasSigil target` | `true` iff the target's first character is `.` or `~`. |
| `target[1:]` when a sigil is present, else `target` | `strippedTarget target` | drop the leading sigil character if present. |

Note: the modeled step also rewrites the visible link TEXT on a `~` sigil
(`for node in result.traverse(nodes.Text): …`). That display-text rewrite is
UNCHANGED by the patch and is not observed by the FAIL_TO_PASS test; the four
attributes above are exactly the node state the test asserts on (a `pending_xref`
with `refdomain="py"`, `reftype="class"`, `reftarget`, and
`**{"py:module": …, "py:class": …}`), so the model captures the patch's full
observable effect on node construction.

## Callee provenance + flag dependencies

- **`ctx.module`, `ctx.cls` — INPUTS, not callees.** They are the values
  `env.ref_context.get('py:module')` / `get('py:class')` return; the surrounding
  directive scope determines them (`py:module`/`py:currentmodule` and
  `py:class`). They are environmental inputs to the node-building step, modeled as
  its arguments. The patch READS them (it does not change how they are computed),
  so there is no unchanged pure callee whose contract the proof must consume: the
  `axioms` region declares no `opaque`/`axiom`.
- **`super().make_xref` — sets the initial `reftarget = target` and the
  `pending_xref` shell.** Its only attribute the modeled step observes
  (`reftarget`) is modeled directly (initialised to `target`, rewritten to
  `strippedTarget target` on a sigil); the patch does not change it. Modeled as
  the `result` initialiser (I), not axiomatized.
- **`sphinx/util/docfields.py` change — a plumbing edit, no behavior of its
  own.** Adding `env=self.directive.state.document.settings.env` to the
  `make_xrefs(...)` call only makes the `env` argument non-`None` at the
  `make_xref` call site (so `env.ref_context.get(...)` can run). It introduces no
  computation modeled separately; it is the enabling half of the SAME single
  observable behavior (the node records its namespace context). It maps to the
  precondition "the surrounding namespace context `ctx` is available to the
  node-building step" — i.e. the `ctx` argument exists.
- **Flag dependencies.** None. The behavior is unconditional once the info-field
  type annotation is being cross-referenced; there is no config flag gating it.
  (The annotation path here is the `make_xrefs` call in `TypedField`/`PyTypedField`
  for `:type:`/`:param <type> name:`/`:rtype:` fields.)

## G-CONF fuzz seed

Pinned LCG seed: **8551** (see `conformance_check.py` `SEED`). Corpus: fuzzed
`(module, class, target)` triples — `module`/`class` drawn from
`{None, "example", "mod", "mod.submod", "Class", ""}` and `target` from a pool of
plain names and `.`/`~`-prefixed names — diffed against an in-process replica of
the post-patch `make_xref` attribute writes (driven through a real dict-backed
`ref_context` so the `.get(...)` ↔ `Option` bijection is exercised), ≥1e5
samples. G-AX is a skip stub (no consumed axiom; the surrounding context is an
input and every written node attribute is modeled directly, exercised by G-CONF).
