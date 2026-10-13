# mapping.md — sphinx-doc__sphinx-8638

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4b452338f914d4f6b54704222d70ae8a746e3db5`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderFieldEntry (name typ : List Char)` | the rendering of one entry of the `'variable'` info field — `PyTypedField('variable', …)` declared at `sphinx/domains/python.py:357-360`, rendered through `TypedField.make_field`'s `handle_item` (`sphinx/util/docfields.py:166-186`) | the modeled changed behaviour: how the variable NAME and its TYPE are turned into nodes |
| `crossRefOrText (refrole) (target)` *(deep model — A-reference)* | `Field.make_xref` (`sphinx/util/docfields.py:64-72`); reached via `PyXrefMixin.make_xref`/`make_xrefs` (`sphinx/domains/python.py:268-307`) | pure spec: the unchanged inline-rendering rule — produce a `pending_xref` when a role is given, else a plain text node |
| `RefNode` (`text` / `xref`) | a docutils inline node: `nodes.Text`/`literal_strong` (plain) vs `addnodes.pending_xref` (a navigable cross-reference) | the two node shapes whose distinction the behaviour constrains |
| `FieldEntry { nameNode, typeNode }` | the two cross-referenceable inline nodes the rendered entry contains: the one for the argument NAME and the one for the TYPE | observable content of one rendered field entry |

The pre-patch repo detail the change removes (refinement audit only, not in the
consumer spec view): the keyword argument `rolename='obj'` on the `'variable'`
`PyTypedField` (`sphinx/domains/python.py:357`). Removing it makes the field's
`rolename` default to `None`, so `make_field`/`handle_item` calls
`make_xrefs(self.rolename=None, …)` for the argument NAME, which produces a plain
text node instead of a `pending_xref`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the real repo objects. A wrong entry surfaces as spurious
G-CONF/G-AX disagreements (the falsifiability the plan §4 trust statement refers
to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the argument NAME string (e.g. `"attr"`) and the TYPE string (e.g. `"int"`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; empty `str` ↔ `[]` |

**Modeled input domain (the `require` clauses of `renderFieldEntry`).** The spec
models one entry whose NAME and TYPE are simple one-word identifiers: both are
non-empty, every character satisfies `isIdentChar` (letter / digit / `_`), and
the TYPE is not the literal word `None`. This pins the model to the rendering
path the patch changes and excludes three UNCHANGED, orthogonal repo behaviours
that produce a different node shape and would otherwise make the single-xref
model unfaithful:

1. `PyTypedField.make_xref` (`sphinx/domains/python.py:326-333`) special-cases
   `rolename == 'class' and target == 'None'` → rewrites the role to `'obj'`
   ("None is not a type"), so `typ = "None"` yields `('xref','obj','None')`,
   not `('xref','class','None')`. Excluded by `require typ ≠ "None".toList`.
2. `PyXrefMixin.make_xref` (`python.py:275-290`) strips a leading `'.'`/`'~'`
   from the target (`typ = "~pkg.Cls"` → `reftarget = "pkg.Cls"`). Excluded:
   `'.'`/`'~'` are not `isIdentChar`.
3. `PyXrefMixin.make_xrefs` (`python.py:292-307`) splits the target on the
   delimiter regex `[\[\](),]` / `or`, yielding SEVERAL nodes for e.g.
   `typ = "a or b"`. Excluded: spaces/brackets/commas are not `isIdentChar`,
   and a one-word identifier never matches the delimiter split.

All three behaviours predate the patch and are byte-identical before and after
it; the gold change (dropping `rolename='obj'` for the NAME) is fully exercised
inside the modeled domain, which also contains the F2P test's input
(`name="attr"`, `typ="int"`).
| a docutils inline node that is a plain text/strong node (no `refuri`/`reftarget`, no `pending_xref` ancestor) | `RefNode.text content` | observed by: the node is NOT a `pending_xref` ⇒ `text`; its text content ↔ `content` |
| a docutils `addnodes.pending_xref` with `reftype=r`, `reftarget=t` | `RefNode.xref r t` | observed by: the node IS a `pending_xref` ⇒ `xref`; `reftype` ↔ `refkind`, `reftarget` ↔ `target` |
| the reference role configured for a field argument (`Field.rolename` / `typerolename`) | `Option (List Char)` | `None` ↔ `none`; a non-empty role string `r` ↔ `some r.toList`; an empty string is treated as no role (`crossRefOrText` maps `some []` to `text`, matching `Field.make_xref`'s `if not rolename` guard) |

The `'variable'` field's argument role: post-patch `rolename=None` ↔ `none`
(NAME rendered as `text`); the TYPE role `typerolename='class'` is UNCHANGED ↔
`some "class".toList` (TYPE rendered as `xref "class"`).

## 3. Callee provenance (deep-model reference — checked by G-AX / axiom_check.py)

### 3.1 `crossRefOrText` deep model ↔ `Field.make_xref` (A-reference)
**Callee:** `sphinx.util.docfields.Field.make_xref` (UNCHANGED by the patch).
Source at base_commit (`sphinx/util/docfields.py:64-72`):

```python
def make_xref(self, rolename, domain, target, innernode=..., contnode=None, env=None):
    if not rolename:
        return contnode or innernode(target, target)          # plain inline text node
    refnode = addnodes.pending_xref('', refdomain=domain, refexplicit=False,
                                    reftype=rolename, reftarget=target)
    refnode += contnode or innernode(target, target)
    ...
    return refnode                                            # a navigable cross-reference
```

The rendering rule the patch toggles is purely *which `rolename` is passed* for
the variable-field NAME; `make_xref` itself is unchanged. `crossRefOrText`
models that unchanged rule deeply: a falsy/empty role ⇒ plain text node
(`RefNode.text`); a truthy role `r` ⇒ a `pending_xref` of kind `r`
(`RefNode.xref r`). There is **no consumed axiom**; the equality of this deep
model to the real `make_xref` is the A-reference G-AX validates.

**Soundness check (G-AX):** `axiom_check.py` constructs the real `PyTypedField`
configurations and drives the real `Field.make_xref` on boundary roles
(`None`, `''`, `'obj'`, `'class'`, `'data'`, fuzzed role/target strings),
asserting `crossRefOrText`'s node-shape (`text` vs `xref reftype reftarget`)
matches the real node (plain inline vs `pending_xref` with that `reftype`/
`reftarget`). It also asserts the post-patch `'variable'` field carries
`rolename is None` and `typerolename == 'class'`. stdlib + docutils + sphinx
(the repo under test) only. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8638`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `crossRefOrText`/`renderFieldEntry` (R/I-tagged ops) to Python and
compares against the ORACLE: the real patched Sphinx rendering of a
`:var TYPE NAME:` info field (the patch.diff behaviour), observing, for the
single rendered entry, whether the NAME node is a `pending_xref` (and of what
`reftype`/`reftarget`) and whether the TYPE node is a `pending_xref` of
`reftype='class'` to the type string. There are no A-tagged callees in the impl
region, so the shadow is pure R/I. The fuzz generator draws inputs from exactly
the spec's modeled domain (§2): non-empty `[A-Za-z0-9_]+` names/types with the
literal type `"None"` remapped, matching the `require` clauses.
