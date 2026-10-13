# RELAXED-LEAKAGE ACCEPTANCE: sphinx-doc__sphinx-10614

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision; see
RELAXED_LEAKAGE.md).** This instance is a `problem_statement <-> gold`
MISMATCH on ONE of the gold's tested behaviours: the public issue reports only
the `../` symptom (SVG inheritance-diagram links in a non-root document climb
one directory too far and 404), but the gold fix's F2P test
(`tests/test_ext_inheritance_diagram.py::test_inheritance_diagram_svg_html`) was
*also* rewritten to exercise an **intersphinx / external-reference** node, and
the only way to make that node register and emit its absolute URL is the new
external-key derivation `refname = child['refuri'].rsplit('#', 1)[-1]`. That
intersphinx/external-key behaviour (modeled here as behaviour (3),
`trailing_name_for_destination` / `after_last_hash`) is **absent from the
solver-visible `problem_statement`** — it lives only in the gold patch and the
rewritten test. A spec faithful to the F2P test MUST pin it (proven necessary
below), so for behaviour (3) faithful + non-leaking is impossible. Independent
adversarial analysis (the batch06 panel) confirmed the verification CORE is
fully SOUND (G-VERIFY/G-DIFF/G-MUT/G-EQ/G-AX/faithfulness clean) and the gold
resolves (G-RESOLVE), so `verify => correct` is UNAFFECTED — only the secondary
no-leakage property is relaxed, and only for behaviour (3).

## The relaxed delta is NARROW: only behaviour (3) (the external-reference key)

Two of the three modeled behaviours are NOT a leak under directive 6 — they are
the public bug:

- **Already public in `problem_statement` (no leak) — behaviours (1) and (2):**
  the `../` over-climb is the entire bug report. The issue states "the links in
  the SVG file are relative to the SVG file ... however the rest of the link is
  written as if it was relative to the file the SVG is embedded on", gives the
  `../my_class_1.html#my_package.MyClass1` examples, and titles itself
  "inheritance-diagram 404 links with SVG". Token check on `problem_statement`:
  `../`=PRESENT, `SVG`/`svg`=PRESENT, `inheritance`=PRESENT, `://`=PRESENT. The
  spec view's behaviours (1)/(2) (the link is the destination URI itself / the
  current document's own name `+ '#' +` the anchor, with no leading `../`, and an
  absolute URL containing `://` preserved verbatim) narrate exactly this public
  symptom and its expected fix. That is permitted de-narration, not a leak.

- **The image-format distinction is likewise public (no leak):** the spec view
  states each clause for both image formats and names the format an input. The
  issue itself draws that distinction — "This issue does not happen in the
  default (png?) mode" — and explains why: the SVG "is embedded using the object
  tag", so its links resolve relative to the image while the other mode's do
  not. Token check on `problem_statement`: `png`=PRESENT, `svg`/`SVG`=PRESENT,
  `object`=PRESENT, `embed`=PRESENT, `format`=PRESENT. So parameterising the
  spec by the image format, and saying that the destination-URI link is the
  same in both modes while the anchor link names the document only in the
  embedded-vector mode, adds NO increment over the public text.

- **The ONLY relaxed increment — behaviour (3):** the spec view's docstring
  clause (3) and `trailing_name_for_destination` narrate that the registration
  key for an *externally-sourced* (non-internal) reference is the trailing
  component of its destination URI after the final `#`. The notions
  "intersphinx", "external reference", "registration key", and "trailing
  component after the final `#`" (`rsplit('#', 1)[-1]`) are **absent from
  `problem_statement`** (and from `hints_text`, which is empty). They are an
  artifact of how the rewritten F2P test wires an intersphinx inventory
  (`subdir.other.Bob py:class 1 foo.html#subdir.other.Bob`); they appear only in
  the gold patch and the test. Token check on `problem_statement`: `refuri`,
  `refid`, `reftitle`, `intersphinx`, `rsplit`, `internal`, `scheme`, `key`,
  `external` = all ABSENT (and `hints_text` is empty, so none are public).

So the relaxation is confined to behaviour (3); the `../`-removal core
(behaviours 1-2, in both image formats) is fully public.

## Why behaviour (3) is genuinely necessary (not lazy de-narration)

### The gold's tested discriminator includes the external node

Gold hunk (`sphinx/ext/inheritance_diagram.py`, `html_visit_inheritance_diagram`):

```python
# Construct the name from the URI if the reference is external via intersphinx
if not child.get('internal', True):
    refname = child['refuri'].rsplit('#', 1)[-1]
else:
    refname = child['reftitle']

urls[refname] = child.get('refuri')
```

The rewritten F2P test adds an intersphinx external inventory and asserts, for
every SVG diagram link:

```python
# Verify that an intersphinx link was created via the external inventory
if 'subdir.' in diagram_content:
    assert "https://example.org" in diagram_content
...
for href in re.findall('href="(\\S+?)"', diagram_content):
    if '://' in href:
        assert href.startswith("https://example.org/")   # absolute URL, no ../
```

The external node's pending_xref carries `refuri =
"https://example.org/foo.html#subdir.other.Bob"` with `internal=False`. Before
the fix the dict was keyed by `child['reftitle']`, and the external node's
absolute URL never reached the SVG (the test's
`assert "https://example.org" in diagram_content` would fail). The fix derives
the key from the URI's trailing component so the node is registered and its
absolute URL is emitted. A partial patch that drops *only* behaviour (3) (keeps
the `../` removal but keys the external reference by reftitle) leaves
`https://example.org` out of the SVG and fails F2P. So behaviour (3) is a TESTED
discriminator, not cosmetic.

### The public problem_statement says nothing about intersphinx/external keys

The `problem_statement` is a symptom report about the `../` over-climb only. It
never mentions intersphinx, external inventories, reference keys, internal-vs-
external selection, or trailing-component extraction. There is no PS-derivable
reformulation that both models the gold fix (which the rewritten F2P test
exercises through an intersphinx node) and avoids naming the external-key
behaviour. Drop it and the spec is unfaithful to the F2P test; name it and the
spec view narrates a behaviour absent from the public issue. That is the
definition of a PS<->gold mismatch.

## Why this is NOT a soundness defect

The `verify => correct` chain is intact and was re-verified after the
image-format refinement (the clause set now pins both formats):

- **G-VERIFY: PASS** — `model.py` verifies (~20s, no flags, no float encoding;
  the stamped figure is `meta.json gates.G-VERIFY`).
- **G-DIFF: PASS** — three prepatch twins each FAIL on their discriminating
  postcondition: `model_prepatch.py` (`'../' + dest_uri` on the vector arm) on
  `ToSeq(Result()) == ToSeq(dest_uri)`; `model_prepatch_2.py`
  (`'../' + current_doc_name + '#' + anchor_id` on the vector arm) on
  `Implies(vector_format, ToSeq(Result()) == ToSeq(current_doc_name) + PSeq(35)
  + ToSeq(anchor_id))`; `model_prepatch_3.py` (whole URI used as key) on
  `ToSeq(Result()) == after_last_hash(ToSeq(dest_uri))` when the URI carries a
  `#`. Each twin is faithful to the pre-patch code in BOTH formats: the pre-patch
  raster arms were already correct, so only the vector arms carry `'../'`.
  `same_spec == True` (axioms / pure / pre / post regions and the module
  docstring byte-identical across all four twins; spec_view sha256
  `2a6542966a3f5bdb1318a145591dde1f5465753dea3b58298f80dd80c170a38d`).
- **G-MUT: PASS** — impl mutants killed (the exact-sequence take/drop
  postconditions leave no slack).
- **G-EQ: SOUND/TIGHT** — refinement.md all R / A-reference / I, no kind-3. The
  changed string ops (drop the `../` prefix; make the destination link
  format-independent; derive the external key from the URI's trailing
  component) are each modeled DEEPLY and grounded in the actual input carrier
  (directive 8 — each `Ensures` pins `Result()` to a structural function of the
  input sequence, `== ToSeq(dest_uri)`,
  `== ToSeq(current_doc_name) + PSeq(35) + ToSeq(anchor_id)` under
  `vector_format`, `== PSeq(35) + ToSeq(anchor_id)` under its negation,
  `== after_last_hash(ToSeq(dest_uri))`, never to an opaque oracle).
- **G-AX: SOUND (vacuous for consumed axioms)** — no `@ContractOnly` axioms; the
  three A-reference deep models are validated == the REAL Python string ops in
  both image formats (`refuri` identity; `cf + '#' + refid` vs `'#' + refid`;
  `refuri.rsplit('#', 1)[-1]`; and `'://' in s`) by `axiom_check.py`, which runs
  RC=0 in the pinned eval container
  `swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-10614:latest` on 19
  boundary + 40000 fuzz inputs.
- **G-CONF: PASS** — the contract-stripped impl region is differentially
  compared against the real patched `html_visit_inheritance_diagram`, driven
  with `graphviz_output_format` in {`svg`, `SVG`, `Svg`, `png`, `PNG`, `pdf`},
  and additionally checks that the two formats' real anchor links DIFFER — so
  the modelled format observable is measured in the real code, not assumed.
- **G-RESOLVE** — `patch.diff` == gold verbatim (1276 B), applies cleanly at
  `base_commit`; harness `resolved` (orchestrator Docker run).

The mechanical G-LEAK screen passes (the spec view names no patched path/symbol
and quotes no diff line; the patched identifiers `refuri`/`refid`/
`current_filename`/`graphviz_output_format` appear only as the abstract
`dest_uri` / `anchor_id` / `current_doc_name` / `vector_format`). But behaviour
(3) is a SEMANTIC leak: the external-key derivation is ABSENT from
`problem_statement` yet LOAD-BEARING for faithfulness, which is precisely when a
clean `pass` is wrong and `relaxed` is required. The adversarial reconstruction
judgment is binding and establishes the PS<->gold mismatch.

## Conclusion

KEEP under the relaxed-leakage policy: the core is sound and the gold resolves,
but the gold's intersphinx/external-key discriminator (behaviour 3) is settled
only in the gold patch and the rewritten F2P test while the public
`problem_statement` is a `../`-over-climb symptom report, so a faithful spec
cannot avoid narrating the external-reference key behaviour. The relaxed delta is
narrow (behaviour 3 only; the `../`-removal core in behaviours 1-2 is already
public, in both image formats). `meta.json` records
`gates.G-LEAK.status = "relaxed"` with a pointer to this document.
