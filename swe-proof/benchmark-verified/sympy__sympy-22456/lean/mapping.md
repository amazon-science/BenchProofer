# mapping.md — sympy__sympy-22456

## Instance
- repo: sympy/sympy
- base_commit: a3475b3f9ac662cd425157dd3bdb93ad7111c090
- modeled behavior: the argument-reconstruction round-trip of the atomic
  `codegen.ast` string value, under EVERY argument-passing convention that value
  publishes about itself — `expr.func(*expr.args) == expr` (the invariance that
  holds for any `Basic` subclass) AND `expr.func(**expr.kwargs()) == expr` (the
  invariance the value already had). The problem_statement names BOTH identities
  verbatim, so `func`/`args`/`kwargs`/`String` are public terms (not leakage).
  The F2P test asserts both, which is why the spec quantifies over the convention
  (`∀ c : ReconCall, result c = some s`) rather than pinning one of them.

## Symbol binding (file:line @ base_commit)
- `sympy/codegen/ast.py:872` — `class String(Token)` (the atomic string value
  under fix). `__slots__ = ('text',)`, `not_in_args = ['text']`, `is_Atom = True`.
- `sympy/codegen/ast.py:165` — `class Token(CodegenAST)`: the base whose
  `__new__` builds the parent (`Basic`) positional args as
  `[val for attr,val in zip(__slots__, attrvals) if attr not in not_in_args]`.
  For `String`, every slot (`text`) is in `not_in_args`, so the positional
  Basic args are **empty**: `String('foo').args == ()`.
- `sympy/codegen/ast.py:165` region — `Token.kwargs()`: the value's KEYWORD
  self-report, derived from the slots as `{k: getattr(self, k) for k in
  __slots__}`, so pre-patch `String('foo').kwargs() == {'text': 'foo'}`.
- `sympy/core/basic.py` — `Basic.func` (unchanged callee): the generic
  reconstruction callable returns `self.__class__`, i.e. the class constructor.
  `obj.func(*obj.args)` and `obj.func(**obj.kwargs())` are the two generic
  round-trips, differing only in which self-report is handed to the callable.
- gold patch sites (`sympy/codegen/ast.py`):
  - import of `Atom` (line 133 region) — changes the MRO/atomicity of `String`.
  - `class String(Atom, Token)` (line 872) — makes the value a genuine atom.
  - new `String.kwargs` returning `{}` and new `String.func` property returning
    `lambda: self` (lines 906–913 region) — the reconstruction callable now
    CONSUMES NO reconstruction data and returns the object itself, and the
    value's keyword self-report becomes empty to match.

## Behavior: pre vs post
- PRE-PATCH: `String.func` is inherited `Basic.func` = the class `String`. The
  positional args are empty, so `func(*args) == String()` raises `TypeError`
  (the required `text` is missing) — the POSITIONAL round-trip cannot reproduce
  the value. The KEYWORD round-trip does: `kwargs() == {'text': ...}` and
  `String(text=...) == obj`. So pre-patch the two conventions DISAGREE.
- POST-PATCH: `String.func` returns `lambda: self` and `String.kwargs()` returns
  `{}`; the callable admits exactly the (empty) data the value publishes under
  each convention, so `func(*args) == self` AND `func(**kwargs()) == self`.
- The two conventions are INDEPENDENT, and both failure directions are real
  (measured; table in refinement.md): a callable admitting no keyword while the
  value still publishes one satisfies the positional identity and RAISES on the
  keyword identity, failing the F2P from the opposite side to the prepatch.
- What is NOT part of the modeled behavior: the particular way agreement is
  reached. An alternative patch that leaves `kwargs()` returning `{'text': ...}`
  and instead makes the callable accept any arguments also satisfies both
  identities and PASSES the F2P (measured on the real repo). So `kwargs() == {}`
  is incidental to the gold spelling and is deliberately NOT pinned; the pin is
  that whatever the value publishes, its callable admits and round-trips.

## Lean ↔ Python type bijection (G-CONF / G-AX)
| Lean | Python |
|---|---|
| `StringObj` (structure, field `text : String`) | a `codegen.ast.String` instance |
| `s.text : String` | `String.text : str` |
| `stringArgs s : List StringObj` (always `[]`) | `String_instance.args : tuple` (always `()`) |
| `ReconCall` (`positional` \| `keyword`) | which self-report is handed to the reconstruction callable: `*obj.args` vs `**obj.kwargs()` |
| the impl's `kwargNames : List String` | the KEY SET of `obj.kwargs()` (what determines whether the callable admits the call; the mapping's values are the value's own text, already carried by `s.text`) |
| `implementation_reconstructString s : ReconCall → Option StringObj` | the round-trip at each convention: `some s` = "reconstructed value equal to the original"; `none` = "round-trip raised / failed / yielded a different value" |
| `∀ c, result c = some s` | `obj.func(*obj.args) == obj` **and** `obj.func(**obj.kwargs()) == obj` are both `True` |

## Callee provenance + flag deps
- `Basic.func` / the generic reconstruction: UNCHANGED callee, but the
  reconstruction is modeled DEEPLY (the impl spells out both round-trips over the
  data the value publishes), so it is an A-reference exercised by G-CONF, NOT a
  consumed axiom. No `opaque` callee is needed; G-AX is a skip.
- No flag dependence.

## G-CONF fuzz seed
- seed = 22456 (pinned in conformance_check.py and meta.json verifier_pins).
- `conformance_check.py` observes BOTH conventions per fuzzed value (2 x N
  observations), matching the quantified clause.
