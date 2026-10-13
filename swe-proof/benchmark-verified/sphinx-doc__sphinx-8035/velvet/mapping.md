# mapping.md — sphinx-doc__sphinx-8035

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5e6da19f0e44a0ae83944fb6ce18f18f781e1a6e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), gives the
provenance of each axiom / deep-model reference, and pins the G-CONF fuzz seed.

Repo file under change: `sphinx/ext/autodoc/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectMembers (members) (sel) (showUndocumented)` | the member-keep loop of `Documenter.filter_members` — `sphinx/ext/autodoc/__init__.py:559` (the `for (membername, member) in members:` body, lines 596–688; the kept list is `ret`) | the modeled changed function: which members survive filtering, in input order |
| `memberShown (sel) (showUndocumented) (m)` | the per-member `keep = …` decision inside `filter_members`, restricted to the two branches the modeled scenario reaches (§2): the `want_all and isprivate` branch (post-patch lines 664–678) and the `else` documented branch (lines 681–687) | pure spec: the keep predicate for one member |
| `selKeeps (sel) (name)` | the post-patch tri-state test on `self.options.private_members` — `None` → `False`, `ALL` → `True`, list → `membername in self.options.private_members` (post-patch lines 668–678) | pure spec: does the selection surface this restricted member |
| `shownMembers (sel) (showUndocumented) (ms)` *(deep model — I-tagged, front-recursive fold)* | the accumulation `ret.append((membername, member, isattr))` over the member loop (`filter_members`, line 686) | pure spec: the kept sublist, in input order |
| `Sel` (`none`/`all`/`only names`) *(R-refinement of an A-reference value)* | the value of `options['private-members']` after the patch re-routes its parser to `members_option` — `members_option` at `sphinx/ext/autodoc/__init__.py:76` | the tri-state the option parses to |
| `Member.name` | `membername` (loop variable in `filter_members`) | a member's identifier |
| `Member.isRestricted` | `isprivate` (`filter_members`, lines 617–625, from `extract_metadata` / `name.startswith('_')`) | whether the member is visibility-restricted (private) |
| `Member.hasDoc` | `has_doc` (`filter_members`, line 615, `bool(doc)` from `getdoc`) | whether the member carries documentation |
| `showUndocumented` | `self.options.undoc_members` (truthy/falsy) | whether undocumented members are requested |

The pre-patch repo facts the change removes (refinement audit only, NOT in the
consumer spec view): `'private-members': bool_option` in `ModuleDocumenter`
(`__init__.py:890`) and `ClassDocumenter` (`__init__.py:1310`) option_specs, and
the boolean keep-decision `keep = self.options.private_members and (has_doc or
self.options.undoc_members)` (`__init__.py:665–666`), which surfaces ALL private
members whenever the option is truthy (a non-empty list is truthy → the bug).

## 2. Modeled scenario (scoping — read before the type table)

The F2P test (`tests/test_ext_autodoc_private_members.py::test_private_members`)
and the issue both exercise the **`want_all` case** — `:members:` given bare
(`members_option(None) = ALL`), so `want_all = (self.options.members is ALL)` is
true and the private branch of `filter_members` is reached. The modeled function
covers exactly this scenario, over **function members** (not data attributes:
the `(namespace, membername) in attr_docs` branch and `INSTANCEATTR` are not on
the F2P path — `target.private` defines two module-level functions), with no
`:exclude-members:`, no `:special-members:` dunder handling, and `objtype =
module` so `is_filtered_inherited_member` is constantly `False` (it returns
`False` unless `self.object` is a class, `__init__.py:574–582`). The two branches
the scenario reaches are modeled exactly (§3): a restricted (private) member and
a non-restricted member, both routed through `memberShown`. Inputs outside this
scenario are not claimed and are excluded from the G-CONF/G-AX fuzz domain
(recorded as under-coverage, plan §4.1).

`selectMembers` models the keep-loop as a pure list filter `List Member →
List Member`; the `autodoc-skip-member` event hook (which can override `keep`
afterwards, lines 689–701) is inactive in the test app and is excluded from the
modeled scenario (no listener connected), matching the F2P configuration.

## 3. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§5) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a member name `membername : str` | `String` (via `Member.name`) | identity on character content; `membername in lst` ↔ `lst.contains name` (whole-string `==`) |
| `has_doc : bool` (`bool(getdoc(member))`) | `Member.hasDoc : Bool` | direct boolean identity |
| `isprivate : bool` | `Member.isRestricted : Bool` | direct boolean identity (computed upstream by `extract_metadata`/`startswith('_')` — unchanged callees, §4) |
| `self.options.undoc_members` (truthy/falsy) | `showUndocumented : Bool` | `bool(undoc_members)` ↔ the `Bool` |
| `self.options.private_members` ∈ {`None`, `ALL`, `list[str]`} | `Sel` | `None ↔ Sel.none`; `ALL ↔ Sel.all`; `["a","b"] ↔ Sel.only ["a","b"]` |
| the member list (in source order) | `List Member` | `[(name, member), …]` ↔ `List Member`; `ret` (kept sublist) ↔ the `out` list; order preserved |

`String` `BEq` is decidable and total; `List.contains` over `String` mirrors
Python's `membername in self.options.private_members` exactly (both are
membership by value equality over the parsed name list).

## 4. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

No module-level `axiom` is consumed by the proof; the keep-decision is modeled
deeply (§3). The unchanged callees that feed the modeled inputs are
A-references, validated == their real callee by `axiom_check.py`.

### 4.1 `Sel` ↔ `members_option` (A-reference)
**Callee:** `members_option(arg)` (`sphinx/ext/autodoc/__init__.py:76`,
**unchanged** by the patch — the patch only re-routes the `:private-members:`
option_spec entry from `bool_option` to this already-existing parser):

```python
def members_option(arg: Any) -> Union[object, List[str]]:
    if arg is None or arg is True:
        return ALL
    return [x.strip() for x in arg.split(',') if x.strip()]
```

`Sel` is the value domain of `members_option`'s result together with option
absence: `arg=None/True → ALL ↔ Sel.all`; `arg="a, b" → ["a","b"] ↔
Sel.only [...]`; option absent → `self.options.private_members is None ↔
Sel.none`. The spec consumes only the membership test `name in names`, so the
A-reference obligation G-AX checks is that `members_option`'s comma-split list is
the set the keep-decision tests against. `axiom_check.py` validates
`members_option == Sel` (the tri-state, incl. the comma-split list) over boundary
+ fuzz arguments.

### 4.2 `isRestricted` / `hasDoc` ↔ `extract_metadata` / `getdoc` (A-reference, abstracted)
**Callees:** `extract_metadata` (`sphinx/util/docstrings.py:24`) and `getdoc`
(`sphinx/util/inspect.py:809`), both **unchanged**. They compute `isprivate`
(`:meta private:`/`:meta public:`/`_`-prefix) and `has_doc` (`bool(doc)`)
**before** the keep-decision; the patch does not touch them. The model abstracts
their results into the `Member.isRestricted` / `Member.hasDoc` fields (R), so
they are inputs to the modeled function, not part of the changed op. G-AX
confirms `extract_metadata`/`startswith` classifies the F2P module's two members
as `_public_function → :meta public: → isRestricted False` and `private_function
→ :meta private: → isRestricted True` — the classification the discriminator
depends on (the underscore-prefixed name is overridden public; the unprefixed
name is overridden private).

## 5. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8035`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `memberShown`/`selKeeps`/`shownMembers` (the I-tagged keep-decision
fold) to Python and bridges I/O via §3; the oracle is the **real patched
`Documenter.filter_members`** keep-decision (A-tagged callees `members_option`,
`extract_metadata`, `getdoc` left as the real repo callees / their faithful
restatement on synthetic members), driven on synthetic function members in the
modeled scenario (§2).
