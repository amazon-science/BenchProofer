# refinement.md — sphinx-doc__sphinx-10673

Maps every operation in `implementation_tocEntries` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `tocEntries` (the accepted-entry loop of `TocTree.parse_content`)

Post-patch repo code (`patch.diff` / `other.py`), the modeled ops:
```python
generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())
...
for entry in self.content:
    if not entry:
        continue
    ...
    # plain-reference branch (non-glob, non-explicit-title, non-url, non-self)
    ref = docname = entry
    ...
    elif docname not in self.env.found_docs | generated_docnames:
        ...  # rejected: nonexisting document, NO entry appended
    else:
        toctree['entries'].append((title, docname))   # accepted: (None, docname)
```

Lean impl (`implementation_tocEntries`): an imperative `Id.run do` accumulator
loop over `requested`, appending `(none, entry)` for each non-blank entry whose
name is in `existingDocs ++ generatedPages`.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `requested : List String` | `self.content` (directive body lines) | **R** | `list[str]` ↔ `List String`; the per-line iteration domain. mapping.md bijection. |
| 2 | `existingDocs : List String` | `self.env.found_docs` (a `set[str]`) | **R** | the existing-document name set; modeled membership-only as a `List String` (order/duplication immaterial — only `.contains` is used). |
| 3 | `generatedPages : List String` | `frozenset(self.env.domains['std'].initial_data['labels'].keys())` = `{'genindex','modindex','search'}` | **R** | **the added input.** The patch introduces `generated_docnames` (`other.py:80`). Its three labelnames are a fixed constant of the std domain (`std.py:587-593`); modeled as the supplied list of those names. Its *value* is consumed (the names), not the dict-walk — a constant lookup, so a direct R refinement, not an axiom. |
| 4 | `let mut entries := []` | `toctree['entries']` starts empty (for the modeled plain-reference contributions) | **I** | initial accumulator. |
| 5 | `for entry in requested do` | `for entry in self.content:` | **I** | identical iteration. |
| 6 | `if entry == "" then pure ()` | `if not entry: continue` | **I** | the blank-line skip — a blank line contributes no entry. |
| 7 | `else if (existingDocs ++ generatedPages).contains entry then entries := entries ++ [(none, entry)]` | `elif docname not in self.env.found_docs \| generated_docnames: <reject> else: toctree['entries'].append((title, docname))` | **I** (the changed op, deeply modeled) | **the fixed operation.** The accept test is membership in the UNION `found_docs ∪ generated_docnames`; pre-patch it was `found_docs` only. The set-union `\|` ↔ `(existingDocs ++ generatedPages).contains` (list-append then membership = union membership). Accepted ⇒ append `(None, docname)`; `title` is `None` for a bare line (op 6's `ref = docname = entry`, no explicit title). The `docname_join`/suffix-strip steps are identity on the F2P inputs (no suffix, current docname is the index root) — outside the modeled abstraction; mapping.md. |
| 8 | `else pure ()` | the reject arm (`elif … not in …:` logs a warning, no append) | **I** | a reference naming neither an existing document nor a generated page contributes no entry. The warning is a side effect outside the modeled value (the entry list); the OBSERVABLE consequence — no entry — is modeled. |
| 9 | `return entries` (`List (Option String × String)`) | `toctree['entries']` (the accepted `(title, docname)` pairs) | **R** | result modeled as `List (Option String × String)`; `none` ↔ `None`, the target string ↔ `docname`. Order preserved (append order = source order). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch accepted-entry computation.

## Multi-site note (why one triple is faithful)
The gold patch touches three files, but they implement ONE behavior change —
"the builder-generated pages `genindex`/`modindex`/`search` are valid toctree
targets" — at three points in the pipeline:
- `directives/other.py` `parse_content` — **accept** such a line as an entry
  (the modeled site; this is what the F2P test observes via `app.env.tocs`).
- `environment/adapters/toctree.py` `resolve`/`_entries_from_toctree` — **render**
  such an entry as a reference node when building the visible toctree.
- `environment/collectors/toctree.py` `assign_figure_numbers` — **skip** such an
  entry when walking for figure numbering.
The latter two are downstream consumers gated on the SAME generated-docname set;
they are not independently exercised by the single F2P test
(`test_toctree_index`, which asserts the `entries` list produced by
`parse_content`). Modeling the `parse_content` acceptance decision captures the
fixed behavior the F2P test pins; the other two are unchanged-by-default consumers
of the same set (a name only reaches them once `parse_content` accepts it). Hence
ONE `Solution_prepatch.lean` (the acceptance bug) is the single
independently-observable fixed behavior for G-DIFF.

## Soundness check (verify ⟹ correct)

- `problem_spec_tocEntries` pins `result` as a TOTAL function of the inputs (a
  single `filter`/`map` equation — directive 5 frame: the entire entry list is
  determined, nothing left unconstrained; directive 8: grounded entirely in
  `requested`/`existingDocs`/`generatedPages`, no ungrounded oracle). A verifying
  impl MUST drop blanks, accept exactly the non-blank names in
  `existingDocs ∪ generatedPages`, in source order, each as `(none, name)`.
- The discriminating clause is membership in `generatedPages`: for a non-blank
  `e ∈ generatedPages \ existingDocs`, the spec demands `(none, e)` appear in the
  result. The prepatch impl tests `existingDocs.contains e` only, so it drops such
  an `e` — the carried gold proof's `key` lemma step fails to reduce
  (`existingDocs.contains` ≠ `(existingDocs ++ generatedPages).contains`), so the
  prepatch `correct_tocEntries` does not typecheck (G-DIFF/G-PANEL). Confirmed:
  `Solution_prepatch.lean` fails verification (exit 1).
- This is exactly what `test_toctree_index` exercises: `genindex`/`modindex`/
  `search` are in the generated set but not in `found_docs`; post-patch they
  become entries, pre-patch they do not.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  accepted-entry computation over ≥1e5 fuzzed inputs (random line lists drawn from
  generated names, existing names, blanks, and unknown names) plus an exhaustive
  edge enumeration — 0 disagreements.
