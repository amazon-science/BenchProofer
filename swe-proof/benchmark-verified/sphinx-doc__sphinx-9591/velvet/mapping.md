# mapping.md — sphinx-doc__sphinx-9591

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9ed054279aeffd5b1d0642e2d24a8800389de29f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one axiom.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `propertyTypeNodes (typ : List Char)` | `PyProperty.handle_signature` — `sphinx/domains/python.py:859` (body, the `if typ:` branch at lines 862-864) | the modeled changed function: builds the inline children of a documented property's type-annotation node |
| `annotationNodes` *(axiom — A-consumed)* | `_parse_annotation` — `sphinx/domains/python.py:110` | UNCHANGED callee: parses a type-annotation string into a list of inline nodes, turning each bare type name into a cross-reference. Already used pre-patch by the variable/attribute siblings (`python.py:664`, `python.py:825`); the patch routes the property branch through it too. |
| `DocNode` (inductive: `text`/`xref`/`punct`) | the `docutils`/`sphinx.addnodes` inline node carriers (`nodes.Text`, `addnodes.pending_xref`, `addnodes.desc_sig_punctuation`) | the only node shapes `_parse_annotation` emits, modeled by the touched fields (text content / cross-reference target) |

The pre-patch construction the change replaces (refinement audit only, not in the
consumer spec view): `addnodes.desc_annotation(typ, ': ' + typ)` — a single inert
text node `': ' + typ` (`python.py:864` @ base_commit).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the `typ` option string) | `List Char` | `s` (Python str) ↔ `s.toList`; `': ' + typ` ↔ `": ".toList ++ typ`; concat ↔ `List` `++` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `nodes.Text(s)` | `DocNode.text s.toList` | only the text content is observed (the F2P test compares `[desc_annotation, (": ", ...)]` by node-class + text) |
| `addnodes.pending_xref(..., reftarget=t, ...)` | `DocNode.xref t.toList` | a cross-reference node; only the reference target (its visible text/target) is observed |
| `addnodes.desc_sig_punctuation('', s)` | `DocNode.punct s.toList` | a punctuation node (`[`, `]`, `, `, `|`) emitted inside compound annotations |
| `addnodes.desc_annotation(typ, '', Text(': '), *annotations)` | the returned `List DocNode` = its child sequence | the wrapping `desc_annotation` is identity over its children for what the test observes; `out` IS the child list `[Text(': '), *annotations]` |

The first two positional args of `desc_annotation(rawsource, text, *children)` are the
rawsource string (`typ`) and the auto-text (`''` → contributes no child); hence the
children are exactly `Text(': ')` followed by the unpacked `annotations`. That child
list is what `propertyTypeNodes` returns.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `annotationNodes` ↔ `_parse_annotation` (A-consumed)
**Callee:** `sphinx.domains.python._parse_annotation(annotation, env)` (UNCHANGED by
the patch). It `ast`-parses the annotation string and, for every produced `nodes.Text`
that is a non-blank type name, replaces it with `type_to_xref(...)` → a
`pending_xref` (`python.py:181-184`). For a bare identifier annotation (no brackets,
dots, operators) the parse yields a single `ast.Name`, so the result is exactly one
cross-reference node targeting that name.

The Lean axiom encodes only the obligation the proof consumes — the **weakest**
contract sufficient: a bare type name renders to a single cross-reference node, NOT to
inert text. Concretely `annotationNodes "int".toList = [DocNode.xref "int".toList]`
(the witness identifier `int` is a public type name from the issue's reproducer; G-AX
checks the same fact for many identifiers). This is the discriminator: the pre-patch
code emitted a `text` node, so the round-tripped annotation could never become a
cross-reference. `annotationNodes` is left opaque otherwise (no deep model), so any
impl that does not actually call it fails to satisfy the structural postcondition.

**Soundness check (G-AX):** `axiom_check.py` constructs a minimal `env`
(`python_use_unqualified_type_names=False`, empty `ref_context`) and runs the REAL
`_parse_annotation` on boundary identifiers (`int`, `str`, `Point`, `bool`, `bytes`,
…) plus randomized identifier fuzz, asserting each returns exactly one node that is a
`pending_xref` whose reference target equals the input (the A-consumed obligation). It
additionally checks the broader structural model on compound annotations
(`Optional[str]`, `Dict[str, int]`, `a.b.C`) — that every emitted node is one of
text / pending_xref / desc_sig_punctuation and type names become xrefs — to confirm
the `DocNode` carrier is faithful. Imports only `sphinx.domains.python` +
`docutils`/`sphinx.addnodes`. Exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9591`** so the consumer-side
verdict is reproducible. The R/I shadow it builds transliterates the impl region's
**I** op — prepend `Text(': ')` to the parsed nodes and return that child sequence —
to Python, leaving the **A**-tagged callee `annotationNodes` as the REAL
`_parse_annotation` (mapping §3.1). The oracle is the patched expression
`addnodes.desc_annotation(typ, '', nodes.Text(': '), *_parse_annotation(typ, env))`'s
child list (patch.diff behaviour). They must agree (node-class + text content) on every
type string.
