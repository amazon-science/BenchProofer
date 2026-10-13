# mapping.md — sphinx-doc__sphinx-10673

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f35d2a6cc726f97d0e859ca7a0e1729f7da8a6c8`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one grounded R-binding.

Repo file under change (modeled site): `sphinx/directives/other.py`.
Spec provenance: **cold** (derived from problem_statement + gold patch + repo
source at base_commit only).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectToctreeEntries (requested sourceDocs autoTargets)` | `TocTree.parse_content` — `sphinx/directives/other.py:79` (validity decision + append loop, body lines 88–140) | the modeled changed function: decide which content entries become `toctree['entries']` |
| `targetExists (sourceDocs autoTargets) (name)` | the post-patch membership test `docname in self.env.found_docs \| generated_docnames` — `sphinx/directives/other.py:121` (post-patch) | pure spec: an entry names a valid target |
| `retainedEntries (sourceDocs autoTargets)` | the per-entry `else`-branch append to `toctree['entries']` inside `for entry in self.content` — `sphinx/directives/other.py:88,139` | pure spec: the request-order filter of valid entries |
| `requested` | the directive `content` lines (plain entries) | input: requested entry names |
| `sourceDocs` | `self.env.found_docs` (`set[str]`) | input: docnames with a backing source file |
| `autoTargets` | `generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())` — `sphinx/directives/other.py:80` (post-patch) | input: auto-generated reference targets; **grounded** by G-AX |

Pre-patch repo expression the change replaces (refinement audit only, not in the
consumer spec view): the validity test `docname not in self.env.found_docs`
(`other.py:121` pre-patch) and the seed `all_docnames = self.env.found_docs.copy()`
(`other.py:83` pre-patch) — both without the `| generated_docnames` union.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a docname `str` (a content entry, a `found_docs` member, a generated key) | `String` | identity on the BMP strings the test/fuzzer use; equality ↔ `String` `=` / `==` |
| `self.content` (ordered entry lines) | `requested : List String` | line order ↔ list order; the F2P entries are simple, suffixless, top-level names so the suffix-strip loop (`other.py:113-116`) and `docname_join` (`other.py:118`, `posixpath.normpath` of a bare name) are the identity on them |
| `self.env.found_docs` (`set[str]`) | `sourceDocs : List String` | set membership ↔ `List.contains`; order irrelevant (only membership observed). Duplicates in the list are harmless (membership is idempotent) |
| `generated_docnames` (`frozenset` of label keys) | `autoTargets : List String` | key set membership ↔ `List.contains`; grounded to `{genindex,modindex,search}` by G-AX (§3) |
| `docname in found_docs \| generated_docnames` (set-union membership) | `targetExists … = sourceDocs.contains e \|\| autoTargets.contains e` | `x ∈ A ∪ B ↔ x ∈ A ∨ x ∈ B` (De Morgan); set-union ↔ boolean disjunction of `.contains` |
| the appended `toctree['entries']` `(title, docname)` pairs (plain entries: `title = None`) | `out : List String` (the docnames) | the F2P test compares entry **docnames**; titles are `None` for plain entries, carried implicitly |

Out of modeled scope (refinement.md §C): the glob branch, the URL/`self`
branches (the test uses none), and the two downstream gold hunks in
`adapters/toctree.py` and `collectors/toctree.py` (rendering + fignum walk),
which the F2P `test_toctree_index` does not observe.

## 3. Grounded R-binding (kind-A-adjacent — checked by G-AX / axiom_check.py)

### 3.1 `autoTargets` ↔ `generated_docnames` (grounded R-binding, NOT a consumed axiom)
**Source:** the std domain's `labels` initial data, `sphinx/domains/std.py:587-594`:
```python
initial_data = {
    ...
    'labels': {             # labelname -> docname, labelid, sectionname
        'genindex': ('genindex', '', _('Index')),
        'modindex': ('py-modindex', '', _('Module Index')),
        'search':   ('search', '', _('Search Page')),
    },
    ...
}
```
The patched `parse_content` computes `generated_docnames` as
`frozenset(self.env.domains['std'].initial_data['labels'].keys())` — exactly the
three keys `{genindex, modindex, search}`. This set is the value flowing into
`autoTargets`. There is **no consumed axiom and no deep-model reference**:
`autoTargets` is a free input of the method, and the modeled decision is pure
membership logic. The only repo fact the refinement leans on is the *identity of
this set*, which decides how the conformance oracle and the F2P scenario are
driven.

**Grounding check (G-AX):** `axiom_check.py` imports the real repo
`sphinx.domains.std.StandardDomain` (in-container, gold patch applied) and
asserts `set(initial_data['labels'].keys()) == {genindex, modindex, search}`
(and that values are 3-tuples). Exit 0 iff the grounding holds. Imports only the
repo's own `sphinx`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10673`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `targetExists`/`retainedEntries`/`selectToctreeEntries` (all R/I
ops) to Python; the oracle transliterates the patched acceptance predicate
`docname in found_docs | generated_docnames` and reconstructs the ordered entry
list `parse_content` appends. There are no A-tagged callees to leave real
(the bundle has no axioms / deep-model references), so the whole impl is R/I
(conf_skip=false).
