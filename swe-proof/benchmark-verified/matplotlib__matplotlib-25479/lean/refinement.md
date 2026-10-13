# refinement.md — matplotlib__matplotlib-25479

Each row maps an op in an `implementation_<name>` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). No consumed/reference axioms in this bundle.

## `implementation_colormapEq` ↔ post-patch `Colormap.__eq__`

| Lean op | patch.diff / repo op | tag | note |
|---|---|---|---|
| `(a b : Colormap)` | `self`, `other` (post `isinstance` narrowing) | R | the modeled fields of two `Colormap`s; `isinstance(other, Colormap)` precondition is the binder's typing (both are `Colormap`). |
| `if a.flag != b.flag then return false` | `if (... or self.colorbar_extend != other.colorbar_extend): return False` | R | `colorbar_extend` ↔ `flag : Int` injective code (mapping.md). The removed `self.name != other.name` disjunct is **absent** here — that is the fix. |
| `return a.table == b.table` | `return np.array_equal(self._lut, other._lut)` (after `_init()`) | R/I | shape-then-elementwise lut equality ↔ `List (List Int)` equality (rows capture shape + entries); `_init()` is a lazy-materialization side effect with no effect on the compared values (R, elided). |

The discriminating clause: the post-patch result does **not** depend on
`a.name`/`b.name`. The prepatch (`Solution_prepatch.lean`) reintroduces the
`a.name != b.name` guard — unprovable against `problem_spec_colormapEq`, which
pins the result to `(a.flag == b.flag) && (a.table == b.table)` with no name term.

## `implementation_register` ↔ post-patch `register` store + name tail

| Lean op | patch.diff / repo op | tag | note |
|---|---|---|---|
| `let mut stored := cmap` | `self._cmaps[name] = cmap.copy()` | R | `cmap.copy()` (`__copy__`) duplicates the object; on the modeled fields (name/flag/table) it is the identity, so the copy is a structural no-op (R). The dict store under `name` is modeled by the returned `stored` being the value retrievable at `name`. |
| `if stored.name != name then stored := { stored with name := name }` | `if self._cmaps[name].name != name: self._cmaps[name].name = name` | I | identical control flow and assignment: set the stored copy's display name to the registration name when it differs. |
| `return stored` | (the value now sitting at `self._cmaps[name]`) | R | the stored colormap; a later `get_cmap(name)` returns (a copy of) it. |

The discriminating clause: the post-patch stored object reports `name` as its
display name. The prepatch (`Solution_prepatch_2.lean`) omits the name-propagation
tail, so `stored.name` stays `cmap.name` — unprovable against
`problem_spec_register`, which demands `result.name = name`.

## No changed-inexpressible op

Every changed op is R or I. The only behaviors that "changed" are the removal of a
disjunct (eq) and the addition of a name assignment (register), both expressed
directly. No op required axiomatization; `conf_skip = false`.
