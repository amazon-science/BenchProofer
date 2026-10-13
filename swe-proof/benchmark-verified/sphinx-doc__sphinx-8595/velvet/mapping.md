# mapping.md — sphinx-doc__sphinx-8595

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b19bce971e82f2497d67fdacdeca8db08ae0ba56`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `sphinx/ext/autodoc/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectDocumentedMembers (exposeAll, published, roster, requested)` | `ModuleDocumenter.get_object_members(self, want_all)` — `sphinx/ext/autodoc/__init__.py:1074` (changed guard line 1077) | the modeled changed function |
| `exposeAll : Bool` | the `want_all` parameter | true ⇒ full implicit-roster mode; false ⇒ explicit named-subset mode |
| `published : Option (List Int)` | `self.__all__` (`Optional[Sequence[str]]`, initialized `None` at `__init__.py:992`, set from the module's published-name attribute at `__init__.py:1020`) | the OPTIONAL published-name list: `None ↔ none`, a list ↔ `some [...]`. Presence (not truthiness) is the discriminator the fix restores. |
| `roster : List Int` | `members = self.get_module_members()` (`__init__.py:1075`), i.e. `list(members.values())` names | the candidate roster of documentable entries, in dict-insertion order |
| `requested : List Int` | `self.options.members or []` (`__init__.py:1090`) | the explicitly named subset (only read when `exposeAll = false`) |
| `MemberOut { name, skipped }` | an `ObjectMember` (`__init__.py:260`) as observed: its `__name__` and its `skipped` flag (`member.skipped = True`, `__init__.py:1085`) | one returned entry |
| `MemberResult { checkOrigin, entries }` | the `Tuple[bool, ObjectMembers]` return | `checkOrigin ↔` the first element (the caller-side origin-filter flag — `True` = "additionally filter implicit entries by origin"); `entries ↔` `list(members.values())` / `ret` |

The pre-patch defect the change removes (refinement audit only, NOT in the
consumer spec view): the guard `if not self.__all__:` (`__init__.py:1077`), whose
truthiness test treats a present-but-empty published-name list the same as an
absent one. The fix is the presence test `if self.__all__ is None:`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an entry name (`str`, a dict key / `member.__name__`) | `Int` | each distinct name ↔ a distinct `Int` identifier (names are compared only by equality / membership; identity of the carrier is all that is observed). G-CONF instantiates the `Int`s as distinct strings. |
| `self.__all__ : Optional[Sequence[str]]` | `Option (List Int)` | `None ↔ none`; a sequence `[a,b,…] ↔ some [â,b̂,…]`. **Crucially `[] ↔ some []`, NOT `none`** — "absent" and "present but empty" are genuinely different inputs (the bug's discriminator). |
| `members` dict / `list(members.values())` | `roster : List Int` | dict-insertion order ↔ list order; `len` ↔ `.length`; `name in members` ↔ `n ∈ roster`. |
| `self.options.members or []` | `requested : List Int` | the explicit subset; `None`/`[]` both ↔ `[]`. |
| an `ObjectMember` | `MemberOut { name, skipped }` | only the two observed fields are modeled; `obj`, `docstring`, `class_` are unmodeled R-identities (not observed by the F2P documented-set assertion). `member.__name__ ↔ name`; `member.skipped ↔ skipped`. |
| the `(bool, list)` return | `MemberResult { checkOrigin, entries }` | first element ↔ `checkOrigin`; the returned `ObjectMembers` ↔ `entries` (name+skipped projection). |

Lean indexing/membership over `List Int` is total and sound; the carrier is
`List Int` because the operation observes names only by equality/membership.

## 3. Callee provenance

There are **no axiomatized callees** (no `axiom`, no `:|` stub). The roster
`members` is produced by the unchanged callee `self.get_module_members()`; per
the §2 cheatsheet for an unchanged callee whose OUTPUT is consumed as data, it is
modeled as the **input carrier `roster`** (not axiomatized). The conformance
check feeds the SAME roster to the real patched `get_object_members`, so
`get_module_members` is bridged as the input — exactly the pattern of the input
classification carriers in the sister bundles. The decision logic itself (the
presence test + per-entry skip marking + explicit-subset filter) is modeled
**deeply** and is therefore an **I/R leg**, refuted by G-CONF.

No flag-dependent callees: the only flag is the modeled parameter `exposeAll`
(`want_all`), which the spec branches on explicitly.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8595`** so the
consumer-side verdict is reproducible. Its SHADOW transliterates
`markAllExposed` / `markByPublished` / `selectRequested` / `objectMembers`
(all R/I-tagged ops) to Python; the ORACLE is the real, gold-patched
`ModuleDocumenter.get_object_members` driven on a duck-typed documenter whose
`get_module_members`, `__all__`, and `options.members` are configured per case.

## 5. G-AX

Skipped: the bundle has no axioms (no `axiom_check.py`). `meta.json
gates.G-AX.status = "skip"`.
