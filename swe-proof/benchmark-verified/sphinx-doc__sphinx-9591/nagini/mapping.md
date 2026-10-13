# mapping.md — sphinx-doc__sphinx-9591

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9ed054279aeffd5b1d0642e2d24a8800389de29f`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `handle_property_annotation(present, typ)` | `PyProperty.handle_signature(self, sig, signode)` — `sphinx/domains/python.py:859` (the type-annotation block at lines 862-864) | the modeled changed function: the type-annotation rendering of a property description |
| `annotation_kinds(s)` *(axiom — A-consumed)* | `_parse_annotation(annotation, env)` — `sphinx/domains/python.py:110` | the cross-reference flags of the unchanged callee's rendered node list: entry `k` is True iff node `k` is a `pending_xref` |
| `annotation_texts(s)` *(axiom — A-consumed)* | the same `_parse_annotation(annotation, env)` — `sphinx/domains/python.py:110` | the rendered texts of that same node list: entry `k` is node `k`'s `astext()`. One entry per node, so its length agrees with `annotation_kinds`. |
| `annotation_bare_text(s)` *(axiom — A-consumed)* | the same `_parse_annotation(annotation, env)` — `sphinx/domains/python.py:110` | the BARE-TEXT flags of that same node list: entry `k` is True iff node `k` `isinstance(n, nodes.Text)` — a node that is nothing but the characters it renders — and False for every marked-up inline node, `pending_xref` and `desc_sig_punctuation` alike. One entry per node. |
| `annotation_holds_one_bare_text(s)` *(axiom — A-consumed)* | the same `_parse_annotation(annotation, env)` — `sphinx/domains/python.py:110` | that same node list read ONE LEVEL IN: entry `k` is True iff node `k` holds exactly one inner node and that node is a bare text run (`len(n.children) == 1 and isinstance(n[0], nodes.Text)`), False on a `nodes.Text` (which has no children) and False on a marked-up node whose label is split across runs or further marked up. One entry per node. |
| `AnnotationGroup{is_xref, text, is_bare_text, holds_one_bare_text, is_annotation_node}` | the annotation group's rendered children as FOUR PARALLEL sequences, plus one flag on the node holding them | `is_xref[k] == isinstance(child_k, addnodes.pending_xref)`, `text[k] == child_k.astext()`, `is_bare_text[k] == isinstance(child_k, nodes.Text)`, `holds_one_bare_text[k] == (len(child_k.children) == 1 and isinstance(child_k[0], nodes.Text))`, `is_annotation_node == (exactly one node is contributed and it is an addnodes.desc_annotation)`. One record per distinction the F2P `assert_node` draws at this site (§2 last four rows), for as many children as the real code emits. |
| `sep_text()` | the literal separator string `': '` (`nodes.Text(': ')` in the patch) | pure spec: the U+003A U+0020 separator emitted before the annotation |
| `is_simple_name(s)` / `is_name_start(c)` / `is_name_char(c)` | no repo symbol — spec-side predicates | `s` is a non-empty `[A-Za-z_][A-Za-z0-9_]*` run over code points: the class of annotation strings on which the real parser's output is exactly one cross-reference (executably confirmed by `axiom_check.py`, §3.1) |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): `addnodes.desc_annotation(typ, ': ' +
typ)` (`sphinx/domains/python.py:864` pre-patch) — a single annotation node
whose entire rendered content is the inert literal string `': ' + typ`, with no
inner cross-reference.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `typ: Optional[str]` from `self.options.get('type')`, guarded by `if typ:` | `present: bool` + `typ: List[int]` | `present` ↔ "`typ` is set and non-empty" (the truthiness guard `if typ:`); `typ` ↔ the annotation-string code points. The repo's falsy guard (None or empty string) collapses to `present == False`; the verifier never reads `typ` when `present` is False. |
| `str` (the annotation string, and node text) | `List[int]` / `PSeq[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation `': ' + typ` ↔ `sep_text() + ToSeq(typ)`; empty `str` ↔ `[]` |
| `signode += <children…>` (appending inline nodes to the signature node) | the returned `AnnotationGroup`'s four parallel sequences plus its group flag | the modeled function returns the ordered children the patch appends, one entry per child in each sequence, and records which node holds them; order, node kinds, node insides and the wrapper's class are what the F2P test asserts. The WIDTH is whatever the real code emits — a compound annotation renders as several children and is representable as such. |
| `nodes.Text(s)` | `is_xref[k] == False`, `text[k] == ToSeq(s)`, `is_bare_text[k] == True`, `holds_one_bare_text[k] == False` | a bare literal-text node: it carries no inline markup role, and it holds no inner node at all — it IS the run it renders |
| `addnodes.desc_sig_punctuation('', s)` (rendered brackets, commas, `...`) | `is_xref[k] == False`, `text[k] == ToSeq(s)`, `is_bare_text[k] == False`, `holds_one_bare_text[k] == True` | also NOT a cross-reference — `is_xref` separates cross-references from every other inline node, not text from non-text — but it IS marked up, so it differs from `nodes.Text(s)` on the third and fourth axes even when it carries the very same characters. That is the distinction the F2P harness draws and the reason the carrier records more than `is_xref`/`text`: see the note below this table. |
| `addnodes.pending_xref(... reftarget=name ...)` (the cross-reference), labelled by one text run | `is_xref[k] == True`, `text[k] == ToSeq(name)`, `is_bare_text[k] == False`, `holds_one_bare_text[k] == True` | a cross-reference node carrying the type name as exactly one bare text run inside it (the default-config form, §3.1) |
| the same `pending_xref` with its label split across two runs, or wrapped in further inline markup | `is_xref[k] == True`, `text[k] == ToSeq(name)`, `is_bare_text[k] == False`, `holds_one_bare_text[k] == False` | same kind, same characters, DIFFERENT inside. Distinguished from the row above by the fourth axis alone, because `assert_node` requires the cross-reference to have exactly one child equal to the name. |
| `desc_annotation(...)` wrapper holding the children | `is_annotation_node == True`, and identity on the children sequences | the F2P test (`assert_node(..., [desc_annotation, (": ", [pending_xref, "str"])])`) checks the wrapper's CLASS with `assert isinstance(node, cls)` before it inspects any child, so the wrapper is itself observable and is recorded rather than treated as transparent grouping. Any other inline wrapper, or contributing the children loose onto `signode`, reads `is_annotation_node == False`. |
| no annotation group contributed at all (`if typ:` false) | `is_annotation_node == False` and all four sequences empty | contributing an EMPTY `desc_annotation` is not the same as contributing nothing: the sequences agree but the flag does not. |

**Why the carrier records four child axes and the wrapper, and not just
`is_xref`/`text`.** The carrier has to be INJECTIVE on every distinction the F2P
oracle draws, or the spec admits an implementation the test fails. `assert_node`
(`sphinx/testing/util.py:48-83`) draws exactly four at this site:

1. the wrapper's class (`assert isinstance(node, cls)`, run before any child) →
   `is_annotation_node`;
2. child kind vs child text — a bare-string expectation such as `": "` is matched
   by node EQUALITY, which `nodes.Text` satisfies (it subclasses `str`) and which
   no `Element` does, so `nodes.Text(': ')` and
   `addnodes.desc_sig_punctuation('', ': ')` are different renderings that agree
   on cross-reference-ness AND on text → `is_bare_text`;
3. child inside — `[pending_xref, "str"]` requires the cross-reference to have
   EXACTLY ONE child equal to `"str"` (`assert len(node) == len(cls)`), so a
   two-run label is rejected while agreeing on kind, text and bare-text-ness →
   `holds_one_bare_text`;
4. the text itself → `text`.

Each axis dropped is a PAIR of renderings the carrier would collapse to one value
while the oracle separates them — i.e. an implementation the spec verifies and the
F2P test fails. An earlier revision of this file recorded rows 2 and 3 above as
having the SAME carrier image, and that non-injectivity was a real spec hole: a
patch emitting the separator as rendered punctuation satisfied the spec and failed
the test. The `properties.py` rivals
`separator-as-rendered-punctuation`, `rewrite-the-xref-inside`,
`wrapper-swap-not-an-annotation-node` and
`empty-annotation-node-when-none-declared` are the standing regression guards, one
per axis; each is rejected by its own clause and by no other.

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and node text is `PSeq[int]`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `annotation_kinds` / `annotation_texts` / `annotation_bare_text` / `annotation_holds_one_bare_text` ↔ `_parse_annotation` (A-consumed)
**Callee:** `sphinx.domains.python._parse_annotation(annotation, env)`
(`sphinx/domains/python.py:110`). It parses the annotation string with the
AST parser, then for each rendered text fragment that names a type it replaces
the fragment with `type_to_xref(...)` (`sphinx/domains/python.py:182-184`):

```python
result = unparse(tree)
for i, node in enumerate(result):
    if isinstance(node, nodes.Text) and node.strip():
        result[i] = type_to_xref(str(node), env)
return result
```

`type_to_xref(text, env)` (`sphinx/domains/python.py:83`) returns
`addnodes.pending_xref('', *contnodes, refdomain='py', reftype=..., reftarget=text, ...)`
— a **cross-reference** node whose target text is the type name. For a simple
documented type name such as `str` the AST is a single `ast.Name`, `unparse`
returns `[nodes.Text("str")]`, and the post-loop converts it to
`[type_to_xref("str", env)]` = `[pending_xref("str")]`: a one-element list whose
sole node is a cross-reference carrying the name. For a compound annotation
`unparse` also emits `addnodes.desc_sig_punctuation` nodes for the rendered
brackets, commas and `|`, which the post-loop leaves alone (they are not
`nodes.Text`), so the list is WIDER than one and its non-name entries are not
cross-references.

The four axioms mirror that node list **elementwise, at its real width**:
`annotation_kinds(s)[k]` is node `k`'s cross-reference flag,
`annotation_texts(s)[k]` is node `k`'s text, `annotation_bare_text(s)[k]` is
whether node `k` is a bare `nodes.Text` rather than a marked-up inline node, and
`annotation_holds_one_bare_text(s)[k]` is whether node `k` holds exactly one inner
node and that node is a bare text run. What they ASSERT is deliberately
only what the property-rendering site consumes, and every clause is an
executably-confirmed property of the real function over the whole admitted
domain:

* **Domain** (`accepted(s)`, with `Ensures(Implies(is_simple_name(s), Result()))`).
  The parser is **PARTIAL**: `accepted(s)` is True exactly when it yields a node
  list for `s`, and the sequence axioms carry `Requires(accepted(s))` so they are
  defined only there. An accepted string with no content yields ZERO nodes (`""`,
  `" "`, `"  "`, `"\t"`, `"\n"` → `[]`), which is different from being
  refused. The only totality claimed is the strong arm: a **simple type name is
  always accepted**, so the discriminating clause is unconditional on the F2P
  class. The refused class is real and reachable through reST: `unparse`'s
  `ast.Constant` arm (`sphinx/domains/python.py:180-183`) does
  `nodes.Text(node.value)`, so a **bytes literal** annotation (`b"x"`, and bytes
  nested in a subscript or union) hands docutils a `bytes` value and
  `nodes.Text.__new__` raises `TypeError: expecting str data, not bytes`; the
  `except SyntaxError` fallback at `:185` does not catch it, so it escapes.
  Because `:type:` is `directives.unchanged`, such a value is an ordinary
  admitted input — the precondition does not and must not exclude it.
* **Refusal is propagated, not absorbed** (`rendered_nodes`'
  `Exsures(AnnotationRejected, ... not accepted(ToSeq(typ)))`, mirrored by the
  operation's own `Exsures`). The caller `PyProperty.handle_signature` at `:859`
  has no handler for it either, so on a refused annotation NO annotation group is
  rendered and the refusal leaves the operation. `AnnotationRejected` is a
  user-defined exception because a **builtin** one in an `Exsures` crashes the
  Nagini translator; the named class is a modelling artifact, and what the real
  code propagates is the parser's own exception (which is why
  `conformance_check.py` compares refusals on the underlying cause type, not on
  the wrapper's identity).
* **Width agreement** (`len(annotation_texts(s)) == len(annotation_bare_text(s))
  == len(annotation_holds_one_bare_text(s)) == len(annotation_kinds(s))`).
  Structural: all four sequences are read off the same node list.
* **Simple names** (`Implies(is_simple_name(s), annotation_kinds(s) == PSeq(True))`,
  `Implies(is_simple_name(s), annotation_texts(s) == PSeq(s))`,
  `Implies(is_simple_name(s), annotation_bare_text(s) == PSeq(False))` and
  `Implies(is_simple_name(s), annotation_holds_one_bare_text(s) == PSeq(True))`).
  For a non-empty `[A-Za-z_][A-Za-z0-9_]*` string the parser returns EXACTLY ONE
  node; that node IS a cross-reference carrying the name — the discriminating
  "type is cross-referenced, not inert text" property the change delivers — it is
  therefore an `Element` and not a bare `nodes.Text`, and it holds that name as
  exactly one bare text run. The bare-text clause is the SAME single measurement
  the cross-reference clause rests on, read on the other flag, so it adds no new
  claim about the parser; the holds-one clause is a genuinely further observation
  of that node's children and is measured as such (it is the one clause here whose
  truth depends on the config flag — see **Flag dependency** below).
* **The two child axes are independent, not complements.** A node can read False
  on both — a marked-up node whose label is not one plain run. `axiom_check.py`
  measures 1320 such nodes across the two config settings, so
  `annotation_holds_one_bare_text` is not `not annotation_bare_text` restated and
  the fourth clause of the operation's postcondition is not derivable from the
  third. (Under the default config alone they happen to come out as exact
  complements over the strings `conformance_check.py` generates; that gate records
  the coincidence explicitly rather than resting on it.)

No width or kind claim is made for any other accepted annotation shape, and that
is the point: the real width varies with the annotation (distribution under
`## G-CONF`), so an axiom asserting a fixed width would be unsound on the
ordinary compound case. The model's general postcondition consumes only the
elementwise mirror, which holds for every shape; the strong simple-name arm is
what discharges the discriminating clause on the F2P input `:type: str`.
`_parse_annotation` is **unchanged** by the gold patch — only its *caller*
changes — so it is a sound axiomatized callee, never the function under spec.

**Flag dependency:** the single-`pending_xref` form (one node, text == name, one
inner text run) holds for a simple name when
`env.config.python_use_unqualified_type_names` is **False** (the default; the test
app uses defaults). When True the cross-reference's `contnodes` are TWO
`pending_xref_condition` children rather than a `Text` payload, but the node
returned is still a `pending_xref` (still `is_xref == True`) and still an
`Element` (still `is_bare_text == False`) — those two discriminating properties are
configuration-independent. What depends on the default is the exact
`text == name` content clause and the `holds_one_bare_text == True` clause (with
two `pending_xref_condition` children the node holds two inner nodes, so it reads
False). `axiom_check.py` fuzzes both configurations, asserts the two
config-independent clauses under both, and records the default as the binding one
for the other two; the non-default nodes are also what supply the 1320-node
measurement above that keeps the two child axes from collapsing into one.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`sphinx.domains.python._parse_annotation`, builds a minimal env, and asserts
every claim above over 23 simple names, 44 compound/degenerate annotations
(subscripted, nested, unions, `...`, numeric, syntax-error, empty and
whitespace-only), every one of the 3392 length-1 and length-2 ASCII identifiers,
and 5000 fuzz strings (including bytes literals bare and spliced into subscripts
and unions), under **both** config settings — treating a **refused simple name**,
a width disagreement, a non-cross-reference or a wrong text as unsound. It also
re-measures a recorded refused class of 12 annotations and reports an accepted
member as a STALE DOMAIN CLAIM, so the partiality the `Exsures` arm rests on is
observed rather than assumed and cannot silently drift back to totality. Exit 0
iff sound.

**Recorded verdict: PASS.**

```
G-AX OK: accepted/annotation_kinds/annotation_bare_text/annotation_holds_one_b
are_text/annotation_texts/rendered_nodes axioms sound on 23 simple names + 44
compound/degenerate annotations + 3392 exhaustive length-1/2 ASCII identifiers
+ 5000 fuzz strings (incl. bytes literals bare and spliced into
subscripts/unions), both config settings, of which 313 fuzz strings were
REFUSED. The real _parse_annotation is PARTIAL, and the split is exactly the
one the axioms describe: it NEVER refused a simple name, so accepted()'s
strong arm holds and the discriminating clause is unconditional on that class;
on every ACCEPTED string its FOUR sequences agree in width and every SIMPLE
name yields EXACTLY ONE pending_xref, not a bare text node, holding exactly
one bare text run that spells the name; and it refused all 12 recorded
refused-class annotations ['b"x"' -> TypeError; "b'x'" -> TypeError; 'B"x"' ->
TypeError; 'rb"x"' -> TypeError; 'b""' -> TypeError; 'List[b"x"]' ->
TypeError; 'x | b"y"' -> TypeError; 'Dict[str, b"k"]' -> TypeError; 'b"x" |
None' -> TypeError; 'Optional[b"x"]' -> TypeError; 'a\x00b' -> ValueError;
'"\ud800"' -> UnicodeEncodeError], so the arm rendered_nodes' Exsures
describes is grounded in measured behaviour rather than assumed. The two
child-kind axes are NOT degenerate on the measured node lists: bare-text
True/False = 470/14728 and holds-one-bare-text True/False = 13408/1790, and no
node ever read True on both. Nor is either the other's complement: 1320
measured nodes read FALSE on BOTH (a marked-up node whose label is not one
plain run -- e.g. the cross-reference under python_use_unqualified_type_names
= True, whose label is a pair of pending_xref_condition children), so the
fourth flag is an independent observation of the real parser's output and not
`not is_bare_text` restated.
```

## G-CONF (differential conformance — `conformance_check.py`)

**Shadow.** The `# impl-start`/`# impl-end` region of `model.py`, copied
verbatim; no contract call appears inside the region, so nothing was deleted.
The `@Pure` helper `sep_text()` and the `AnnotationGroup` record are copied
verbatim minus contracts; `PSeq`/`ToSeq` are realized by an immutable-tuple shim.
The `@ContractOnly` callees `rendered_nodes` / `annotation_kinds` /
`annotation_texts` / `annotation_bare_text` / `annotation_holds_one_bare_text`
have no body to copy, so the shadow reads them off the REAL
function they axiomatize, `sphinx.domains.python._parse_annotation` (§1, §3.1),
exercising the axioms instead of assuming them. `rendered_nodes` is given
`is_annotation_node = False`, since the model's `Ensures` makes no claim there —
a bare node list is not held in anything — so a shadow that forwarded the
parser's group unchanged would be caught rather than inheriting the caller's
answer for free. `rendered_nodes` is realized as
"call the real parser; if it refuses, signal", so which arm of the model's
postcondition applies is decided by the real callee and not by the shadow.

**Oracle.** The REAL gold-patched `PyProperty.handle_signature`
(`sphinx/domains/python.py:859`), **called**, not transliterated — the directive
is driven with a duck-typed `state.document.settings.env` (which is the whole of
the context `Directive.env` needs), the method is invoked once without `:type:`
to learn the base children and once with it. The observable is the PAIR (§2):
which node holds the group (`len(added) == 1 and isinstance(added[0],
addnodes.desc_annotation)`) and the children of that wrapper read four ways —
exactly the four things the F2P `assert_node` inspects, no fewer.

**Type bridge.** Generation runs in the CONCRETE direction (an `Optional[str]`
option) and derives the abstract pair, so every input satisfies
`Requires(Implies(present, len(typ) > 0))` by construction rather than by
filtering: `present = (typ_str not in (None, ''))` (the repo's `if typ:` falsy
guard), `typ = [ord(c) for c in typ_str]`; each rendered child `n` maps to
`(isinstance(n, pending_xref), n.astext(), isinstance(n, nodes.Text),
len(n.children) == 1 and isinstance(n[0], nodes.Text))`, compared elementwise
against the shadow's four parallel sequences, and the wrapper observation is
compared against `is_annotation_node`.

**Inputs / seed.** 100034 Requires-satisfying inputs — 34 boundary cases
(absent, empty, the F2P `str` shape, singleton, dotted, `None`, whitespace-only,
`...`, subscripted, nested, union, comma-separated, non-ASCII, long, and the
REFUSED class: bytes literals bare and nested in subscripts/unions, plus NUL)
with both branches of the impl region and both arms of the postcondition taken,
then seeded fuzz. **Pinned seed: `SEED = 9591`.**

**Classification.** A refusal by BOTH sides is the agreement it is — the model's
`Exsures` says a refused annotation yields no group and the refusal propagates,
which is what the real caller does — and is compared on the UNDERLYING cause
type, so "refuses for an unrelated reason" is not scored as agreement. A
one-sided refusal is a disagreement: `oracle_only_refused` is exactly the
shadow inventing a group where the real code produces none (what the pre-patch
shape does), and `shadow_only_refused` the converse.

**Recorded verdict: PASS — 0 disagreements over 100034 inputs.**

```
G-CONF OK: model.py impl region (verbatim, contracts stripped, @ContractOnly r
endered_nodes/annotation_kinds/annotation_texts/annotation_bare_text/annotatio
n_holds_one_bare_text -> real _parse_annotation) agrees with the real patched
PyProperty.handle_signature on 100034 Requires-satisfying inputs (98017
present / 2017 absent, seed=9591), 0 disagreements, on ALL FIVE observables
the model carries: which node holds the group (is_annotation_node), and per
child its cross-reference flag, its rendered text, whether it is a bare text
node, and whether it holds exactly one bare text run. Group widths observed:
{0: 2017, 1: 58, 2: 61936, 3: 14, 4: 17, 5: 12920, 6: 7079, 7: 7000, 8: 2953}
— the carrier holds every real width, including the compound annotations (e.g.
"List[int]" -> 5 children) that a fixed-width-2 carrier could not represent.
None of the three added axes is degenerate over these outputs: bare-text
True/False = 106133/197605, holds-one-bare-text True/False = 197605/106133,
is_annotation_node True/False = 91977/2017 — so agreement on them is a
measurement, not a constant. Recorded honestly: under the DEFAULT config this
gate runs (the F2P app's, python_use_unqualified_type_names = False) the two
child axes came out as exact complements, because every marked-up node this
parser emits under that config happens to hold exactly one plain run. They are
still independent observations rather than one restated — axiom_check.py
sweeps BOTH config settings and reports the nodes that read False on both —
and both are separately load-bearing here, since a rival that gets one right
and the other wrong (rendered punctuation carrying the separator; a cross-
reference relabelled across two inner runs) is caught by whichever it broke.
On 6040 of those inputs the annotation is one the parser REFUSES, and both
sides refused with the same exception type: no group is produced and the
refusal propagates, which is the model's Exsures arm. A shadow that invented a
group there (as the pre-patch shape does) would be counted
`oracle_only_refused` and fail.
```

The width distribution is the substantive record. The real annotation group is
two children wide only for the simple/dotted-name case; it is 5 wide for
`List[int]`, 7 for `Dict[str, int]`, 6 for `int | None`, 1 for `"  "`, and 0 when
no annotation is declared. All of those are inside the model's `Requires` (its
only clause is `Implies(present, len(typ) > 0)`, and `:type:` is
`directives.unchanged`), so the postcondition must — and now does — predict the
group at the real width for each of them, through the elementwise axioms. The
domain was NOT narrowed to reach this pass — in either revision. It is the same
generator over the same `Requires`-admitted domain as the earlier run that
recorded 35161 `axiom_shape` disagreements against a fixed-width-two carrier, and
the boundary list still contains that run's `List[int]` witness. The refused
class was ADDED to the generator rather than excluded from it: 6040 of the inputs
are annotations the parser will not render, they are admitted by the same
unchanged precondition (`:type:` is `directives.unchanged`), and the postcondition
now predicts what the real caller does on them instead of promising a group.

The same holds for the three axes added in the current revision. The generator,
the seed and the `Requires` are unchanged; what changed is that each input is now
scored on FIVE observables instead of two, so this run is strictly harder to pass
than the one before it. The axis census in the recorded output is the evidence
that the added clauses constrain something real rather than agreeing vacuously:
106133 children read as bare text and 197605 did not, 197605 held exactly one
bare text run and 106133 did not, and the group flag came out True on 91977
inputs and False on 2017. A spec clause that could only be satisfied one way
would show a one-sided census.
