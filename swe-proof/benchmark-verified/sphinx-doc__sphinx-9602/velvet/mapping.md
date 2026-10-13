# mapping.md — sphinx-doc__sphinx-9602

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6c38f68dae221e8cfc70c137974b8b88bd3baaab`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model references.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `literalTypeNodes (head : List Char) (values : List LitVal)` | `_parse_annotation(annotation, env)` — `sphinx/domains/python.py:109` (the `ast.Subscript` branch at lines 150-154 and the top-level node-rewrite loop at lines 182-188) | the modeled changed function: builds the inline child nodes rendered for a parametrised type annotation; this bundle models it on the parametrised-by-constants subdomain (a `Literal[...]`) |
| `reprVal` *(deep model — A-reference)* | the constant-rendering call `repr(node.value)` introduced by the patch in the `ast.Constant` branch (`python.py:126` post-patch) — i.e. Python builtin `repr` on the constant object | pure spec: the source-form display text of one constant value |
| `expandLiteral` / `wrap` / `valSeq` *(deep model — A-reference)* | the full node sequence the patched `_parse_annotation` emits for a `Literal[...]` annotation: head cross-reference, `[`, the comma-separated value nodes (each PLAIN inline text), `]` | pure spec: the rendered node sequence of a constant-parametrised type; validated == the patched real callee by `conformance_check.py` (G-CONF) |
| `DocNode` (inductive: `text`/`xref`/`punct`) | the `docutils`/`sphinx.addnodes` inline node carriers (`nodes.Text`, `addnodes.pending_xref`, `addnodes.desc_sig_punctuation`) | the only node shapes the renderer emits over this domain, modeled by the observed fields (display text / cross-reference target) |
| `LitVal` (inductive: `bool`/`int`/`str`) | the `ast.Constant.value` of each subscript argument — a `bool`, `int`, or `str` Python object | the constant kinds a `Literal[...]` annotation in scope carries |

The pre-patch behaviour the change replaces (refinement audit only, not in the
consumer spec view): each constant rendered via the bare value (`nodes.Text(node.value)`)
without its source delimiters, and every non-blank inline text node — including
the rendered constant values inside the brackets — rewritten into a
cross-reference by the top-level loop, so e.g. a boolean value became a
(broken) class reference.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the head of the annotation, e.g. `"Literal"`, `"typing.Literal"`) | `List Char` | `s` (Python str) ↔ `s.toList`; on the BMP `Char.ofNat (ord ch)` ↔ `ch`, total and exact |
| an `ast.Constant.value` that is a `bool` | `LitVal.bool b` | `True ↔ LitVal.bool true`, `False ↔ LitVal.bool false` |
| an `ast.Constant.value` that is an `int` | `LitVal.int n` | the Python integer ↔ the Lean `Int`; decimal source form ↔ `toString n` |
| an `ast.Constant.value` that is a `str` (simple — see `okLit`) | `LitVal.str s` | the Python string ↔ `s.toList`; only "simple" strings (printable-ASCII, no `'`/`\`) are in scope, where `repr` is single-quoted with no escapes |
| `repr(value)` (the constant's display text) | `reprVal v` | `repr(True)="True"`, `repr(False)="False"`, `repr(n)=str(n)`, `repr(simple_str s) = "'" + s + "'"` |
| `nodes.Text(s)` | `DocNode.text s.toList` | only the display text is observed (the F2P test compares node-class + text) |
| `addnodes.pending_xref(..., reftarget=t)` | `DocNode.xref t.toList` | a cross-reference node; only the visible text / reference target is observed |
| `addnodes.desc_sig_punctuation('', s)` | `DocNode.punct s.toList` | a punctuation node (`[`, `]`, `, `) emitted around / between the arguments |
| the returned `List[Node]` of `_parse_annotation` | the returned `List DocNode` | `out` IS that node sequence, child for child (class + text) |

`List Char` indexing is total and sound; the carriers are `List Char` / `List
DocNode` / `List LitVal` because the operation is per-element over the argument
sequence.

## 3. Callee provenance (deep-model references — checked by G-AX / G-CONF)

### 3.1 `reprVal` ↔ Python `repr` (A-reference, G-AX)
**Callee:** Python builtin `repr`, called by the patch as `repr(node.value)` to
render each constant value's display text. `repr` is UNCHANGED by the patch
(only the *call to it* is added). On the modeled domain — `bool`, `int`, and
"simple" `str` (`okLit`: printable-ASCII excluding `'` and `\`) — `repr`
produces exactly: `True`/`False` for booleans, the decimal digits for integers,
and a single-quoted, escape-free form for strings. `reprVal` encodes precisely
this. `axiom_check.py` runs the REAL `repr` on boundary values (the booleans,
small/large/negative integers, the issue's `'abc'`, empty and spaced strings)
plus randomized fuzz and asserts `reprVal(v) == repr(python_value(v))` for every
`v`. G-AX runs WITHOUT the gold patch — `repr` is a builtin available at
base_commit — so this A-reference is validated against the genuinely-unchanged
callee.

### 3.2 head cross-reference ↔ `type_to_xref` (carrier check, G-AX)
**Callee:** `sphinx.domains.python.type_to_xref` (UNCHANGED by the patch). The
top-level loop rewrites the head text node (`Literal` / `typing.Literal`) into a
`pending_xref` whose target is that head string. `axiom_check.py` constructs a
minimal `env` (`python_use_unqualified_type_names=False`, empty `ref_context`)
and asserts `type_to_xref(head, env)` is a `pending_xref` with visible text and
`reftarget` equal to `head` — confirming the `DocNode.xref head` modeling of the
head node. Available at base_commit (unchanged).

### 3.3 `expandLiteral` ↔ patched `_parse_annotation` (A-reference, G-CONF)
The full node sequence is the deep model of the CHANGED callee, so its
equivalence to the real function is validated by `conformance_check.py` (G-CONF)
**with the gold patch applied** (the changed function gives the buggy result at
base_commit, so the equivalence can only be checked against the patched repo).
G-CONF builds the `expandLiteral` shadow and diffs it node-for-node (class +
text) against `_parse_annotation("<head>[<values>]", env)` over ≥10⁵ fuzzed
`Literal[...]` annotations.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9602`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl region's ops — head `xref`, bracket/comma `punct`, and one `text` node
per value carrying `reprVal v` — to Python node fingerprints `(class, astext)`,
leaving the A-reference content (`reprVal` ↔ `repr`, the whole-function
equivalence) to be exercised against the real patched `_parse_annotation`. The
oracle is the patched `_parse_annotation("<head>[<values>]", env)` child list.
They must agree (node-class + text) on every annotation.
