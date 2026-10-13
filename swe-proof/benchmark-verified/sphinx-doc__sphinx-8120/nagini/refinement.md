# refinement.md — sphinx-doc__sphinx-8120

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_translation` impl region, the deep precedence fold `resolved`, and
the assembled-list constructors `seq_defines`/`seq_tr`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses an axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The behavioural change — the catalog-source order (`sphinx/application.py`)

Gold hunk (`_init_i18n`, body line 296):
```
- locale_dirs = [None, path.join(package_dir, 'locale')] + list(repo.locale_dirs)
+ locale_dirs = [None]  # type: List[Optional[str]]
+ locale_dirs += list(repo.locale_dirs)
+ locale_dirs += [path.join(package_dir, 'locale')]
```
i.e. the assembled order changes from `[default, bundled] ++ project` to
`[default] ++ project ++ [bundled]`. `locale.init(locale_dirs, language)` then
merges catalogs in that order: the first source found becomes the primary
translator, each subsequent one is appended to the gettext fallback chain
(`translator.add_fallback(trans)`), and `gettext(message)` returns the FIRST
source's entry in chain order — i.e. first-wins precedence (mapping.md §3.1).

| # | model.py impl op (`select_translation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `system_defines/system_tr`, `user_defines/user_tr`, `builtin_defines/builtin_tr`, `message` | the three catalog sources (default `None`; the project `repo.locale_dirs`; the bundled `package_dir/'locale'`) + the looked-up message | R | each source is abstracted to (does it provide a translation for the message?, which text). A `str` localedir path and its `.mo` catalog entry for one message reduce to a `bool`+`int` code; the message and translations are `int` codes under a per-case bijection (mapping.md §2). `repo.locale_dirs` (several project dirs) ↔ the `user_*` parallel lists, in order. |
| A2 | `defines = [system_defines] + user_defines + [builtin_defines]` and the aligned `tr = [system_tr] + user_tr + [builtin_tr]` (`seq_defines`/`seq_tr`) | `locale_dirs = [None] + list(repo.locale_dirs) + [path.join(package_dir,'locale')]` | R + I | the LIST CONSTRUCTION is the heart of the change: default first, project sources next, bundled fallback last. `[a]+b+[c]` ↔ `[None]; += project; += [bundled]` (`+=` on a list is concatenation, I); the source-id payloads abstract to the `defines`/`tr` pair (R). |
| A3 | `res = resolved(ToSeq(defines), ToSeq(tr))` (the backward fold computing the first source, in order, that provides) | `locale.init(locale_dirs, language)` → `translator.gettext(message)` | A-reference | the merged-catalog **first-wins precedence** is modelled DEEPLY (`resolved`, a front-recursive fold over the ordered sources). There is no consumed `gettext` axiom; the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) builds REAL `gettext` translation objects, chains them with the real `add_fallback`, and asserts `merged.gettext(message)` equals `resolved` over the same order (mapping.md §3.1). |
| A4 | `if res == NO_TEXT(): out = message` | `gettext`'s own behaviour: a message no source provides is returned unchanged | A-reference | same deep model: when no source in the chain has an entry, real `gettext` returns the message itself; the model returns `message`. Covered by the same G-AX check (the `[]`, `[{}]`, "nobody provides" boundary cases). |
| A5 | `return out` (an `int` code) | `self.translator, has_translation = locale.init(...)`; the chosen translation text | R | the model returns the selected text's code; the real code stores a translator whose `gettext(message)` yields that text. The F2P test observes the rendered text (`app.translator.gettext('Quick search') == 'QUICK SEARCH'` and `'QUICK SEARCH' in index.html`), i.e. exactly which source's text was selected — the code↔text bijection preserves it (mapping.md §2). |

The discriminating content of the change — the **project sources precede the
bundled fallback** so a project override wins — lives in `seq_defines` /
`seq_tr` (`[default] ++ project ++ [bundled]`) and is pinned by the decisive
precedence postcondition (§D). `model_prepatch.py` reproduces the pre-patch
order (`[default] ++ [bundled] ++ project`) and **fails** the postcondition.

## B. The type-only second hunk — `locale.init` signature

Gold hunk (`sphinx/locale/__init__.py:109`):
```
- def init(locale_dirs: List[str], language: str,
+ def init(locale_dirs: List[Optional[str]], language: str,
```
This is a **pure type-annotation refinement** with NO runtime behaviour change:
`None` was already an element of `locale_dirs` in BOTH the pre- and post-patch
code (the leading `[None]`), so `init`'s loop body (`for dir_ in locale_dirs:
gettext.translation(..., localedir=dir_, ...)`) is byte-identical and behaves
identically. The annotation is widened only so static type-checking accepts the
now-explicitly-typed list. It maps to **no** model operation (there is nothing
behavioural to model); it is recorded here for completeness as an **I/R**
(annotation-only) hunk. The model's abstraction of `init` is entirely in A3/A4.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (none) | `List[str]` → `List[Optional[str]]` on `init`'s `locale_dirs` param | R | annotation-only; the runtime list already contained `None` pre-patch, so no behaviour changes and there is no model op. Type carrier widening, observationally identity. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the catalog-source **order** that drives the first-wins precedence
— is modelled **deeply** (`seq_defines`/`seq_tr` assemble the order; `resolved`
spells out first-wins precedence; both verified), never hidden behind a
consumed axiom. The merged-catalog precedence is an **A-reference** validated ==
the real `gettext` merge/lookup by G-AX. There is **no consumed `@ContractOnly`
axiom**: the per-source catalog facts (`*_defines`/`*_tr`) are plain input data
(whether a real localedir's `.mo` has an entry for the message, and what it is),
exactly as the real code consumes them.

## D. G-DIFF — the prepatch fails on the right clause

`model_prepatch.py` keeps the spec byte-identical (axioms / pure /
pre-conditions / post-conditions regions hash-identical — confirmed) and
reverts the `select_translation` impl to the pre-patch assembly: `defines =
[system_defines] + [builtin_defines] + user_defines` (the bundled fallback
AHEAD of the project sources). It **fails** verification on the postcondition

  `Implies(resolved_assembled(...) != NO_TEXT(), Result() == resolved_assembled(...))`

(and the decisive precedence clause `Result() == user_tr[first_provider(...)]`),
because `resolved_assembled` is defined over the FIXED order `[default] ++
project ++ [bundled]`, while the prepatch computes resolution over `[default] ++
[bundled] ++ project`. When the bundled source and a project source both provide
the message, the prepatch returns the **bundled** text where the spec demands
the **project** text. This is exactly the F2P-tested behaviour:
`app.translator.gettext('Quick search')` must be the project override
`'QUICK SEARCH'`, not the bundled value (`test_customize_system_message`).

## E. verify(model) ⇒ resolved

`select_translation` verifies only if its output equals the first-wins resolution
over the assembled order `[default] ++ project ++ [bundled]` (A2/A3/A4), and in
particular only if a project-supplied translation is selected over the bundled
fallback for the same message (the decisive precedence clause, §D). By R (each
localedir/`.mo` ↔ a `defines`/`tr` pair; the text↔code bijection; `+=` ↔ `+`)
and the A-reference (G-AX: `resolved` == the real `gettext` merge/lookup), the
verified function equals the gold-patched `_init_i18n` list construction +
`locale.init`'s merged-catalog lookup on the tested inputs. The F2P test
`test_customize_system_message` observes precisely this: a project
`sphinx.po`/`sphinx.mo` providing `'Quick search' → 'QUICK SEARCH'` wins over the
bundled `de` catalog, and that text appears in the built HTML. Therefore an impl
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the G-AX-validated deep model — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model
soundness (G-AX) and refinement fidelity (this document, G-EQ).
