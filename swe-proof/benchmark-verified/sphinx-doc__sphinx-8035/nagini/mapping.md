# mapping.md — sphinx-doc__sphinx-8035

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5e6da19f0e44a0ae83944fb6ce18f18f781e1a6e`, states the type
abstraction, and documents the provenance of each modeled behaviour. There are
NO `@ContractOnly` axioms in this bundle: both modeled behaviours are pure
boolean / sequence logic, spelled out deeply, and validated against the REAL
post-patch code by `axiom_check.py` (G-AX).

Repo file under change: `sphinx/ext/autodoc/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `keep_private_member(mode, names, membername, has_doc, undoc_members, filtered_inherited)` | the private-member keep decision inside `Documenter.filter_members` — the `elif want_all and isprivate:` branch, `sphinx/ext/autodoc/__init__.py:657-660` (pre-patch); the post-patch three-state branch is the gold patch's second hunk | the modeled changed function (private-member retention decision) |
| `keep_private(...)` *(pure)* | the same branch, expressed as a pure decision | pure spec: the three-state keep rule |
| `documentable(has_doc, undoc_members)` *(pure)* | `has_doc or self.options.undoc_members` (`__init__.py:660`, `:645`, `:666`) | pure spec: usual documentability test |
| `merge_selector_names(members_is_all, members, extra)` | the new merge helper introduced by the gold patch (the `for key in {'private-members','special-members'}: ... members.append(member)` body), replacing the call to `merge_special_members_option` in `ModuleDocumenter.__init__` (`__init__.py:868`) and `ClassDocumenter.__init__` (`__init__.py:1290`) | the modeled added function (merge of `*-members` selectors into the member list) |
| `merged_at(orig, extra, i)` *(pure)* | the `if member not in members:` guard of the merge loop | pure spec: append-if-absent membership predicate |

The pre-patch repo facts the change replaces (for the refinement audit, not
referenced from the consumer spec view):
- `'private-members': bool_option` in `ModuleDocumenter.option_spec`
  (`__init__.py:862`) and `ClassDocumenter.option_spec` (`__init__.py:1282`):
  the option was a boolean, so `self.options.private_members` was `True`/`False`.
  The gold patch makes it `members_option`, so the value is now `None` / the
  `ALL` sentinel / a `List[str]`.
- the pre-patch keep line `keep = self.options.private_members and (has_doc or
  self.options.undoc_members)` (`__init__.py:659-660`) — a boolean-and collapse
  that keeps EVERY documentable private member whenever the option is truthy.
- `merge_special_members_option` (`__init__.py:126`) merged only special-members;
  the gold patch deprecates it and adds `merge_members_option`, which also
  merges private-members.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| member name (`str`) | `int` identity token | only equality / list-membership of names is observed (`membername in self.options.private_members`, `member not in members`); a `str` name ↔ a distinct `int` token, equality-preserving. Nagini bans `str` indexing, so a name is an opaque token. |
| `self.options.private_members` ∈ {`None`, `ALL`, `List[str]`} | `mode: int` ∈ {0,1,2} + `names: List[int]` payload | `None` ↔ `mode==0`; the `ALL` object sentinel ↔ `mode==1`; a `List[str]` ↔ `mode==2` with `names` the token list. This is the faithful refinement of the option's three states; `axiom_check.py` builds the states through the REAL `members_option` converter and asserts the equivalence. |
| `self.options.members is ALL` (the principal members selector) | `members_is_all: bool` | the `members` option's all-form (its own `ALL` sentinel) ↔ `members_is_all==True`. |
| `self.options.private_members` list, `options['members']` list, `options[key]` list (`str` lists) | `List[int]` of name tokens; specification over `PSeq[int]` via `ToSeq` | list `+`/`append`/`in`/`len`/`take` mirror `str`-list `+`/`append`/`in`/`len`/slice. |
| `has_doc`, `self.options.undoc_members`, `is_filtered_inherited_member(membername)` | `has_doc`, `undoc_members`, `filtered_inherited` booleans | the surrounding context computes these; they are the decision's inputs and are abstracted to plain booleans (their internals are unchanged by the patch). |

`str` indexing/iteration is banned in Nagini, so names are `int` tokens and
name-lists are `List[int]`; the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Deep-model references (A-reference — checked by G-AX / axiom_check.py)

There are no consumed axioms. The two modeled behaviours are validated equal
to the real post-patch code:

### 3.1 `keep_private` deep model ↔ post-patch `filter_members` private branch (A-reference)
**Reference:** the post-patch `elif want_all and isprivate:` branch of
`Documenter.filter_members`:
```python
if has_doc or self.options.undoc_members:
    if self.options.private_members is None:
        keep = False
    elif self.options.private_members is ALL:
        keep = True
    elif is_filtered_inherited_member(membername):
        keep = False
    else:
        keep = membername in self.options.private_members
else:
    keep = False
```
`keep_private` is exactly this, with the option's three states refined to the
`mode`/`names` carrier (§2). Note the inherited-member filter applies ONLY to
the explicit-list state, NOT to the all-form (mode 1 returns `True` for any
documentable member); this asymmetry is transcribed faithfully and was
caught/confirmed by `axiom_check.py`. The discriminating content: an explicit
list keeps a documentable, non-filtered member iff its OWN name is in the list
(`membername in self.options.private_members`). The pre-patch boolean-and kept
EVERY documentable private member whenever the option was truthy — which a
non-empty list always is. **Soundness check (G-AX):** `axiom_check.py` builds
the three option states through the REAL `members_option` converter and asserts
`keep_private` equals the verbatim gold decision over every combination of
option state × member name × `has_doc` × `undoc_members` × `filtered_inherited`.

### 3.2 `merge_selector_names` deep model ↔ the new `merge_members_option` (A-reference)
**Reference:** the merge helper the gold patch adds:
```python
def merge_members_option(options):
    if options.get('members') is ALL:
        return                       # no-op when members: ALL
    members = options.setdefault('members', [])
    for key in {'private-members', 'special-members'}:
        if key in options and options[key] is not ALL:
            for member in options[key]:
                if member not in members:
                    members.append(member)
```
`merge_selector_names` models one supplementary selector (`extra`) being merged
into `members`: a no-op when `members_is_all`, else append-if-absent preserving
order and avoiding duplicates. **Soundness check (G-AX):** `axiom_check.py`
imports the REAL `sphinx.ext.autodoc.merge_members_option` and asserts the deep
model equals its observed effect on the `members` list over 5000 randomized
inputs (both branches), with option dicts constructed exactly as the directive
builds them.

**Why the merge has no separate failing `model_prepatch`:** the F2P test
(`test_private_members`) supplies `members: ALL`, for which the merge returns
early (a no-op), so it does not affect the tested observation. The merge is
modeled for faithfulness of the multi-site change, and its soundness is audited
by G-AX (real `merge_members_option`); the tested, differentiating behaviour is
the keep decision (§3.1), which `model_prepatch.py` exercises.

`axiom_check.py` imports only the standard library plus `sphinx.ext.autodoc`
(the very module the gold patch changes); nothing test-/repo-private. Exit 0
iff every obligation holds.
