# mapping.md — sphinx-doc__sphinx-10673

## Symbol binding (file:line @ base_commit f35d2a6cc726f97d0e859ca7a0e1729f7da8a6c8)

Modeled function: the entry-collection loop of the table-of-contents directive,
`TocTree.parse_content(self, toctree)`, `sphinx/directives/other.py:79-147`. For
each line of the directive body it decides whether that line names a valid target
and, if so, appends an entry to `toctree['entries']`.

The gold patch makes the **builder-generated reference pages** (`genindex`,
`modindex`, `search`) acceptable targets. These pages are registered in the std
domain's `initial_data['labels']` (`sphinx/domains/std.py:587-593`); their
*labelnames* are exactly the docnames a user writes in a toctree to link them.
Pre-patch a toctree line naming one of them was rejected as a "nonexisting
document"; post-patch it is accepted (the union `found_docs | generated_docnames`).

The modeled decision is the per-line non-glob branch (`other.py:104-140`),
restricted to the F2P-observable behavior — whether a listed reference becomes an
accepted `(title, target)` entry:

```python
# post-patch (other.py:79-140, the relevant ops)
def parse_content(self, toctree):
    generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())
    ...
    for entry in self.content:
        if not entry:
            continue
        ...
        # (non-glob, non-explicit, non-url branch)
        ref = docname = entry
        ...
        if url_re.match(ref) or ref == 'self':
            toctree['entries'].append((title, ref))
        elif docname not in self.env.found_docs | generated_docnames:
            ...  # WARNING: nonexisting document  -> NO entry appended
        else:
            ...
            toctree['entries'].append((title, docname))
```

```python
# pre-patch (base_commit, other.py:79-140)
def parse_content(self, toctree):
    # (no generated_docnames)
    for entry in self.content:
        if not entry:
            continue
        ...
        elif docname not in self.env.found_docs:
            ...  # WARNING for genindex/modindex/search -> NO entry appended
        else:
            toctree['entries'].append((title, docname))
```

Lean modeled function name: `tocEntries` (names the *behavior* — "the accepted
entries of a table-of-contents directive" — at the abstract level; it does not
echo a patched repo symbol such as `parse_content`, `found_docs`,
`generated_docnames`, or `initial_data`).

### Modeling scope (what is and isn't modeled)
The F2P test `test_toctree_index` asserts the `entries` list of a toctree built
from a directive whose lines are ordinary documents (`foo`) and generated pages
(`genindex`, `modindex`, `search`): post-patch all of them become entries. The
modeled value is exactly this accepted-entry list for the **plain (non-glob,
non-explicit-title, non-URL, non-`self`) lines** — the branch the fix touches.
Glob lines, explicit-title (`Title <doc>`) lines, URL/`self` lines, suffix
stripping, `docname_join` absolutization, the duplicate-entry bookkeeping
(`all_docnames`), and the `reversed` option are OUTSIDE the modeled decision:
they are unchanged by the fix and orthogonal to the F2P behavior. (The other two
patched files — `adapters/toctree.py` rendering and `collectors/toctree.py`
fignumber-skipping — are downstream consumers of the same generated-docname set;
they are not independently exercised by the F2P test, which inspects
`app.env.tocs['index']` entries produced via `parse_content`. See refinement.md.)

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `requested : List String` | `self.content` — the directive body lines, one reference per non-blank line (`other.py:88`, the `for entry in self.content` loop). |
| `existingDocs : List String` | `self.env.found_docs` — the set of docnames the project contains (`other.py:121`, `docname not in self.env.found_docs`). Modeled as the list of those names. |
| `generatedPages : List String` | `frozenset(self.env.domains['std'].initial_data['labels'].keys())` — `{'genindex', 'modindex', 'search'}` (`other.py:80` post-patch; `sphinx/domains/std.py:587-593`). Modeled as the list of those labelnames. |
| blank-line skip | `if not entry: continue` (`other.py:89-90`) ↔ `if entry == "" then (skip)`. |
| accept test | `docname in self.env.found_docs | generated_docnames` (post-patch `other.py:122`) ↔ `(existingDocs ++ generatedPages).contains entry`. |
| `result : List (Option String × String)` | `toctree['entries']` restricted to the accepted plain-reference entries; each is `(title, docname)` with `title = None` for a bare line (`other.py:111, 139`). `none` ↔ Python `None`; the target string is the entry name. |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.content : list[str]` (directive body lines) | `requested : List String` |
| `self.env.found_docs : set[str]` | `existingDocs : List String` (membership-only; order/duplication immaterial) |
| `initial_data['labels'].keys() : {'genindex','modindex','search'}` | `generatedPages : List String` |
| `entry == ''` / `not entry` | `entry == ""` |
| `docname in found_docs | generated_docnames` | `(existingDocs ++ generatedPages).contains entry` |
| `toctree['entries']` (accepted `(None, docname)` pairs) | `result : List (Option String × String)` |
| `None` (no explicit title) | `(none : Option String)` |

### Post-patch decision (the modeled value)
```
entries = [ (None, e)  for e in content  if e != '' and e in (found_docs ∪ generated_pages) ]
```
which is exactly `problem_spec_tocEntries` / `implementation_tocEntries`.

### Pre-patch decision (the bug the prepatch encodes)
```
entries = [ (None, e)  for e in content  if e != '' and e in found_docs ]
```
`generated_docnames` does not exist pre-patch, so a line naming `genindex` /
`modindex` / `search` fails the `in found_docs` test and is rejected (a
"nonexisting document" warning, no entry). The prepatch Lean impl encodes this by
testing membership in `existingDocs` only.

### Discriminating behavior (the F2P test)
`test_toctree_index` builds testroot `toctree-index` whose `index.rst` has a
second toctree listing `genindex`, `modindex`, `search`. It asserts that toctree's
`entries == [(None,'genindex'), (None,'modindex'), (None,'search')]`.
- Post-patch: those three names are in `generated_docnames` ⇒ all three accepted ⇒
  `entries` has the three pairs. Test passes.
- Pre-patch: none is in `found_docs` ⇒ all three rejected ⇒ `entries == []` (and
  three warnings). Test fails.

The PASS_TO_PASS tests (`test_glob`, `test_get_toctree_for*`, `test_process_doc`,
…) all use toctrees over ordinary existing documents, whose acceptance is
unchanged (a name in `found_docs` is accepted both pre- and post-patch, since
`found_docs ⊆ found_docs ∪ generated_pages`).

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** Every observation the modeled
  decision uses is directly supplied: the directive lines (`self.content`), the
  existing-document name set (`self.env.found_docs`), and the generated-page name
  set (`initial_data['labels'].keys()`, a fixed three-element constant). The
  accept test is plain set/list membership and the blank test is string equality
  — both spelled out directly in the Lean impl. ⇒ `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub (G-AX skips).
- **Branch/flag dependency:** the modeled branch is the plain-reference path —
  it fires when the line is non-blank, not a glob (no `*?[`), not an explicit
  `Title <doc>` form, and not a URL or `self`. The F2P toctree lines
  (`genindex`/`modindex`/`search`/`foo`) are all plain references, so the modeled
  domain is exactly the in-branch domain. Recorded so G-CONF fuzzes plain
  reference names only (the orthogonal glob/explicit/url paths are unchanged by
  the fix).

## G-LEAK
The solver-visible `problem_statement` publicly names `toctree`, `genindex`,
`modindex`, `search`, and the symptom ("toctree contains reference to nonexisting
document"). The spec view (Solution.lean minus impl+proof regions, incl. the
docstring) names NO patched file path, NO gold-diff line, NO diff marker, and NO
patched repo symbol — `parse_content`, `found_docs`, `generated_docnames`,
`initial_data`, `labels`, `std`, `domains` appear NOWHERE in the spec view,
neither as identifiers nor in comments. It also does NOT use the public symptom
strings `genindex`/`modindex`/`search`/`toctree`; it states the abstract behavior
("special reference pages — the general index, the module index, and the search
page") without the bug→fix mechanism (no mention of a "union with found_docs" or
the missing-set diagnosis).

## Pinned G-CONF fuzz seed
`10673`.
