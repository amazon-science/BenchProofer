# mapping.md — sphinx-doc__sphinx-8593

## Symbol binding (file:line @ base_commit 07983a5a8704ad91ae855218ecbda1c8598200ca)

The modeled function is the routine that collects the documented entries of a
module (the `want_all` / explicit-name paths), the function the gold patch
rewrites.

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_collectModuleEntries` / `problem_spec_collectModuleEntries` / `correct_collectModuleEntries` | `ModuleDocumenter.get_object_members(self, want_all)` together with the new helper `ModuleDocumenter.get_module_members(self)` that the gold patch introduces | `sphinx/ext/autodoc/__init__.py` `get_object_members` @ base `1046-1074`; gold adds `get_module_members` and rewrites `get_object_members` at `1046-1099` post-patch |
| `dirNames : List String` | `dir(self.object)` — the names visible on the target module | `__init__.py` post-patch `get_module_members`: `for name in dir(self.object)`; @ base the free function `importer.get_module_members`: `for name in dir(module)` (`importer.py:145`) |
| `annotNames : List String` | `inspect.getannotations(self.object)` — annotation-only member names (`attr: int` with no value) | post-patch `get_module_members`: `for name in inspect.getannotations(self.object)`; @ base `importer.py:154` `getannotations(module)` |
| `val : String → String` | `safe_getattr(self.object, name, None)` — the member's value, rendered. (Has default `None`, so it does NOT raise; the `except AttributeError: continue` is effectively dead for the module path.) | post-patch `get_module_members`: `value = safe_getattr(self.object, name, None)` |
| `doc : String → String` | the documentation comment attached to the name: `"\n".join(attr_docs.get(('', name), []))` where `attr_docs = self.analyzer.attr_docs` (empty when there is no analyzer) | post-patch `get_module_members`: `docstring = attr_docs.get(('', name), [])`, `ObjectMember(name, value, docstring="\n".join(docstring))` |
| `INSTANCEATTR` sentinel (annotation-only value) | `INSTANCEATTR` | modeled as `Member.value = none` |
| `wantAll : Bool` | `want_all` parameter | `get_object_members(self, want_all)` |
| `allNames : Option (List String)` | `self.__all__` (set by `import_object`; `None` when absent / `__all__` raised) | `__init__.py:1019-1031`; `not self.__all__` ⇔ `None` or empty list |
| `memberlist : List String` | `self.options.members or []` (the explicit `:members:` name list) | post-patch `get_object_members` else-branch: `memberlist = self.options.members or []` |
| `Member` (pure structure) | `ObjectMember(name, obj, docstring=…, skipped=…)` — only the fields the spec observes: name, value, attached doc comment, skipped flag | `__init__.py:262-283` (`class ObjectMember`) |
| result `Bool × List Member` | `Tuple[bool, ObjectMembers]` returned by `get_object_members` | post-patch returns `(True, list(members.values()))` / `(False, list(members.values()))` / `(False, ret)` |

### What the patch changes (base_commit)

At base commit, `ModuleDocumenter.get_object_members` collects members through the
free function `importer.get_module_members(self.object)`, which returns plain
`(name, value)` tuples — **no documentation comment is attached**:

```python
def get_object_members(self, want_all):
    if want_all:
        members = get_module_members(self.object)        # List[Tuple[str, Any]]
        if not self.__all__:
            return True, members                          # raw tuples, no doc
        else:
            ret = []
            for name, value in members:
                if name in self.__all__:
                    ret.append(ObjectMember(name, value)) # docstring defaults None
                else:
                    ret.append(ObjectMember(name, value, skipped=True))
            return False, ret
    else:
        memberlist = self.options.members or []
        ret = []
        for name in memberlist:
            try:
                value = safe_getattr(self.object, name)
                ret.append(ObjectMember(name, value))     # no doc
            except AttributeError:
                logger.warning(...)
        return False, ret
```

Because the collected entries carry no documentation comment, the unchanged
downstream filtering step (which reads each entry's comment to extract its
`:meta public:` / `:meta private:` metadata, falling back to the
leading-underscore convention) never sees the metadata for a module-level
variable. A variable named with a leading underscore but documented `:meta
public:` is therefore always classified private and dropped — the bug.

The gold patch adds a `ModuleDocumenter.get_module_members` method that builds a
`{name: ObjectMember}` dict in which **each entry carries the documentation
comment for its name** (`docstring="\n".join(attr_docs.get(('', name), []))`),
and rewrites `get_object_members` to source its entries from that dict:

```python
def get_module_members(self):
    attr_docs = self.analyzer.attr_docs if self.analyzer else {}
    members = {}
    for name in dir(self.object):
        value = safe_getattr(self.object, name, None)
        docstring = attr_docs.get(('', name), [])
        members[name] = ObjectMember(name, value, docstring="\n".join(docstring))
    for name in inspect.getannotations(self.object):
        if name not in members:
            docstring = attr_docs.get(('', name), [])
            members[name] = ObjectMember(name, INSTANCEATTR, docstring="\n".join(docstring))
    return members

def get_object_members(self, want_all):
    members = self.get_module_members()
    if want_all:
        if not self.__all__:
            return True, list(members.values())
        else:
            for member in members.values():
                if member.__name__ not in self.__all__:
                    member.skipped = True
            return False, list(members.values())
    else:
        memberlist = self.options.members or []
        ret = []
        for name in memberlist:
            if name in members:
                ret.append(members[name])
            else:
                logger.warning(...)
        return False, ret
```

Now every collected entry carries its documentation comment, so the downstream
filter sees the `:meta public:` metadata and keeps the documented variable.

The patch also adds a `RemovedInSphinx50Warning` deprecation warning inside the
free `importer.get_module_members` (and the corresponding import). That edit is
behaviorally inert with respect to the harness (a warning, not a value change)
and is carried verbatim in `patch.diff`; it is not modeled.

### Lean modeling

- `Member = { name, value : Option String, doc : String, skipped : Bool }` keeps
  only the observed fields of `ObjectMember`. `value = none` models the
  `INSTANCEATTR` sentinel used for annotation-only members; `value = some s`
  models a concrete `safe_getattr` value.
- `baseMembers dirNames annotNames val doc` builds the entry table: one entry per
  name in `dirNames` carrying `value = some (val name)` and `doc = doc name`,
  followed by one entry per annotation-only name not already present, carrying
  `value = none` and `doc = doc name`. This mirrors the dict built by the new
  `get_module_members` (insertion order = `dir` order then annotation order).
  **The fix is encoded here:** every entry's `doc` field is `doc name` (the
  attached documentation comment). The pre-patch impl builds the same table but
  with `doc = ""` (no comment attached).
- `expectedMembers` / `problem_spec_collectModuleEntries` pin the full result —
  the boolean first component, and for every entry its name, value, doc comment
  and skipped flag, in order — leaving nothing free (frame discipline,
  SPEC_GUIDE §0.5). `want_all` with no export list ⇒ `(true, table)`; with an
  export list ⇒ `(false, table with non-listed names marked skipped)`;
  explicit-name request ⇒ `(false, the present entries in request order)`.
- `implementation_collectModuleEntries` is the `Id.run do` skeleton: two
  `for … do` loops building the table (the dir loop, then the annotation loop
  with the "not already present" guard), then the three return branches.
- The pre-patch impl (`Solution_prepatch.lean`) attaches no comment (`doc = ""`).
  Its `correct_collectModuleEntries` is therefore unclosable whenever some
  collected name has a non-empty documentation comment — exactly the F2P
  scenario (`_PUBLIC_CONSTANT` documented `:meta public:`) and the G-DIFF signal.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a member name (`str`) | `String` | string equality |
| `dir(self.object)` | `dirNames : List String` | distinct names (precondition `dirNames.Nodup` holds for `dir`) |
| `inspect.getannotations(self.object)` keys | `annotNames : List String` | distinct names (precondition `annotNames.Nodup` holds for a dict's keys) |
| `safe_getattr(self.object, name, None)` | `val name : String` (carried as `some (val name)`) | rendered value string; total (default `None` ⇒ no raise) |
| `"\n".join(attr_docs.get(('', name), []))` | `doc name : String` | the joined documentation comment; `""` when absent |
| `INSTANCEATTR` | `Member.value = none` | annotation-only sentinel |
| `self.__all__` | `allNames : Option (List String)` | `None`/`[]` ⇒ "no export list" (`not self.__all__`) |
| `ObjectMember(name, value, docstring=d, skipped=s)` | `⟨name, some value, d, s⟩` | field-wise |
| `(want_all_flag, list(members.values()))` | `(Bool, List Member)` | tuple |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behaviour the patch changes is the
  construction of the entry table with each entry carrying its documentation
  comment; this is modeled DEEPLY and structurally (`baseMembers` /
  `expectedMembers`), and SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed operation. The values `val name` and the documentation comments
  `doc name` are INPUT observations (the result of `safe_getattr` and of the
  source-comment analyzer), not callee properties the proof consumes, so the
  `axioms` region declares no `opaque`/`axiom … _prop` and **G-AX skips**.
- **Flag dependency:** the discriminating scenario is the `want_all` path with no
  `__all__` (the `:members:` option, `self.__all__` empty), where every collected
  entry is returned. The documentation comment matters there because the
  downstream filter reads it; G-CONF and the prepatch both exercise that
  configuration as well as the `__all__` and explicit-name branches.
- The downstream privacy filter (`filter_members` / `extract_metadata`) is
  UNCHANGED by the patch and is out of scope; it is the consumer that reads the
  attached comment. A spec-satisfying entry table (comments attached) makes that
  unchanged consumer keep the documented variable, so the harness resolves.

## G-CONF fuzz seed

Pinned LCG seed: **8593** (see `conformance_check.py` `SEED`). Corpus: randomized
`(wantAll, allNames, memberlist, dirNames, annotNames, val, doc)` tuples over a
small name universe (names with and without leading underscores, distinct
`dir`/annotation name sets, random value strings, random comment strings
including the empty comment), ≥1e5 fuzzed inputs, plus hand-picked edge cases:
the F2P scenario (an underscore-prefixed name carrying a non-empty comment is
collected with its comment), no-export-list vs non-empty `__all__` (skipped
marking), and explicit-name requests with present/absent names. The R/I shadow of
`implementation_collectModuleEntries` is diffed against an in-process replica of
the POST-PATCH `get_object_members`/`get_module_members` logic.
