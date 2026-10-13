# refinement.md — django__django-13658

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_settings_parser` impl region and the deep `program_name` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed**, where the proof uses the axiom's
`Ensures`, vs **A-reference**, where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The parser-construction site — `ManagementUtility.execute`

Gold hunk (`django/core/management/__init__.py:347`):
```
- parser = CommandParser(usage='%(prog)s subcommand [options] [args]', add_help=False, allow_abbrev=False)
+ parser = CommandParser(
+     prog=self.prog_name,
+     usage='%(prog)s subcommand [options] [args]',
+     add_help=False,
+     allow_abbrev=False,
+ )
```

| # | model.py impl op (`build_settings_parser`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `self: Utility` with read-only fields `argv0_basename`, `sys_argv0_basename` | `self` is the `ManagementUtility`; `self.prog_name` is `os.path.basename(self.argv[0])` (+ bootstrap rule), and the ambient default is `os.path.basename(sys.argv[0])` | R | the two `str` first-argument basenames ↔ two `List[int]` of code points (mapping.md §1, §2). They are independent inputs and may disagree — precisely the embedded-caller scenario the issue describes. |
| A2 | `parser = Parser()` then `parser.prog := …` | `parser = CommandParser(prog=…, usage=…, add_help=False, allow_abbrev=False)` | R | `CommandParser` ↔ `Parser`, observing only the program name `prog` (mapping.md §2). The `usage`/`add_help`/`allow_abbrev` keywords do not affect `prog` (G-AX §3.2), so they are omitted from the carrier. |
| A3 | `parser.prog := program_name(ToSeq(self.argv0_basename))`, spelled out as: if the basename is the bootstrap name emit the module-invocation code points, else copy the basename code points one by one | `prog=self.prog_name`, where `self.prog_name = os.path.basename(self.argv[0])` with `'__main__.py' → 'python -m django'` | A-reference | the changed operation — *deriving the parser's program name from the utility's OWN first argument* — is modeled **deeply**: `program_name` (the pure region) and the verified loop ARE that derivation. There is no consumed axiom about the function under change. The deep model is validated **== the real primitives** out-of-band: G-AX (axiom_check.py) asserts `program_name(basename(argv0))` equals the real `ManagementUtility.__init__` `prog_name` (§3.1) and that the real argument-parser adopts an explicit `prog` (§3.2). |
| A4 | `return parser` | the assigned `parser` flows on to `parser.add_argument(...)`/`parse_known_args(...)`; only its `prog` is observed by the F2P test (through `%(prog)s`) | I | the returned parser object carries the program name; control flow is identical. |

The discriminating content of the change — the parser's program name comes from
the utility's OWN `argv[0]` (`self.prog_name`), NOT from the ambient
`sys.argv[0]` — lives in `Result().prog == program_name(ToSeq(self.argv0_basename))`
(model) ⇔ the added `prog=self.prog_name` keyword (real). The pre-patch supplies
no `prog`, so the parser defaults to `os.path.basename(sys.argv[0])`;
`model_prepatch.py` reproduces that (it derives `prog` from
`self.sys_argv0_basename`) and **fails** the postcondition
`ToSeq(Result().prog) == program_name(ToSeq(self.argv0_basename))` whenever the
two sources disagree — exactly the spec sensing the change (G-DIFF). In the F2P
regression test the disagreement is forced: the utility's own argv is
`['django-admin', …]` while `sys.argv` is mocked to `[None, …]`, so the ambient
source is not merely different but unusable (`os.path.basename(None)` raises),
which is why the pre-patch crashes and the post-patch prints `usage:
django-admin shell`.

## B. The program-name rule (`program_name`) is deep, not axiomatized

`program_name` (the basename, with `'__main__.py' → 'python -m django'`) is the
`__init__` computation of `self.prog_name` — an **unchanged** computation the fix
merely *reuses* at the call site. It is modeled deeply (spelled-out pure
function + the verified copy loop), so it is an **A-reference** (validated ==
real by G-AX §3.1), never a consumed axiom. No `@ContractOnly` is shipped.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
**source selection** for the parser's program name (utility argv vs. ambient
argv) — is modeled **deeply** (the spelled-out `program_name` over
`self.argv0_basename`, step A3, an **A-reference**), not hidden behind an axiom
about the function under change. There are no consumed axioms; the only kind-A
elements are the two **A-references** the deep model is checked against by G-AX
(the `__init__` program-name rule and the argument-parser program-name handling),
both unchanged library primitives.

## D. verify(model) ⇒ resolved

`build_settings_parser` verifies only if its parser's program name equals the
program name derived from the utility's OWN first argument (A3), grounded in the
actual input `self.argv0_basename` rather than the ambient `self.sys_argv0_basename`.
By R (`str` ↔ `List[int]`, `CommandParser` ↔ `Parser` on `prog`, the unaffected
`usage`/`add_help`/`allow_abbrev` keywords) the verified builder equals
`CommandParser(prog=self.prog_name, usage=…, add_help=False, allow_abbrev=False)`;
by G-AX the deep model `program_name` equals the real `prog_name` computation
(A-reference §3.1) and the real argument parser adopts an explicit `prog`
(A-reference §3.2). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited library primitives —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ); there is no consumed-axiom trust point here.
