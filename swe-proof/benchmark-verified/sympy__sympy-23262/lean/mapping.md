# mapping.md — sympy__sympy-23262

## Symbol binding (file:line @ base_commit fdc707f73a)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_renderArg` / `problem_spec_renderArg` / `specRender` | `_recursive_to_string(doprint, arg)` | `sympy/utilities/lambdify.py:948-967` |
| `Arg.tuple` delimiter assembly | `left, right = "(", ",)"` (fixed) / `"()"` (buggy) branch | `sympy/utilities/lambdify.py:961` |
| `Arg.list` delimiter assembly | `left, right = "[", "]"` branch | `sympy/utilities/lambdify.py:959` |
| `String.intercalate ", "` | `', '.join(...)` | `sympy/utilities/lambdify.py:964` |

## Modeled function

`_recursive_to_string` walks a nested structure of SymPy/python `list`/`tuple`/
leaf objects and renders it to source-string form. The patched line assembles a
container as `left + ', '.join(render(e) for e in arg) + right`.

The bug: tuple delimiters were set by the literal `left, right = "()"`, which
sequence-unpacks the 2-char string `"()"` into `left="("`, `right=")"`. A
one-element tuple `(1,)` therefore rendered as `(1)` — a non-tuple. The fix sets
`right = ",)"` so every tuple closes with a trailing comma: `(1,)`, `(1, 2,)`,
`(,)` for the empty tuple. (The list branch `"[]"` already unpacked to the
correct `"["`, `"]"`, so list rendering is unchanged.)

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| recursive arg object (list/tuple/leaf) | `inductive Arg` with `leaf : String`, `list : List Arg`, `tuple : List Arg` |
| python `list` node | `Arg.list` |
| python `tuple` node | `Arg.tuple` |
| a leaf object after `doprint(leaf)` / `str(leaf)` produced its source string | `Arg.leaf s` (the already-printed string `s`) |
| rendered output string | Lean `String` |

### doprint refinement (R, not an axiom)

The unchanged callee `doprint` (and the `isinstance(arg, (Basic, MatrixOperations))`
/ `isinstance(arg, str)` leaf cases) only produce the per-leaf string that the
assembly then splices. The fix does not touch leaf rendering — only container
delimiter assembly. We therefore refine every leaf to the string it would print
to (`Arg.leaf s`). `doprint` is **refined away** (type-only R), not called in the
impl, so it is neither an A-consumed nor an A-reference callee, and needs no
`opaque`/axiom declaration. axiom_check.py is a skip stub.

## Callee provenance / flag deps

None. No flag-dependent callee; the assembly is unconditional once the
list-vs-tuple branch is selected.

## G-CONF fuzz seed

Pinned seed: `23262`. conformance_check.py generates random nested `Arg` trees
(depth ≤ 5, leaf strings from a small alphabet incl. empty), renders them with
the Lean-impl Python shadow, and diffs against the real patched
`_recursive_to_string` (leaves pre-substituted as `str`-returning identity via a
trivial `doprint`).
