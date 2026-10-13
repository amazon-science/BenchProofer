# mapping.md — sphinx-doc__sphinx-10673

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f35d2a6cc726f97d0e859ca7a0e1729f7da8a6c8`, states the type
abstraction, and gives the provenance of the modeled behaviour and the single
A-reference the deep model is validated against.

Repo files under change:
`sphinx/directives/other.py`, `sphinx/environment/adapters/toctree.py`,
`sphinx/environment/collectors/toctree.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_toctree_entries(entries, found, generated)` | `TocTree.parse_content(self, toctree)` — `sphinx/directives/other.py:79` (the per-entry classification loop, body lines 88-140) | the modeled changed function: classifies each listed toctree target and builds the retained `toctree['entries']` list |
| `found` (param) | `self.env.found_docs` — `sphinx/environment/__init__.py` `BuildEnvironment.found_docs` (the discovered source documents), read at `other.py:83,121` | the discovered-source family |
| `generated` (param) | `generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())` — added at `other.py:80` post-patch; the keys are `{'genindex','modindex','search'}` from `sphinx/domains/std.py:590-594` `StandardDomain.initial_data['labels']` | the always-provided reference-page family |
| `entries` (param) | the suffix-stripped, `docname_join`-absolutized target names iterated from `self.content` in the non-glob branch (`other.py:104-140`) | the listed targets, in order |
| `known(x, found, gen)` *(deep model — A-reference)* | the membership test `docname in self.env.found_docs | generated_docnames` — `other.py:121` post-patch (was `docname not in self.env.found_docs` pre-patch) | pure spec: a target is known iff in EITHER family |
| `mem(x, s)` | Python `in` on a `set`/`frozenset` of document names | pure spec: set membership, modeled as a sequence-membership fold |
| `kept(entries, found, gen)` *(deep model — A-reference)* | the order-preserving accumulation into `toctree['entries']` of the targets that pass the membership test (the loop at `other.py:104-140`, retaining `(title, docname)` exactly when `docname in found_docs | generated_docnames`) | pure spec: the retained, order-preserving entry list |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): at `other.py:121` the test was
`elif docname not in self.env.found_docs:` — a target naming a generated
reference page (`genindex`/`modindex`/`search`), which is not a discovered
source document, fell into the warning branch (`'toctree contains reference to
nonexisting document %r'`, `other.py:126-131`) and was **never appended** to
`toctree['entries']`. The patch widens the universe to
`self.env.found_docs | generated_docnames`, so such a target is retained.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a document name (`str`, e.g. `'genindex'`, `'foo'`) | a distinct `int` identifier | each distinct name ↔ a distinct int; equality of names ↔ equality of ints. Only equality/membership of names is observed by the classification, so the int abstraction is faithful (the suffix-stripping / `docname_join` normalization that produces each name happens BEFORE this classification and is identity on the F2P targets `genindex`/`modindex`/`search`, which carry no suffix and no `/`). |
| `self.env.found_docs` (a `set[str]`) | `found: List[int]` | a set of names ↔ a list of int ids; membership `name in found_docs` ↔ `mem(id, ToSeq(found))`. Order/duplication in `found` is irrelevant to membership (checked by axiom_check.py fuzz). |
| `generated_docnames` (a `frozenset[str]`) | `generated: List[int]` | likewise; the three real members map to three distinct ids. |
| `self.env.found_docs | generated_docnames` (set union) | `known(x, found, gen) == mem(x, found) or mem(x, gen)` | set-union membership ↔ disjunction of the two membership folds (a standard set-union law; validated by axiom_check.py). |
| `toctree['entries']` accumulation of `(title, docname)` | `Result(): List[int]` of retained ids, in order | the model tracks only the `docname` component and its order/presence (what the F2P test asserts: `entries=[(None,'genindex'),(None,'modindex'),(None,'search')]`); `title` is `None` for these targets and is omitted (mapping.md §3). |

`str` indexing/iteration is banned in Nagini, and the classification observes
only name equality/membership, so document names are modeled as opaque `int`
ids and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Behaviour provenance and the A-reference (checked by G-AX / axiom_check.py)

### 3.1 The classification is modeled DEEPLY (no consumed axiom)
There is **no `@ContractOnly` axiom** in this bundle. The changed operation —
deciding which listed targets are retained — is the patch's own logic
(`docname in self.env.found_docs | generated_docnames`), built from Python set
union and membership. These are not opaque library callees with surprising
semantics; they are spelled out deeply as the `mem` / `known` / `kept` folds.

### 3.2 `kept` deep model ↔ real set-union membership (A-reference)
The deep model `kept` is validated **equal to the real semantics** out-of-band
by `axiom_check.py` (G-AX): for any `entries`, `found`, `generated`,

  `kept(entries, found, generated)` ==
  `[e for e in entries if e in (set(found) | set(generated))]`

which is exactly the order-preserving subset of targets satisfying
`docname in self.env.found_docs | generated_docnames` (`other.py:121`
post-patch). axiom_check.py asserts this on 9 boundary cases + 50 000 fuzz
inputs and on the concrete F2P scenario (the three generated reference-page ids
present in `generated`, absent from `found`, all retained in order). It imports
only the Python standard library (`random`), nothing repo-specific — set union
and membership are language primitives.

### 3.3 Why the other two patched files are not separately modeled
The FAIL_TO_PASS test `tests/test_environment_toctree.py::test_toctree_index`
asserts on `app.env.tocs['index']`, whose toctree `entries` lists are populated
by `process_doc` → `TocTree.parse_content`. The asserted discriminator is
exactly `entries=[(None,'genindex'),(None,'modindex'),(None,'search')]` — the
output of the classification in `parse_content`. The two further gold hunks
(`environment/adapters/toctree.py::TocTree.resolve`’s `_entries_from_toctree`
rendering branch for `ref in generated_docnames`, and
`environment/collectors/toctree.py::assign_figure_numbers._walk_doctree`’s skip
of generated docnames) operate during toctree resolution / figure numbering in
the full build; they do not alter the `env.tocs` entry lists the F2P test
inspects. They are shipped verbatim in `patch.diff` (which is the gold patch and
the real correctness oracle, G-RESOLVE) but are not independently observable
from the F2P assertion, so they are not given a separate failing
`model_prepatch_<k>`; the single modeled site (`parse_content`) is the
F2P-discriminating behaviour. See refinement.md §B.
