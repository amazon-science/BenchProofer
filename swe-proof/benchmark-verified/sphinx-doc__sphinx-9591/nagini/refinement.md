# refinement.md — sphinx-doc__sphinx-9591

The operation-by-operation correspondence between `model.py`'s implementation
(the `handle_property_annotation` impl region, plus the `accepted` /
`annotation_kinds` / `annotation_bare_text` / `annotation_holds_one_bare_text` /
`annotation_texts` axioms) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses the axiom's `Ensures`, **A-reference** where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The property type-annotation site — `PyProperty.handle_signature`

Gold hunk (`sphinx/domains/python.py:861-865`; post-patch worktree line numbers
`863` = `if typ:`, `864` = `annotations = ...`, `865` = `signode += ...`):
```
  typ = self.options.get('type')
  if typ:
-     signode += addnodes.desc_annotation(typ, ': ' + typ)
+     annotations = _parse_annotation(typ, self.env)
+     signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)
```

What the correctness oracle observes of that one line is fixed by the F2P
expectation `[desc_annotation, (": ", [pending_xref, "str"])]` read through
`assert_node` (`sphinx/testing/util.py:48-83`), which makes exactly FOUR
distinctions: (a) the contributed node's CLASS (`desc_annotation`); (b) each
child's kind, since the expected `": "` is compared with `==` and
`nodes.Text.__eq__` is `str` equality while `Element.__eq__` is identity, so only
a bare `nodes.Text` can match it; (c) the cross-reference's INSIDE, since
`[pending_xref, "str"]` requires that node to have exactly one child equal to
`"str"`; (d) each child's characters. The carrier below records one observable
per distinction, plus the child count, and that is why it has five fields rather
than two: **any pair of renderings the carrier maps to one value is a pair the
spec cannot tell apart, and if the oracle separates them the spec admits an
implementation that fails the test.**

| # | model.py impl op (`handle_property_annotation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `present: bool`, `typ: List[int]` | `typ = self.options.get('type')` (an `Optional[str]`, `:type:` being `directives.unchanged` at `python.py:856`) and the guard `if typ:` (`:863`) | R | `present` ↔ the truthiness guard `if typ:` (set and non-empty); `typ: List[int]` ↔ the annotation-string code points (mapping.md §2). |
| A2 | `if present:` branch; all four sequences empty and `is_annotation_node == False` when not present | `if typ:` guard (`:863`); nothing appended otherwise | I | identical control flow: an annotation group is built iff a non-empty type was declared. The absent arm is now pinned on the flag as well, so "contributes nothing" is a claim about the node too, not only about a child count. |
| A3 | `PSeq(False)` prepended to `is_xref`, `PSeq(sep_text())` to `text`, `PSeq(True)` to `is_bare_text`, `PSeq(False)` to `holds_one_bare_text` | `nodes.Text(': ')` as the first child of the new `desc_annotation` (`:865`) | R | The four values are the four observations of that one node object. `nodes.Text` is not a `pending_xref` → `is_xref == False`; it IS the bare text kind → `is_bare_text == True`; it has no children at all, so "holds exactly one child and that child is a `Text`" is false → `holds_one_bare_text == False`; its `astext()` is `': '` ↔ `sep_text() == PSeq(58,32)`. The image is **injective against the near-miss**: `desc_sig_punctuation('', ': ')`, the node `_parse_annotation` itself uses for punctuation (`python.py:118` and following), carries the same characters and is equally not a cross-reference, but reads `is_bare_text == False` and `holds_one_bare_text == True`, and it fails distinction (b) of the oracle. **An earlier revision of this document recorded this row as `nodes.Text` ↔ "an `is_xref == False` entry" alone.** That was non-injective — rendered punctuation had the same carrier image — and it was a real spec hole: a rival emitting `desc_sig_punctuation` in the separator's place verified while its patch did not resolve. The two kind axes close it, and `properties.py`'s `SEP_AS_PUNCTUATION` rival is the standing regression. |
| A4 | `+ annotation_kinds(...)` / `+ annotation_texts(...)` / `+ annotation_bare_text(...)` / `+ annotation_holds_one_bare_text(...)` — the parser's whole node list, on all four axes, concatenated after the separator entry | `annotations = _parse_annotation(typ, self.env)` (`:864`); `*annotations` spliced as the remaining children (`:865`) | A-consumed | The four axioms mirror the unchanged callee `_parse_annotation` **elementwise, at its real width** (mapping.md §3.1), so the concatenation is exactly the `*annotations` splice for a list of ANY length — a compound annotation's several children included. The proof consumes their `Ensures`: the width clauses discharge the general per-axis postconditions, and the simple-name arms (`annotation_kinds(s) == PSeq(True)`, `annotation_bare_text(s) == PSeq(False)`, `annotation_holds_one_bare_text(s) == PSeq(True)`, `annotation_texts(s) == PSeq(s)`) discharge the cross-reference clause. Because all four are read off the SAME node list, the splice cannot re-kind a node or edit its inside without breaking one of them: the caller has no node of its own at those positions. `accepted` is consumed the same way — `Requires(accepted(s))` on the four sequence axioms is what forces the domain clause to precede them. G-AX confirms every claim against the real `_parse_annotation`. |
| A5 | `is_annotation_node == True` on the present arm | `addnodes.desc_annotation(typ, '', ...)` — the WRAPPER class chosen at `:865` | R | `assert_node` matches the outer element's class before it looks at any child, and the F2P expectation's outer element is `desc_annotation`; `:865` names that class. The choice is the CALLER's: `_parse_annotation` returns a bare `List[Node]` with no wrapper, so nothing in A4 constrains it. Hence a dedicated observable rather than an unrecorded detail. The raw-source first argument `typ` and the empty `''` text argument set `rawsource`/`Element.rawsource`, which `assert_node` never reads, so the carrier deliberately does not record them (mapping.md §2). |
| A6 | `return AnnotationGroup(kinds, texts, bares, holds, True)` (the group as four parallel child sequences plus the wrapper flag) | the children appended to `signode` via `+=` (`:865`) | R | `signode += desc_annotation(typ, '', <children>)` ↔ returning `is_annotation_node == True` together with the ordered children as `(is_xref[k], text[k], is_bare_text[k], holds_one_bare_text[k])`; `+=` contributes exactly one node to the signature, which is what `is_annotation_node == present` says at the group level (mapping.md §2). |

The discriminating content of the change — the type is rendered through a
**cross-reference** node rather than as a single inert text run — lives in the
leading `False` of the kinds sequence together with its simple-name value
`PSeq(False, True)` (model) ⇔ the `nodes.Text(': ')` child followed by the
`*annotations` splice of `_parse_annotation` output (real). The pre-patch emitted
one inert node `': ' + typ`; `model_prepatch.py` reproduces that (a single
`is_xref == False` entry whose text is `sep_text() + ToSeq(typ)`, built without
consulting the parser) and **fails**: it cannot even discharge
`Implies(present, accepted(ToSeq(typ)))`, since it never delegates, and its
single-child group contradicts the kinds clause
`PSeq(False) + annotation_kinds(ToSeq(typ))` and the simple-name value
`PSeq(False, True)` as well. That is the spec sensing the change (G-DIFF); the
verifier reports the domain clause first only because it is the first
postcondition in source order.

Why the group is modelled at the parser's real width rather than as a fixed pair:
the real `_parse_annotation` renders a compound annotation as several nodes
(`"List[int]"` → cross-reference `List`, punctuation `[`, cross-reference `int`,
punctuation `]`, giving a five-child group), and `:type:` is
`directives.unchanged` (`python.py:856`), so any such string is an ordinary input
at this site. A fixed two-child claim would therefore be a claim the real code
does not honor. The exact two-child rendering is retained where it is genuinely
true — under `is_simple_name` — and that is the arm the F2P input `:type: str`
lands in. G-CONF's observed width histogram
(`{0: 2017, 1: 58, 2: 61936, 3: 14, 4: 17, 5: 12920, 6: 7079, 7: 7000, 8: 2953}`)
is the measurement that the wider arms are reachable rather than hypothetical.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
is the caller's *delegation* to the annotation parser (which produces the
cross-reference) and the splitting of the separator into its own node — both
expressed directly in the model (A4, A3) — together with the caller's own choice
of wrapper, which the patch keeps and the model pins (A5). The axioms —
`accepted` / `annotation_kinds` / `annotation_bare_text` /
`annotation_holds_one_bare_text` / `annotation_texts` (all **A-consumed**) — cover
the **unchanged** callee `_parse_annotation` the new code now invokes; the patch
does not modify `_parse_annotation`, so axiomatizing it is sound, and the proof
genuinely consumes every one of their `Ensures` (without them neither the general
per-axis clauses, nor the domain clause, nor the simple-name cross-reference
clause is provable). There is no dead axiom and no A-reference deep model in this
bundle.

The two child-kind axes deserve a note here because they look like one axis
restated. They are not complements: a marked-up node whose label is split across
several inner runs, or itself further marked up, reads False on BOTH. G-AX
measures 1320 such nodes in the real parser's output (they arise under
`python_use_unqualified_type_names = True`, where a cross-reference's label is a
pair of `pending_xref_condition` children). Under the DEFAULT config that G-CONF
and the F2P app use, they do come out as exact complements on the measured
outputs, and both gates record that plainly rather than leaving it to be
discovered; both remain separately load-bearing, since a rival that gets the kind
axis right and the inside axis wrong (a cross-reference relabelled across two
inner runs) is caught only by the second.

## C. verify(model) ⇒ resolved

`handle_property_annotation` verifies only if, on a declared annotation, it

1. contributes exactly one ANNOTATION node and nothing else (`is_annotation_node
   == present`, A5/A2) — oracle distinction (a);
2. makes that node's first child the literal separator as a BARE TEXT node
   holding no inner run (`PSeq(False)`/`PSeq(sep_text())`/`PSeq(True)`/`PSeq(False)`,
   A3) — oracle distinctions (b) and (d);
3. follows it with exactly the parser's own children, in order, each at the kind
   the parser gave it, with the inside the parser gave it, and carrying the text
   the parser gave it (A4) — oracle distinctions (b), (c) and (d) on the
   remaining children;
4. therefore, for a simple type name, renders exactly two children of which the
   second is a **cross-reference** carrying the name as ONE bare inner run
   (`is_xref == PSeq(False, True)`, `text == PSeq(sep_text(), ToSeq(typ))`,
   `is_bare_text == PSeq(True, False)`, `holds_one_bare_text == PSeq(False, True)`);
5. emits nothing at all when no annotation is declared (A2), and propagates the
   parser's refusal rather than substituting a rendering when the parser rejects
   the string (`Exsures`).

By R (`str` ↔ `List[int]`; `Optional[str]`/`if typ:` ↔ `present`/`typ`;
`nodes.Text` ↔ `(is_xref False, is_bare_text True, holds_one_bare_text False)`,
`desc_sig_punctuation` ↔ `(False, False, True)`, `pending_xref` with a one-run
label ↔ `(True, False, True)`; `desc_annotation` ↔ `is_annotation_node`; `+=` ↔
the returned group) the verified rendering equals
`desc_annotation(typ, '', nodes.Text(': '), *_parse_annotation(typ, env))` on the
tested input. By G-AX the real `_parse_annotation` meets the four axioms
(A-consumed) it stands in for, over both config settings. By G-CONF the impl
region — taken verbatim, contracts stripped, the `@ContractOnly` callees bound to
the real `_parse_annotation` — reproduces the real patched method on 100034
`Requires`-satisfying inputs with 0 disagreements, scored on ALL FIVE observables
and across every observed group width (0 through 8), including the 6040 inputs on
which both sides refuse with the same exception type. None of the five is
vacuous over that run (bare-text True/False = 106133/197605, holds-one True/False
= 197605/106133, `is_annotation_node` True/False = 91977/2017).

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE; the F2P `test_pyproperty` now expects
`[desc_annotation, (": ", [pending_xref, "str"])]` in place of
`[desc_annotation, ": str"]`). The converse direction — that no NON-gold
rendering slips through — is what the injectivity argument at the head of §A and
the four standing rivals in `properties.py` (`SEP_AS_PUNCTUATION`,
`WRAPPER_SWAP`, `XREF_INTERIOR`, `EMPTY_GROUP_NODE`, one per oracle distinction)
are for: each is a plausible real patch that the oracle rejects, and each is
rejected by exactly one clause of this spec. The trust points are exactly the two
of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ).
