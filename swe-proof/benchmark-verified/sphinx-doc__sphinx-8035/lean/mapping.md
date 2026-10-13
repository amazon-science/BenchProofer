# mapping.md — sphinx-doc__sphinx-8035

## Symbol binding (file:line @ base_commit 5e6da19f0e)
Modeled function: the keep/drop decision for a **private** member inside the
member filter `Documenter.filter_members(self, members, want_all)`,
`sphinx/ext/autodoc/__init__.py`. The gold patch changes how the
`:private-members:` option is interpreted: it was previously a boolean flag
(`bool_option`), so when present it documented *all* private members; the patch
makes it name-selective (`members_option`), so it can carry an explicit list of
member names, mirroring `:members:`.

The modeled decision is the non-attribute private branch (`elif want_all and
isprivate:`, `__init__.py:664-687` in the patched file; the pre-patch lines
`__init__.py:668-670`):

```python
# post-patch
elif want_all and isprivate:
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

```python
# pre-patch (base_commit)
elif want_all and isprivate:
    # ignore members whose name starts with _ by default
    keep = self.options.private_members and \
        (has_doc or self.options.undoc_members)
```

Lean modeled function name: `keepPrivateMember` (names the *behavior* — "decide
whether a private member is kept" — at the abstract level; it does not echo a
patched repo symbol).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `privateMembers : PrivateMembersOption` | `self.options.private_members`. Post-patch values: `None` (option absent → `disabled`), `ALL` (the `members_option` sentinel `object()`, produced when the option is given with no argument → `all`), or a `List[str]` of member names (the option given an explicit comma list → `names`). `__init__.py:42` `ALL = object()`, `members_option` `__init__.py:76-80`. |
| `PrivateMembersOption.disabled` | `self.options.private_members is None` |
| `PrivateMembersOption.all` | `self.options.private_members is ALL` |
| `PrivateMembersOption.names ns` | `self.options.private_members` is a list; `ns` is that list of names |
| `memberName : String` | `membername`, the candidate member's name (`__init__.py:592`) |
| `hasDoc : Bool` | `has_doc = bool(doc)` (`__init__.py:615`) |
| `undocMembers : Bool` | `self.options.undoc_members` (truthy) |
| `dropAsInherited : Bool` | `is_filtered_inherited_member(membername)` — the member is present only because it was inherited from an ancestor class outside the documented `:inherited-members:` selection (`__init__.py:650-658`) |
| `result : Bool` | the `keep` value assigned by this branch (`__init__.py`); `True` ⇒ the member is appended to `ret` (documented), `False` ⇒ dropped |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.options.private_members ∈ {None, ALL, list[str]}` | `privateMembers : PrivateMembersOption ∈ {disabled, all, names ns}` |
| `membername : str` (ASCII attribute identifiers) | `memberName : String` |
| `bool(doc)` | `hasDoc : Bool` |
| `bool(self.options.undoc_members)` | `undocMembers : Bool` |
| `is_filtered_inherited_member(membername) : bool` | `dropAsInherited : Bool` |
| `membername in self.options.private_members` | `ns.contains memberName` |
| `keep : bool` | `result : Bool` |

### Post-patch decision (the modeled value)
```
keep =
  (has_doc or undoc_members) and (
     False                              if private_members is None
     True                               if private_members is ALL
     (False if is_filtered_inherited_member(name) else name in private_members)
                                        if private_members is a list
  )
  else False
```
which is exactly `problem_spec_keepPrivateMember` / `implementation_keepPrivateMember`.

### Pre-patch decision (the bug the prepatch encodes)
`keep = private_members and (has_doc or undoc_members)`. `private_members` was a
**bool flag** (`bool_option` always returns `True` when present, else the
`Options` dict returns `None`). So pre-patch: present ⇒ keep EVERY documented
private member regardless of name; absent ⇒ keep none. There is no name
selection and no inherited-member carve-out. The prepatch impl encodes this as
`enabled && (hasDoc || undocMembers)` where `enabled` is true for any non-`None`
selection.

### Discriminating behavior (the F2P test)
`test_private_members` sets `private-members = "_public_function"` (a one-name
list) on module `target.private`, which has a documented private function
`_public_function` (`:meta public:` → still name-starts-with-`_`, treated as
private here via `isprivate = membername.startswith('_')`) and `private_function`
(`:meta private:`).
- Post-patch: `_public_function` ∈ list ⇒ kept; `private_function` ∉ list ⇒
  dropped. Output documents only `_public_function`.
- Pre-patch: the bool flag is truthy ⇒ BOTH documented private members kept,
  so `private_function` would also appear — the test fails.

The two PASS_TO_PASS tests:
- `test_private_field` (no `private-members`): `disabled` ⇒ both dropped
  (`_public_function` dropped as private). Output documents nothing under the
  module body except the module header (matches both pre- and post-patch, since
  pre-patch absent ⇒ falsy ⇒ drop).
- `test_private_field_and_private_members` (`private-members: None` → `ALL`):
  every documented private member kept (matches both pre- and post-patch, since
  pre-patch present-bool ⇒ keep all).

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** Each observation the modeled
  decision uses is a directly-supplied input: the option's shape
  (`is None` / `is ALL` / list, modeled as the `PrivateMembersOption` tag), the
  documented flag `has_doc`, the keep-undocumented flag `undoc_members`, the
  list-membership test (`name in private_members`, modeled as `List.contains`),
  and the inherited-member predicate `is_filtered_inherited_member` (its boolean
  result is taken as the `dropAsInherited` input — the modeled decision does not
  recompute the MRO walk, it consumes the already-computed boolean). All are
  modeled directly ⇒ `axioms = []`, `deep_model_references = []`,
  `axiom_check.py` is a skip stub (G-AX skips).
- **Flag dependency:** this branch fires only under `want_all and isprivate`
  (i.e. the member is private and all members are being scanned). The modeled
  decision is exactly the body of that branch; `want_all`/`isprivate` are the
  branch precondition (the F2P/P2P tests all set `members: None` → ALL, which
  makes `want_all` true). Recorded so G-CONF/G-AX fuzz only the in-branch domain.

## G-LEAK
The solver-visible `problem_statement` publicly names `autodoc`,
`:private-members:`, `:members:`, and the feature ("take arguments, similarly to
how `:members:` currently works"). The spec view names no patched file path, no
gold-diff line, no diff marker, and no patched repo symbol (`merge_members_option`,
`filter_members`, `private_members`, `is_filtered_inherited_member`,
`bool_option`, `members_option` appear NOWHERE in the spec view — neither as
identifiers nor in comments). The docstring states the abstract keep decision
only ("the private members selection takes one of three shapes…"), never the
bug→fix mechanism (bool→list).

## Pinned G-CONF fuzz seed
`8035`.
