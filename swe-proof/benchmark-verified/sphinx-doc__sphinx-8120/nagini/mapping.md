# mapping.md — sphinx-doc__sphinx-8120

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 795747bdb6b8fb7d717d5bbfc2c3316869e66a73`, states the type
abstraction, and gives the provenance of the one A-reference deep model (the
merged-catalog first-wins precedence) checked by G-AX.

Repo files under change: `sphinx/application.py` (the behavioural hunk) and
`sphinx/locale/__init__.py` (a type-annotation-only hunk).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_translation(...)` | `Sphinx._init_i18n` — `sphinx/application.py:279` (changed body line 296) | the modeled changed behaviour: assemble the ordered catalog-source list and resolve the message catalog from it |
| `seq_defines` / `seq_tr` | the assembled `locale_dirs` list — `sphinx/application.py:296` (post-patch: `[None] + list(repo.locale_dirs) + [path.join(package_dir,'locale')]`) | pure spec: the ordered source list, default ++ project ++ bundled |
| `resolved` *(deep model — A-reference)* | `sphinx.locale.init` + `gettext` merge/lookup — `sphinx/locale/__init__.py:109` (loop body line 131-137) and CPython `Lib/gettext.py` (`NullTranslations.add_fallback`, `GNUTranslations.gettext`) | pure spec: first-wins precedence of the merged catalog; validated `resolved == real gettext merge/lookup` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `some_provides` / `first_provider` | the existence / index of the first source (in order) whose catalog has an entry for the message | pure spec: helpers for the decisive precedence clause |
| `resolved_assembled` | `resolved` over the fully assembled order | pure spec: wrapper folding in the default and bundled endpoints |
| `NO_TEXT()` (0) | gettext's "no entry found anywhere" outcome (returns the message itself) | pure spec: the untranslated sentinel |
| `message` / `*_tr` (>=1) | the source message string / the translation strings | the looked-up message and the per-source translations, as distinct int codes |
| `*_defines` (bool) | whether a given localedir's `.mo` for the `'sphinx'` catalog has an entry for the message | per-source "provides?" fact |

The pre-patch repo construction the change reorders (for the refinement audit,
not referenced from the consumer spec view): `locale_dirs = [None,
path.join(package_dir, 'locale')] + list(repo.locale_dirs)`
(`sphinx/application.py:296`, pre-patch) — bundled (`package_dir/'locale'`)
AHEAD of the project (`repo.locale_dirs`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a catalog source = a localedir path (`str` or `None`) plus its compiled `.mo` catalog | a pair `(defines: bool, tr: int)` per source, for the one looked-up message | `defines` ↔ "the source's `.mo` for the `'sphinx'` catalog has an entry for this message"; `tr` ↔ the int code of that entry's text (a skipped/absent source ⇒ `defines=False`) |
| `repo.locale_dirs` (the project's several localedirs, in order) | parallel lists `user_defines: List[bool]`, `user_tr: List[int]` (aligned, in order) | the i-th project dir ↔ index i |
| the bundled `path.join(package_dir, 'locale')` source | `builtin_defines: bool`, `builtin_tr: int` | the single bundled fallback source |
| the leading `None` (system default localedir) source | `system_defines: bool`, `system_tr: int` | for the `'sphinx'` catalog this provides nothing (`system_defines=False`); kept first to mirror `[None]` exactly |
| `list` concatenation / `+=` building `locale_dirs` | list `+` building `defines`/`tr` | `[a] + b + [c]` ↔ `[a]; += b; += [c]` (observationally identical; `+=` on a list IS concatenation) |
| a message / translation `str` | a distinct `int` code (>= 1 for a real text; 0 == NO_TEXT) | a per-case bijection over the finite set of texts present; the F2P test observes WHICH source's text is selected, which the bijection preserves exactly (axiom_check.py builds the bijection explicitly) |

The spec is about WHICH source's text is selected (catalog precedence), not
about the characters of any translation, so each text is modelled as an opaque
distinct identity (`int` code); `str` indexing is never needed and the Nagini
`str` ban does not bite.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolved` deep model ↔ the real gettext merge/lookup (A-reference)
**Callee:** the unchanged `sphinx.locale.init` merge loop + CPython `gettext`.
`init` (`sphinx/locale/__init__.py:109`) iterates `locale_dirs` in order:

```python
translator = None
for dir_ in locale_dirs:
    try:
        trans = gettext.translation(catalog, localedir=dir_, languages=languages)
        if translator is None:
            translator = trans            # first found -> primary
        else:
            translator.add_fallback(trans)  # rest -> fallback chain, in order
    except Exception:
        pass                              # dir without a catalog is skipped
```

and the resulting `translator.gettext(message)` (CPython `Lib/gettext.py`):

```python
class NullTranslations:
    def add_fallback(self, fallback):
        if self._fallback: self._fallback.add_fallback(fallback)
        else: self._fallback = fallback          # append to END of chain

class GNUTranslations(NullTranslations):
    def gettext(self, message):
        tmsg = self._catalog.get(message, missing)
        if tmsg is not missing: return tmsg      # this source's entry wins
        if self._fallback: return self._fallback.gettext(message)  # else descend
        return message                           # nobody has it -> untranslated
```

Because `add_fallback` appends to the end of the chain and `gettext` returns the
primary's entry if present and otherwise descends the chain in order, the
resolved translation of a message is the entry from the **first source, in the
order the sources were added, that has one** — i.e. exactly `resolved`. The
order the sources are added is the order of `locale_dirs`, which the gold patch
sets to `[default] ++ project ++ [bundled]` (project ahead of bundled). Docs:
https://docs.python.org/3/library/gettext.html#gettext.NullTranslations.add_fallback .

This change is sound only because gettext's precedence is **first-in-chain-wins**
(not last); a source that comes earlier in `locale_dirs` overrides later ones
for any message it provides. (No flag dependency: `gettext.translation`'s merge
and `*.gettext` lookup use no configurable mode here.)

**Soundness check (G-AX):** `axiom_check.py` builds REAL `gettext` translation
objects (in-memory catalogs; the merge/lookup logic under test is identical to
the `.mo`-backed path — only the catalog population differs), chains them with
the genuine `NullTranslations.add_fallback`, and asserts the real
`merged.gettext(message)` equals `resolved` over the same ordered sources on 14
boundary orderings + 20 000 randomized fuzz orderings (varying source count,
skipped sources, gap sources, and which sources provide the message), plus the
decisive sphinx scenario: order `[None] ++ project ++ bundled` with the project
overriding a message the bundled source also provides selects the PROJECT text
(`'QUICK SEARCH'`), while the pre-patch order `[None] ++ bundled ++ project`
selects the bundled text (the bug). Imports only the standard-library `gettext`
module — the very module the changed code merges/looks up through. Exit 0 iff
sound.

## 4. No consumed axioms
The `axioms` region of model.py is empty (a documented no-op). The merged-catalog
precedence is modelled deeply (`resolved`) and is an **A-reference** (§3.1), not
a consumed `@ContractOnly`. The per-source catalog facts are plain inputs. The
`sphinx/locale/__init__.py` hunk is a type-annotation-only widening
(`List[str]` → `List[Optional[str]]`) with no runtime effect (`None` was already
in the list pre-patch) and therefore no model operation.
