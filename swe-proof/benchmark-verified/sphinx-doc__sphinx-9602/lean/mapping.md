# mapping.md — sphinx-doc__sphinx-9602

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6c38f68dae221e8cfc70c137974b8b88bd3baaab`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model references.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `implementation_literalTypeNodes (head : List Char) (values : List LitVal)` / `problem_spec_literalTypeNodes` / `correct_literalTypeNodes` | `_parse_annotation(annotation, env)` — `sphinx/domains/python.py:109` (the `ast.Subscript` branch at lines 150-154 and the top-level node-rewrite loop at lines 182-188) | the modeled changed function: builds the inline child nodes rendered for a parametrised type annotation; this bundle models it on the parametrised-by-constants subdomain (a `Literal[...]`) |
| `reprVal` *(deep model — A-reference)* | the constant-rendering call `repr(node.value)` introduced by the change in the `ast.Constant` branch (`python.py:126` post-change) — i.e. Python builtin `repr` on the constant object | pure spec: the source-form display text of one constant value |
| `expandLiteral` / `wrap` / `valSeq` *(deep model — A-reference)* | the full node sequence the changed `_parse_annotation` emits for a `head[...]` annotation whose arguments are constants: head cross-reference, `[`, the comma-separated argument nodes, `]` | pure spec: the rendered node sequence of a constant-parametrised type; validated == the real callee by `conformance_check.py` (G-CONF) |
| `isHeadStartChar` / `isHeadTailChar` / `pyReservedWords` / `headSegments` / `okHeadSeg` / `okHead` | the shape of the head string `result[0]` for which `_parse_annotation` produces a parametrised type at all — a dotted Python name, i.e. dot-separated identifier segments that are not reserved words | pure spec: the head domain the signature covers. Not a way to exclude inputs: it is the largest domain on which the modeled sequence is exact, and it spans BOTH sides of the head test |
| `isLitHead` / `argNodeCtor` | the `result[0] in ('Literal', 'typing.Literal')` test of hunk 2, and the two legs of hunk 3's dispatch it selects between | pure spec: which node class an ARGUMENT of `head[...]` carries — plain inline text under the enumeration head, a cross-reference under every other dotted head. This is the changed control-flow op, modeled on both branches (refinement.md row 1b) |
| `DocNode` (inductive: `text`/`xref`/`punct`) | the `docutils`/`sphinx.addnodes` inline node carriers (`nodes.Text`, `addnodes.pending_xref`, `addnodes.desc_sig_punctuation`) | the only node shapes the renderer emits over this domain, modeled by the observed fields (display text / cross-reference target) |
| `LitVal` (inductive: `null`/`bool`/`int`/`str`) | the `ast.Constant.value` of each subscript argument — `None`, or a `bool`, `int`, or `str` Python object | the constant kinds a parametrised annotation in scope carries. `null` is the constant the non-enumeration rows exercise (`List[None]`) |

The prior behaviour the change replaces (refinement audit only, not in the
consumer spec view): each constant rendered via the bare value
(`nodes.Text(node.value)`) without its source delimiters, and every non-blank
inline text node — including the rendered constant values inside the brackets —
rewritten into a cross-reference by the top-level loop, so e.g. a boolean value
became a (broken) class reference.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the head of the annotation, e.g. `"Literal"`, `"typing.Literal"`) | `List Char` | `s` (Python str) ↔ `s.toList`; on the BMP `Char.ofNat (ord ch)` ↔ `ch`, total and exact |
| an `ast.Constant.value` that is `None` | `LitVal.null` | `None ↔ LitVal.null`; source form and `repr` are both `None` |
| an `ast.Constant.value` that is a `bool` | `LitVal.bool b` | `True ↔ LitVal.bool true`, `False ↔ LitVal.bool false` |
| an `ast.Constant.value` that is an `int` | `LitVal.int n` | the Python integer ↔ the Lean `Int`; decimal source form ↔ `toString n` |
| an `ast.Constant.value` that is a `str` (simple — see `okLit`) | `LitVal.str s` | the Python string ↔ `s.toList`; only "simple" strings are in scope — `isSimpleStrChar`, i.e. printable-ASCII with neither `'` nor `\` — which is exactly the sub-domain on which `repr` is single-quoted with no escapes |
| a subscript slice that is an `ast.Tuple` with `elts == []` — the source spelling `head[()]` | `values = []` | the ONE zero-argument shape a parametrised type has. `unparse` takes the `ast.Tuple` `else` leg and emits `desc_sig_punctuation('', '(')` then `desc_sig_punctuation('', ')')` ↔ `valSeq _ _ [] = [DocNode.punct "(", DocNode.punct ")"]`. The pair is punctuation, so hunk 2's head guard cannot reach it (it rewrites `nodes.Text` children only) and the region is head-independent |
| `repr(value)` (the constant's display text) | `reprVal v` | `repr(None)="None"`, `repr(True)="True"`, `repr(False)="False"`, `repr(n)=str(n)`, `repr(simple_str s) = "'" + s + "'"` |
| the head string `str`, as a dotted Python name | `okHead head = true` | `s` ↔ `s.toList` and `s.split('.')` ↔ `headSegments s.toList`; a segment is admitted iff it is a non-empty ASCII identifier that is not in `keyword.kwlist` — measured against the real function, a head with a keyword segment does not parse as a parametrised type at all, so it is genuinely outside the rendered-sequence domain rather than excluded by choice |
| `nodes.Text(s)` | `DocNode.text s.toList` | only the display text is observed (the F2P test compares node-class + text) |
| `addnodes.pending_xref(..., reftarget=t)` | `DocNode.xref t.toList` | a cross-reference node; only the visible text / reference target is observed |
| `addnodes.desc_sig_punctuation('', s)` | `DocNode.punct s.toList` | a punctuation node (`[`, `]`, `, `, and the `(`/`)` pair of the empty tuple) emitted around / between the arguments |
| the returned `List[Node]` of `_parse_annotation` | the returned `List DocNode` | `out` IS that node sequence, child for child (class + text) |

`List Char` indexing is total and sound; the carriers are `List Char` / `List
DocNode` / `List LitVal` because the operation is per-element over the argument
sequence.

The two method preconditions are encoded as hypotheses of
`problem_spec_literalTypeNodes` (an implication chain): `okHead head` (the head
is a dotted Python type name — the enumeration heads AND every other dotted
head) and `values.all okLit`. Outside this domain the spec imposes no
obligation.

The argument list is deliberately NOT assumed non-empty. `values = []` is the
source spelling `head[()]` (table row above), which parses, renders, and is read
by a graded row of `tests/test_domain_py.py::test_parse_annotation` (`Tuple[()]`
→ reference, `[`, `(`, `)`, `]`). A hypothesis excluding it would leave that
shape unconstrained, so a model free to abbreviate it — for instance to the head
reference alone — would satisfy the contract while regressing that row.

The head membership test is deliberately NOT a precondition. It is an operation
the changed function performs, and its two branches render the arguments
differently, so both are part of the observable behaviour and both live in the
postcondition via `argNodeCtor` (refinement.md row 1b). A precondition naming
only the enumeration heads would leave the other branch unconstrained and admit a
model that renders every head's arguments alike.

## 3. Callee provenance (deep-model references — checked by G-AX / G-CONF)

### 3.1 `reprVal` ↔ Python `repr` (A-reference, G-AX)
**Callee:** Python builtin `repr`, called as `repr(node.value)` to render each
constant value's display text. `repr` is UNCHANGED (only the *call to it* is
added). On the modeled domain — `bool`, `int`, and "simple" `str` (`okLit`:
printable-ASCII excluding `'` and `\`) — `repr` produces exactly: `True`/`False`
for booleans, the decimal digits for integers, and a single-quoted, escape-free
form for strings. `reprVal` encodes precisely this. `axiom_check.py` runs the
REAL `repr` on boundary values (the booleans, small/large integers, the issue's
`'abc'`, empty and spaced strings) plus randomized fuzz and asserts `reprVal(v)
== repr(python_value(v))` for every `v`. G-AX runs WITHOUT the change — `repr` is
a builtin available at base_commit — so this A-reference is validated against the
genuinely-unchanged callee.

### 3.2 head cross-reference ↔ `type_to_xref` (carrier check, G-AX)
**Callee:** `sphinx.domains.python.type_to_xref` (UNCHANGED). The top-level loop
rewrites the head text node (`Literal` / `typing.Literal`) into a `pending_xref`
whose target is that head string. `axiom_check.py` constructs a minimal `env`
(`python_use_unqualified_type_names=False`, empty `ref_context`) and asserts
`type_to_xref(head, env)` is a `pending_xref` with visible text and `reftarget`
equal to `head` — confirming the `DocNode.xref head` modeling of the head node.
Available at base_commit (unchanged).

### 3.3 `expandLiteral` ↔ real `_parse_annotation` (A-reference, G-CONF)
The full node sequence is the deep model of the CHANGED callee, so its
equivalence to the real function is validated by `conformance_check.py` (G-CONF)
**with the gold patch applied** (the changed function gives the wrong result at
base_commit, so the equivalence can only be checked against the changed repo).
G-CONF builds the `expandLiteral` shadow and diffs it node-for-node (class +
text) against `_parse_annotation("<head>[<values>]", env)` over ≥10⁵ fuzzed
annotations whose heads span BOTH sides of the head test — the two enumeration
names, ordinary container and dotted module names, and near-misses of the
enumeration names — so the head-selected argument class is validated on both
branches rather than at one head only.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`9602`** so the
consumer-side verdict is reproducible. Its head pool (`HEAD_POOL`) is every
dotted-name shape listed in §3.3, and its value generator draws `None`,
booleans, non-negative integers and simple strings. The R/I shadow it builds
transliterates the impl region's ops — head `xref`, bracket/comma `punct`, and
one node per value carrying `reprVal v` whose class is the one `argNodeCtor`
selects — to Python node fingerprints `(class, astext)`,
leaving the A-reference content (`reprVal` ↔ `repr`, the whole-function
equivalence) to be exercised against the real `_parse_annotation`. The oracle is
the `_parse_annotation("<head>[<values>]", env)` child list (gold patch applied).
They must agree (node-class + text) on every annotation.
