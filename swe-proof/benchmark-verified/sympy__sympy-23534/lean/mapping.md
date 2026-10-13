# mapping.md — sympy__sympy-23534

## Symbol binding
- **Modeled function:** `symbols(names, *, cls=Symbol, **args)`
  — `sympy/core/symbol.py:586` @ base_commit `832c24fec1046eaa544a4cab4c69e3af3e651759`.
- **Changed site:** the non-string (`else`) branch that iterates a sequence of
  name-specs and recurses, `sympy/core/symbol.py:789-794` @ base_commit.

## Behavior under model
`symbols` accepts either a single name token (a `str`) or an arbitrarily nested
*sequence* of name-specs (tuple/list/set). For a sequence it returns a container
of the same shape whose entries are the result of applying `symbols`
**recursively** to each element, carrying the requested target class `cls`
through every layer. For a single token it parses the token (possibly a range
producing several objects) and constructs objects of class `cls`.

The observable property the fix restores: the target class `cls` reaches **every
leaf**, including leaves nested below one or more sequence layers — e.g.
`symbols(('q:2','u:2'), cls=Function)` must yield `UndefinedFunction` objects,
not default `Symbol`s.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| target class object (`Symbol`/`Function`/`Wild`/`Dummy`) | `ClassId := Nat` (a class tag); `defaultClass = 0` ↔ `Symbol` |
| a single name token `str` | `String` |
| nested name-spec (`str` \| seq of name-specs) | `inductive NameSpec` (`tok String` \| `seq (List NameSpec)`) |
| result for a token (constructed object under class X) | `SymResult.leaf X s` — a **class-tagged leaf** |
| result for a sequence (same-shape container of results) | `SymResult.node (List SymResult)` |
| `symbols(token, cls=X)` on a single token (string path) | `SymResult.leaf X token` |

The single-token construction result is modeled CONCRETELY as a class-tagged
leaf `SymResult.leaf cls s`. The unchanged token-parsing internals (range
expansion, escape handling, assumption-`args` application, scalar-vs-tuple
collapsing) are abstracted to the one component the fix governs — the class the
constructed object is built under. There is **no opaque/axiomatized callee and
no consumed `_prop` axiom**: `correct_symbols` discharges by structural
induction. `axioms: []`; `axiom_check.py` is a skip stub.

## Callee provenance + flag deps
- The token arm corresponds to the `isinstance(names, str)` branch of `symbols`
  (`sympy/core/symbol.py:706-787`); the constructed object's class is determined
  by the `cls` argument. Assumption kwargs `**args` are orthogonal to the fix
  and held fixed in G-CONF.

## G-CONF fuzz seed
`SEED = 23534` (pinned in `conformance_check.py`).
