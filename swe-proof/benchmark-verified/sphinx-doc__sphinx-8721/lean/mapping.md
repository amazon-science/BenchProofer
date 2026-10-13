# mapping.md — sphinx-doc__sphinx-8721

## 1. Symbol binding (file:line @ base_commit 82ef497a)

- Modeled function: `collect_pages(app)` — `sphinx/ext/viewcode.py:181`
  (the `html-collect-pages` event handler, registered at
  `sphinx/ext/viewcode.py:285`).
- `collect_pages` is a generator; its observable behavior is the SEQUENCE of
  `(pagename, context, template)` triples it yields. An early `return` makes it
  yield NOTHING (an empty sequence).

### What is modeled, and what is deliberately not

The gold patch inserts two early-return guards at the top of the function body,
immediately AFTER the pre-existing `if not hasattr(env, '_viewcode_modules'):
return` and BEFORE the page-construction work:

```python
    if app.builder.name == "singlehtml":                                             # (i)
        return
    if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub:  # (ii)
        return
```

Only guard **(ii)**, the electronic-book one, is described by the public
`problem_statement` ("module pages should not be created for epub by default"),
and only (ii) is exercised by any FAIL_TO_PASS / PASS_TO_PASS test
(`test_viewcode_epub_default`, `test_viewcode_epub_enabled`, `test_linkcode`,
`test_local_source_files`; the shipped test set contains no single-file build).
The model therefore specifies exactly the tested electronic-book behaviour. The
single-file co-change (i) is carried verbatim by `patch.diff` — the correctness
oracle, so G-RESOLVE and `verify ⇒ resolved` are untouched — but is not part of
the modeled, consumer-visible behavioural contract.

**This scoping is a disclosed modeling boundary, and it costs the model no
faithfulness at the single-file format.** The reason is the type bridge for
`generatedPages` in §2: that carrier is *what the active output format publishes
for this build when the electronic-book preference does not withhold it*, which
at the single-file format is the EMPTY sequence — guard (i) sits upstream of the
preference and fires regardless of its value. So the model's fall-through leg
predicts `[]` at the single-file format, which is what the real post-patch
function actually yields, rather than predicting a publish the repo does not
perform. G-CONF checks this over the whole domain with NO output-format name
excluded (§4).

## 2. Lean ↔ Python type bridge (used by G-CONF)

| Lean | Python | note |
|---|---|---|
| `hasModules : Bool` | `hasattr(env, '_viewcode_modules')` | `true ↔ True` |
| `builderName : String` | `app.builder.name : str` | byte-for-byte string |
| `enableEpub : Bool` | `env.config.viewcode_enable_epub : bool` | `true ↔ True`; declared default `False` at `viewcode.py:281` |
| `generatedPages : List String` | **the sequence of pages the active output format publishes for this build when the electronic-book preference does not withhold it** — obtained from the real `collect_pages` with `viewcode_enable_epub` forced `True` | each `String` is a yielded page's name; the two premises below are what make this a bridge |
| `result : List String` | the materialized sequence of yielded pages | `[] ↔` the generator returns immediately (yields nothing) |
| `String.startsWith` | `str.startswith` | single-prefix form only (no `start`/`end` args at the call site) |

`generatedPages` is left universally quantified in the spec: the modeled
behaviour decides only WHETHER that whole sequence is published, never what it
contains.

### Why the forced-preference bridge is a bridge and not an answer key

Two premises, both MEASURED against the real post-patch callee by
`conformance_check.py` (`check_bridge_facts`) rather than assumed:

* **(A)** Off the electronic-book family, the preference does not affect the
  published sequence at all. So forcing it on only ever reaches the unchanged
  page-construction body; it cannot pre-empt a decision the specification is
  responsible for. (That body — `highlighter = ...` through both `yield`s —
  never reads the preference.)
* **(B)** On the electronic-book family, with the preference forced ON the format
  publishes its FULL sequence. So the electronic-book decision is emphatically
  NOT baked into `generatedPages`: the specification still has to make it, which
  is what keeps the obligation discriminating. A negative control confirms this
  operationally — a shadow with the electronic-book guard REMOVED disagrees with
  the real callee (measured: 6 disagreements), so the carrier cannot be used to
  smuggle in the answer.

## 3. Callee / attribute provenance + flag deps

| repo expression | role | provenance | flag dep |
|---|---|---|---|
| `hasattr(env, '_viewcode_modules')` | gate: was any module data collected | env attribute set by `doctree_read` (`viewcode.py:53+`), UNCHANGED | — |
| `app.builder.name` | the active output format's registered name | `Builder.name` class attr (`sphinx/builders/__init__.py`), UNCHANGED | — |
| `str.startswith("epub")` | does the name begin with the electronic-book family prefix | Python stdlib, UNCHANGED | — |
| `env.config.viewcode_enable_epub` | bool config, default `False` (declared `viewcode.py:281`) | UNCHANGED config value | the electronic-book guard fires only when this is `False` |
| page construction (`viewcode.py:185–276` post-patch) | builds & yields the per-module pages + the trailing index page | UNCHANGED downstream work; represented by `generatedPages` per §2 | reads no preference (premise (A)) |

## 4. G-CONF domain and seed

Pinned seed: **8721**. `conformance_check.py` diffs the shadow against the real
patched `collect_pages` over boundary cases + 1e5 fuzzed inputs.
`excluded_builder_names` is **empty**: every output-format name — including the
single-file one and its near-misses (`"singlehtm"`, `"singlehtmlx"`,
`"ssinglehtml"`, `"singlehtmlepub"`, `"epubsinglehtml"`) — is inside the checked
domain, and the electronic-book prefix boundary (`""`, `"e"`, `"ep"`, `"epu"`,
`"epub"`, `"epub2"`, `"epub3"`, `"epubfoo"`, `"Epub"`, `"EPUB"`, `"htmlepub"`) is
exercised on both sides.

## 5. Axioms

No `opaque`/`axiom` callee contract is required: the modeled behaviour is a pure
control-flow decision over `(hasModules, builderName, enableEpub)` and the
downstream page-construction work is universally quantified, so the proof
consumes no property of any callee. `axiom_check.py` is a skip stub.
