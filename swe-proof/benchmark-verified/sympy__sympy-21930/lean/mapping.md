# mapping.md — sympy__sympy-21930

## Instance
- repo: sympy/sympy
- base_commit: de446c6d85f633271dfec1452f6f28ea783e293f
- modeled functions: the three typeset-markup renderers
  `AntiSymmetricTensor._latex`, `CreateBoson._latex`, `CreateFermion._latex`
  in `sympy/physics/secondquant.py`
- spec_provenance: cold

## The modeled behavior

Each of the three carriers renders to a typeset-markup token. The pre-state
renderers emit a *bare* token whose body already carries a subscript (and, for
the dagger operators, a superscript), e.g. `b^\dagger_{0}`. When the surrounding
context appends a further superscript (e.g. squaring the operator), the trailing
exponent attaches only to the last group of the bare token rather than to the
whole token — `b^\dagger_{0}^{2}` is an ill-formed double superscript. Wrapping
the entire token in one outer brace pair (`{b^\dagger_{0}}`) makes the token a
single group, so a following exponent binds to the whole token.

Each renderer is an independent value-level string construction:

1. indexed symbol: `"%s^{%s}_{%s}" % (sym, join(upper), join(lower))`
   → enclose the result in one outer brace pair.
2. bosonic raising token: `"b^\\dagger_{%s}" % name` → enclose in one outer brace
   pair.
3. fermionic raising token: `"a^\\dagger_{%s}" % name` → enclose in one outer
   brace pair.

The `join` is the empty-string join of index names:
`"".join([i.name for i in self.args[k]])`.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python | location @ base_commit |
|---|---|---|
| `implementation_tensorMarkup` / `problem_spec_tensorMarkup` | `AntiSymmetricTensor._latex(self, printer)` | `sympy/physics/secondquant.py:220`–`224` (class `:153`) |
| `joinNames upper` | `"".join([i.name for i in self.args[1]])` (upper index block) | `sympy/physics/secondquant.py:222` |
| `joinNames lower` | `"".join([i.name for i in self.args[2]])` (lower index block) | `sympy/physics/secondquant.py:223` |
| `sym` argument | `self.symbol` (`self.args[0]`, a `Symbol`/text) | `sympy/physics/secondquant.py:221`, `symbol` property `:225` |
| `implementation_bosonCreatorMarkup` / `problem_spec_bosonCreatorMarkup` | `CreateBoson._latex(self, printer)` | `sympy/physics/secondquant.py:480`–`481` (class `:445`) |
| `implementation_fermionCreatorMarkup` / `problem_spec_fermionCreatorMarkup` | `CreateFermion._latex(self, printer)` | `sympy/physics/secondquant.py:941`–`942` (class `:799`) |
| `name` argument (bose/fermi) | `self.state.name` (the operator's index/state symbol name) | `:481`, `:942` |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean carrier |
|---|---|
| index/symbol name `str` (per code point) | `String` |
| list of index objects `self.args[k]` | `List String` (their `.name`s, in order) |
| `"".join(names)` | `joinNames names` |
| `_latex(...)` return `str` | `String` (the rendered token) |
| `%`-format substitution of a single `str` | Lean `String` `++` concatenation |

- The renderers take a `printer` argument but never use it; it carries no data
  into the result, so it is not modeled.
- The index objects' only observable contribution to the rendered string is their
  `.name`; the bijection therefore maps each index list to the `List String` of
  its names. Order is preserved (`join` concatenates in argument order).
- A `Symbol`'s LaTeX in these renderers is its plain `.name`/`.symbol` text
  spliced verbatim by `%s`; modeled as the `String` argument spliced verbatim by
  `++`. (The fuzz domain in G-CONF/G-AX therefore draws plain symbol names — the
  inputs these three call sites actually pass.)

## Callee provenance + flag deps
- No unchanged external callee is consumed as an `axiom <callee>_prop`. The only
  sub-operation is the empty-string join of names, modeled deeply as `joinNames`
  (an A-reference, validated == `"".join(...)` by G-AX). No flag-dependent
  callees. `axiom_check.py` validates the `joinNames` A-reference against the real
  `"".join` over fuzzed name lists.

## G-CONF fuzz seed
- pinned seed: `21930`
- fuzz domain: for the indexed-symbol renderer, a `sym` name plus an upper and a
  lower list (length 0..4) of index names; for the two dagger renderers, a single
  state name. Names are drawn over an alphabet spanning ASCII letters/digits, the
  symbols sympy index names admit, and a few non-ASCII code points; ≥10^5 samples
  across the three renderers. Each sample compares the Lean impl's shadow against
  the real post-patch `_latex` output.
