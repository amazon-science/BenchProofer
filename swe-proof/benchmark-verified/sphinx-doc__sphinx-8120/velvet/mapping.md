# mapping.md — sphinx-doc__sphinx-8120

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 795747bdb6b8fb7d717d5bbfc2c3316869e66a73`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference (the search-order resolver).

Repo files under change: `sphinx/application.py`, `sphinx/locale/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildLocaleDirs (repoDirs) (sysNone) (packageLocale)` | the `locale_dirs` assembly inside `_init_i18n` — `sphinx/application.py:296` (post-patch :296-298) | the modeled changed function: builds the ordered search list |
| `repoDirs : List Dir` | `list(repo.locale_dirs)` (`sphinx/application.py:296`), the user-provided localization directories from `CatalogRepository(self.srcdir, self.config.locale_dirs, …)` | the user/source-tree entries |
| `sysNone : Dir` | the `None` first element (`sphinx/application.py:296`), the system-default catalog path | the system-default search entry (sentinel) |
| `packageLocale : Dir` | `path.join(package_dir, 'locale')` (`sphinx/application.py:296`) | the bundled (shipped-with-Sphinx) localization directory |
| `resolve` *(deep model — A-reference)* | `sphinx.locale.init` — `sphinx/locale/__init__.py:109` (the `for dir_ in locale_dirs:` loop, lines 121-130, using `gettext.translation` + `add_fallback`) | the search-order message-catalog loader: first matching dir wins, later dirs are fallbacks; validated `resolve == init`'s precedence by axiom_check.py (G-AX), NOT consumed as an axiom |

The `List[str] → List[Optional[str]]` change to `init`'s signature
(`sphinx/locale/__init__.py:109`) and the matching `Optional` import are pure
type-annotation edits: they alter no runtime value (`None` was already passed as
the first element pre-patch) and are observationally the identity (refinement.md
§C). The modeled behavioral change is the **order** of `locale_dirs`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a localization directory path (`str`), or the `None` system-default sentinel | `Dir` (= `String`) | a directory path `p` (Python `str`) ↔ the Lean `String` `p`; the `None` sentinel ↔ a distinguished Lean `String` that defines no message (`sysNone`, `cat sysNone _ = none` in the resolver model — see §3) |
| the `locale_dirs` list (`List[Optional[str]]`) | `List Dir` | Python list ↔ Lean `List`; `[a, b] + c` ↔ `[a, b] ++ c`; element order preserved exactly (order = precedence, the modeled behavior) |
| `repo.locale_dirs` (an iterable of user dirs) | `repoDirs : List Dir` | `list(repo.locale_dirs)` ↔ the Lean list, order preserved |
| the resolved translation for a message id | `Option String` | a message id `k` resolves to its translation `v` (`some v`) or to no override (`none`, i.e. fall back to the built-in source string) |

Lean `List` is total/ordered; no workaround needed. The carrier is `List Dir`
because the operation is purely the assembly and ordering of a directory list.

## 3. Callee provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolve` deep model ↔ `sphinx.locale.init` search order (A-reference)
**Callee:** `sphinx.locale.init(locale_dirs, language, catalog, namespace)`
(`sphinx/locale/__init__.py:109`). The function under change
(`_init_i18n`) calls `init` with the assembled list; `init` is **unchanged** in
behavior (only its parameter type annotation changed). Its message-lookup
semantics are modeled deeply by `resolve` in the `pure` region; there is **no
consumed axiom**. The relevant body:

```python
for dir_ in locale_dirs:
    try:
        trans = gettext.translation(catalog, localedir=dir_, languages=languages)
        if translator is None:
            translator = trans          # FIRST hit becomes the primary
        else:
            translator.add_fallback(trans)   # later hits are fallbacks only
    except Exception:
        pass
```

`NullTranslations.gettext`/`add_fallback` semantics: a lookup consults the
primary catalog first and only descends the fallback chain when the primary does
not define the message. Therefore the **first directory in `locale_dirs` that
defines a message supplies it**, and later directories can only fill in messages
no earlier directory defined — exactly `resolve cat (d :: ds) k =
(cat d k).orElse (fun _ => resolve cat ds k)`. The post-patch order puts the
user (`repoDirs`) entries before the bundled `packageLocale` entry, so a user
override of a built-in message wins (the abstract property
`resolve_user_precedence`).

**Soundness check (G-AX):** `axiom_check.py` builds, in temporary directories,
real gettext `.mo` catalogs (via Python's `msgfmt`-equivalent struct writer),
constructs the list in the post-patch order, calls the **real**
`sphinx.locale.init`, and asserts the resulting translator's `gettext`
observations match `resolve` over boundary + fuzz configurations (user-overrides,
package-only, system-only, conflicting definitions). Exit 0 iff the deep model
matches the real loader's precedence.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8120`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`buildLocaleDirs` (R/I-tagged list-assembly ops) to Python and compares the
produced ordered list against `patch.diff`'s behaviour (the order
`_init_i18n` assembles post-patch). The A-tagged callee `resolve`
(`sphinx.locale.init`) is NOT substituted by its model here; it is out of
G-CONF's R/I scope and validated by G-AX.
