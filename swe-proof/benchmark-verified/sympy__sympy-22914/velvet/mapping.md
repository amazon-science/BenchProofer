# mapping.md — sympy__sympy-22914

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c4e836cdf73fc6aa7bab6a86719a0f08861ffb1d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo files under change: `sympy/printing/pycode.py` (the lookup table the gold
patch extends). The behavior it changes manifests in
`sympy/printing/codeprinter.py` (the application-printing dispatch that reads
that table).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `printApp (head : List Char) (args : List (List Char)) (fallback : List Char)` | `CodePrinter._print_Function(self, expr)` — `sympy/printing/codeprinter.py:415` | the modeled changed behavior: how the printer emits one function-application node. The gold patch adds two entries to the builtin-equivalent table (`sympy/printing/pycode.py:19`) read by the `if expr.func.__name__ in self.known_functions:` branch (`codeprinter.py:416-429`). |
| `renderCall (name) (args)` | the known-function emission `func(*[self.parenthesize(item, 0) for item in expr.args])` (`codeprinter.py:427`), i.e. `"{name}({comma-joined args})"` | pure spec: assemble `name(arg1, arg2, ...)`. |
| `joinComma` | the `", ".join(...)` of the rendered operands implied by `func(*rendered_args)` / `stringify(args, ", ")` (`codeprinter.py:427,429`; `str.py:41`) | pure spec: comma-separated rendered operands. |
| `head` (`List Char`) | `expr.func.__name__` — the application head/function name (`codeprinter.py:416`) | read-only input; the routine never alters it (directive 5). |
| `args` (`List (List Char)`) | `[self.parenthesize(item, 0) for item in expr.args]` — the operands ALREADY rendered to source text (`codeprinter.py:427`) | read-only input; recursive operand rendering is unchanged infrastructure supplied to the routine. |
| `fallback` (`List Char`) | the source text the UNCHANGED surrounding printing machinery emits for a node whose head is none of `Min`/`Max`/`Abs` — the `_print_<class>` dispatch / `_rewriteable_functions` rewrite (`codeprinter.py:430-441`) / `_print_not_supported` paths, all untouched by the gold hunk | read-only input; that machinery is pre-existing, unchanged infrastructure whose OUTPUT is supplied to the modeled per-node decision. The fourth post-condition pins the routine to return it verbatim for every non-mapped head (the no-change contract). |

The patch's literal hunk adds, to `_known_functions` (`pycode.py:19-21`):
`'Min': 'min'` and `'Max': 'max'`, alongside the pre-existing `'Abs': 'abs'`.
`_known_functions` is folded into `known_functions` via `_kf`
(`pycode.py:79-82`), the dict `_print_Function` consults.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| emitted source text (a Python `str`: the printer's return value, each rendered operand, and the unchanged machinery's emission) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; `", ".join` ↔ `joinComma` |
| the application head name `expr.func.__name__` (a `str`, e.g. `"Min"`) | `head : List Char` | `"Min"` ↔ `"Min".toList`; equality of head names ↔ `List Char` equality |
| the rendered operands `[parenthesize(arg,0) for arg in expr.args]` (a list of `str`) | `args : List (List Char)` | each rendered operand `str` ↔ its `List Char`; the operand list ↔ the `List`. The recursive rendering itself is NOT modeled — its OUTPUT (already-rendered operand texts) is the input `args`. |
| the unchanged machinery's emission for a non-mapped head (a `str`) | `fallback : List Char` | the emitted text ↔ its `List Char`. The machinery itself is NOT modeled — its OUTPUT is the input `fallback`. |

Strings are modeled per code point (`List Char`) because call assembly is a
per-code-point concatenation; Lean `List Char` indexing/concat is total and
sound.

**Why the operands and the non-mapped emission are inputs, not callees.**
`_print_Function` renders each operand by recursively calling
`self.parenthesize`/`self._print`; a node whose head has no builtin entry is
emitted by the surrounding machinery (rewrite branch, per-class printers,
not-supported fallback). Both are pre-existing, unchanged machinery; the gold
patch does not touch them. The modeled behavior is purely the per-node DECISION
(which builtin name for the three mapped heads, assemble the call; otherwise
keep the unchanged emission). So the rendered operand texts enter `printApp` as
the read-only input `args`, and the unchanged emission enters as the read-only
input `fallback`; there is no operand-rendering or fallback-printing axiom to
consume and no deep-model reference. G-CONF supplies the real
`parenthesize(arg,0)` outputs as `args` and the real pristine-printer
`doprint(expr)` as `fallback` (poison sentinel on mapped heads) so the
differential isolates exactly the modeled R/I leg.

## 3. Callee provenance

**No consumed axioms; no deep-model references.** The modeled decision is
spelled out in full (the `if head = … then renderCall …` ladder + the fallback
pass-through + `renderCall`/`joinComma` pure helpers). The only things the
routine relies on from elsewhere — the rendered operand texts and the unchanged
machinery's emission — are INPUTS (`args`, `fallback`), per §2. Hence
`axiom_check.py` is absent and G-AX is `skip` (no axioms in the bundle),
consistent with the no-axiom exemplar `tasks/django__django-12406/`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`22914`** so the
consumer-side verdict is reproducible. It builds the SHADOW by transliterating
`renderCall`/`joinComma`, the head→builtin dispatch (`Min→min`, `Max→max`,
`Abs→abs`), and the fallback pass-through, feeding it the printer's own
`parenthesize(arg, 0)` outputs as the rendered-operands input `args` and a
pristine same-class printer's `doprint(expr)` as `fallback` on non-mapped heads
(a poison sentinel on mapped heads, so a shadow that leaks `fallback` where the
builtin call is required diverges); the ORACLE is the patched
`PythonCodePrinter().doprint(expr)` on real `Min`/`Max`/`Abs`/other (`sin`,
`exp`, `gamma`, undefined `f`, `Piecewise`, …) expressions. Boundary cases
(2–5 args, nesting, integer args, non-mapped heads) + a seeded random
expression tree over both mapped and non-mapped constructors, ≥10⁵ inputs.
