# refinement.md — sphinx-doc__sphinx-8593

Operation-by-operation correspondence between
`implementation_collectModuleEntries` (Solution.lean impl region) and
`patch.diff` (the POST-PATCH `ModuleDocumenter.get_module_members` +
`ModuleDocumenter.get_object_members`). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `for name in dirNames do members := members ++ [⟨name, some (val name), doc name, false⟩]` | gold `get_module_members`: `for name in dir(self.object): value = safe_getattr(self.object, name, None); docstring = attr_docs.get(('', name), []); members[name] = ObjectMember(name, value, docstring="\n".join(docstring))` | R (each entry built with its value AND its recorded comment) |
| 2 | `for name in annotNames do if (members.find? …).isNone then members := members ++ [⟨name, none, doc name, false⟩]` | gold `get_module_members`: `for name in inspect.getannotations(self.object): if name not in members: members[name] = ObjectMember(name, INSTANCEATTR, docstring="\n".join(attr_docs.get(('', name), [])))` | R (annotation-only entry, sentinel value, with its comment) |
| 3 | `if wantAll then match allNames with … | none => return (true, members)` and `some [] => return (true, members)` | gold `get_object_members`: `if want_all: if not self.__all__: return True, list(members.values())` (`not self.__all__` ⇔ `None` or empty) | I |
| 4 | `some names, names ≠ [] ⇒ for m in members: if m.name ∈ names then ret ++ [m] else ret ++ [{m with skipped := true}]; return (false, ret)` | gold `get_object_members`: `else: for member in members.values(): if member.__name__ not in self.__all__: member.skipped = True; return False, list(members.values())` | I |
| 5 | `else (wantAll = false): for name in memberlist do match members.find? … with some m => ret ++ [m] | none => pure ()` | gold `get_object_members`: `else: memberlist = self.options.members or []; ret = []; for name in memberlist: if name in members: ret.append(members[name]) else: logger.warning(…)` | I (the warning is a side effect, not a value) |
| — | the whole table: every entry carries `doc name` (its recorded documentation comment) | the FIX: collect each member through `ObjectMember(name, value, docstring="\n".join(attr_docs.get(('', name), [])))` so the entry carries its source comment | R (the discriminating attachment) |

Notes:

- **The R leg is the comment attachment** (ops 1, 2 and the "—" row): the
  post-patch code builds each collected entry carrying the documentation comment
  recorded for its name (`docstring="\n".join(attr_docs.get(('', name), []))`);
  pre-patch the entries came from `importer.get_module_members`, which returned
  bare `(name, value)` tuples, so the `ObjectMember`s were built with the default
  `docstring=None` (no comment). SPEC_GUIDE §3 forbids axiomatizing this
  deeply-modeled changed construction, so it is spelled out structurally in both
  `problem_spec` (`baseTable` carries `doc n` on every entry) and the impl (each
  entry built with `doc name`), not axiomatized.
- **No A-consumed / A-reference legs, no opaque callees.** The two per-name
  observations the routine reads — a member's value (`safe_getattr(…, None)`,
  total because of the default) and the documentation comment recorded for the
  name (`attr_docs.get(('', name), [])`, joined) — are taken as the INPUT
  functions `val` and `doc`. The proof consumes no property of either, so there
  is no `axiom … _prop` and **G-AX skips**. `result` is fully pinned by
  `problem_spec` to `expectedResult`, so no output component is left free (frame
  discipline, SPEC_GUIDE §0.5): every returned entry's name, value, recorded
  comment and skipped flag, and the boolean flag, are pinned.
- **Ops 3, 4, 5 are I (identical concrete ops):** the three resolution modes
  (`want_all`/no-`__all__`, `want_all`/`__all__` with skipped marking,
  explicit-name request dropping absent names) are unchanged control flow,
  modeled concretely. The Python dict's insertion order (`dir` order then
  annotation order) is mirrored by the two append loops over `dirNames` then
  `annotNames`; the `Nodup` preconditions reflect that `dir(...)` and a dict's
  keys are distinct.
- **The fix itself** is the "—" row: before the patch the collected entries
  carried no documentation comment, so the unchanged downstream privacy filter
  (which reads each entry's comment to extract its `:meta public:` /
  `:meta private:` metadata, else falls back to the leading-underscore rule)
  never saw the metadata for a module-level variable — an underscore-named
  variable documented `:meta public:` was always dropped. The pre-patch impl
  (`Solution_prepatch.lean`) reproduces this exactly: it builds every entry with
  `doc = ""`. Its `correct_collectModuleEntries` is therefore unclosable whenever
  some collected name has a non-empty recorded comment (the two tables disagree
  on that entry's `doc` field) — exactly the F2P scenario (`_PUBLIC_CONSTANT`
  documented `:meta public:`) and the signal G-DIFF wants.
- **G-CONF** mechanically refutes the R/I legs over ≥1e5 fuzzed inputs (no
  A-consumed legs): the Python shadow of the impl is diffed against an in-process
  replica of the post-patch routine, with the per-name `val`/`doc` observations
  the same input on both sides so the diff isolates the modeled
  construction/resolution.
