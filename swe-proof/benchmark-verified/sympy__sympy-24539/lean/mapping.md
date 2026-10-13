# mapping.md — sympy__sympy-24539

## Symbol binding (file:line @ base_commit 193e3825645d93c73e31cdceb6d742cc6919624d)

- Modeled function: `PolyElement.as_expr(self, *symbols)`
  — `sympy/polys/rings.py:618-624` @ base_commit (patched lines 619-622).
- Callee (UNCHANGED, A-reference): `expr_from_dict(rep, *gens)`
  — `sympy/polys/polyutils.py:375-387`. Imported into `rings.py` from
  `sympy.polys.polyutils`.
- Helper feeding the callee (UNCHANGED): `PolyElement.as_expr_dict(self)`
  — `sympy/polys/rings.py:626-628`; builds `{monom: to_sympy(coeff)}`.
- `self.ring.ngens` — number of ring generators (`PolyRing.ngens`).
- `self.ring.symbols` — the ring's own tuple of symbols (`PolyRing.symbols`).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean |
|---|---|
| `*symbols` (variadic tuple of `Symbol`) | `symbols : List Symb` |
| empty tuple `()` (i.e. `not symbols`) | `symbols.isEmpty` |
| `len(symbols)` | `symbols.length` |
| `self.ring.ngens : int` | `ngens : Nat` |
| `self.ring.symbols` | `ringSymbols : List Symb` |
| term data `self.as_expr_dict()` | `d : TermDict` (`entries : List (List Nat × Int)`) |
| a ring generator (any `Expr`; a `Symbol` is one case) | `Symb` (`named (name : String)` / `other (tag : Nat)`) |
| returned `Expr` | `SymExpr` wrapped as `Except.ok` |
| `raise ValueError(...)` | `Except.error ()` |
| `expr_from_dict(self.as_expr_dict(), *gens)` | `exprFromDict d gens` |

The generator carrier is two-case on purpose. A ring's generators are
arbitrary expressions, not necessarily named symbols: `PolyRing` builds them
through `_parse_symbols` (`sympy/polys/rings.py:181-192`), which accepts any
`Expr`, and `PolyRing((pi, sqrt(2)), ZZ, lex).symbols == (pi, sqrt(2))` —
neither generator has a `.name` at all. So `Symb` is `named (name : String)`
for the generators that carry a name and `other (tag : Nat)` for the ones that
do not, `tag` standing for nothing but the generator's own identity. A
generator is therefore not determined by a name and cannot be rebuilt from
one, which is all the modeled function needs: `expr_from_dict` substitutes its
generators positionally into `Pow(g, m)` and asks nothing else of them.

## Callee provenance + flag deps

- `expr_from_dict` is a pure UNCHANGED conversion: it iterates the term dict and
  `zip(gens, monom)`s the generators against each monomial's exponent vector,
  building `Add(*[Mul(coeff, *[Pow(g, m)...])...])`. The patch does NOT touch it.
  It is modeled as `opaque exprFromDict : TermDict → List Symb → SymExpr` so the
  spec can state WHICH symbol list is fed to it; no property of its output is
  consumed by the proof (A-reference, not A-consumed). It depends on no flags.
- Behaviour-defining fact used by the spec: `expr_from_dict` consumes its
  generator list positionally, so feeding `ringSymbols` vs `symbols` yields a
  different expression whenever the two lists differ — this is exactly the bug.

## G-CONF fuzz seed

`conf_seed = 24539` (pinned in meta.json). The shadow draws its generators as
named `Symbol`s, so it exercises the `named` case of the carrier; the nameless
case is covered in the G-PBT battery, whose `uniq-namewise-rebuild` reject
witness sits exactly there.
