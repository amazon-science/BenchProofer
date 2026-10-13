# mapping.md — sphinx-doc__sphinx-7440

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 9bb204dcabe6ba0fc422bf4a45ad0c79c680d90b
- changed file: `sphinx/domains/std.py` (two sites)
- spec_provenance: cold

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_glossaryTermEntry` / `problem_spec_glossaryTermEntry` / `correct_glossaryTermEntry` | `make_glossary_term`, the `note_object('term', …)` registration + the index-entry construction | `sphinx/domains/std.py:307` (and `:309-310` for the index entry) |
| `implementation_termXrefTarget` / `problem_spec_termXrefTarget` / `correct_termXrefTarget` | the `'term'` cross-reference role's target computation (`XRefRole.create_xref_node`, governed by the role's `lowercase` flag) | role declared at `sphinx/domains/std.py:567`; target folding at `sphinx/roles.py:146-147` |

## What the fix changes

The repository registers and resolves glossary terms under a cross-reference
key derived from the term's text. At two coordinated sites the key was reduced
to a single canonical case before use, while the index entry / displayed term
kept the term's original characters. As a result two terms whose texts differ
only in letter case (e.g. `MySQL` vs `mysql`) collapsed to one key and a term's
registered key disagreed with its index entry.

- **Registration site** (`make_glossary_term`): the term text `termtext` is used
  to build BOTH the cross-reference key passed to `note_object` AND the index
  entry term. Pre-patch the key argument applied a case fold (`termtext.lower()`)
  while the index entry used the un-folded `termtext`; post-patch both use the
  un-folded `termtext`.
- **Lookup site** (the `'term'` role): the reference target was case-folded before
  lookup when the role's case-folding flag was set; post-patch the flag is unset,
  so the target is used as written.

Both reduce to the same modeled behavior: the term identifier is the term text
with its exact characters preserved, including letter case.

## Lean ↔ Python type bijection (used by G-CONF, G-AX)

A Python `str` operated on per code point is modeled as `List Char` (cheatsheet,
SPEC_GUIDE §2). The case fold `str.lower()` is modeled as `List.map Char.toLower`
over the ASCII letter range (see fuzz note). Identity passes the term through
unchanged.

### Registration site (`make_glossary_term`)
| Python | Lean | bijection |
|---|---|---|
| `termtext` (the term's text) | `termtext : List Char` | per-code-point identity |
| object key arg of `note_object('term', termtext, …)` | `result.1 : List Char` | identity (post-patch); the modeled changed value |
| index entry term in `indexnode['entries'] = [('single', termtext, …)]` | `result.2 : List Char` | identity; the unchanged frame component |

### Lookup site (the `'term'` role)
| Python | Lean | bijection |
|---|---|---|
| `target` (the reference text) | `target : List Char` | per-code-point identity |
| folded target used for lookup | `result : List Char` | identity (post-patch); pre-patch applied `str.lower()` |

## Callee provenance / flag deps

- No UNCHANGED callee is consumed: both modeled values are computed directly from
  the term/reference text by straight-line code. No `opaque`/`axiom` declared.
- The node id passed to `note_object` (`make_id(...)`) is NOT modeled — the patch
  does not change it and it is irrelevant to the case-preservation behavior; the
  modeled output is the two term-derived strings only.
- **Flag dependency:** the lookup site's case fold is gated on the role's
  case-folding flag (a boolean given when the role is constructed). The fix flips
  that flag for the `'term'` role only. G-CONF fuzzes the post-patch
  (flag-off / identity) configuration, which is the modeled behavior.

## ASCII fuzz note
`str.lower()` is full-Unicode in CPython; `Char.toLower` is ASCII-only. Glossary
terms and the F2P test inputs are ASCII. G-CONF fuzzes ASCII strings (mixed
upper/lower/digit/punct), where `str.lower()` == per-char `Char.toLower`.

## G-CONF fuzz seed
`SEED = 7440` (pinned in conformance_check.py).
