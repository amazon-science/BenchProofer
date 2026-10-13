# mapping.md — symbol binding & type bijection (sympy__sympy-19637)

## Modeled function
- **Lean** `implementation_kernSHit : Bool → List Char → Except Unit Bool`
- **Python** `kernS(s)` — `sympy/core/sympify.py:440-541 @ 63f8f465d4`.
  The modeled SLICE is the `hit`-flag computation inside the bracket-handling
  branch, lines 471-516 (the `hit = False` init at 471, the
  `if '(' in s and not quoted:` gate at 473, the `if ' ' in s:` marker
  substitution at 510-515, and the membership read `hit = kern in s` at 516).

The patch (the changed op) is exactly the indentation/scope of the membership
read: pre-patch `hit = kern in s` runs UNCONDITIONALLY after the
`if ' ' in s:` block, but `kern` is bound only inside that block; gold moves the
read inside `if ' ' in s:` and adds `else: hit = False`. Net post-patch
behaviour: `hit` is set iff the bracket branch is active and a space was present
(so the substituted marker `kern` occurs in `s`); otherwise `hit` is unset, and
the routine NEVER raises `UnboundLocalError`.

The slice abstracts the unmodified upstream of the branch into the single input
`parenBranch : Bool` (the value of `'(' in s and not quoted`, computed before
the modeled region) and the post-transform string into `s : List Char` (the
string at line 510, after the `*(`/`-(`/nesting rewrites but before space
substitution). Those rewrites are unchanged by the patch; the only observable
they feed into the modeled flag is whether a space character is present.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| branch gate `'(' in s and not quoted` (bool) | `parenBranch : Bool` | unchanged upstream predicate; the slice's first input |
| transformed string `s` at line 510 (`str`) | `s : List Char` | per-code-point; only `' ' in s` is observed |
| `' ' in s` | `s.contains ' '` | space-presence test (Python `in` on `str` ↔ `List.contains`) |
| `hit` (bool) on normal return | `Except.ok hit` | well-defined flag |
| `UnboundLocalError` raised (pre-patch) | `Except.error ()` | marker referenced before assignment |

## Callee provenance
- The marker-membership step `kern in s` is the changed operation itself; its
  value post-patch is fully determined: when a space is present a fresh marker
  is substituted for the spaces and so necessarily occurs in the result string
  (`kern in s` is `True`); when no space is present the marker is never bound
  and the flag is `False`. This is modeled DEEPLY as the boolean
  `parenBranch && s.contains ' '` (an **A-reference**, validated by G-AX against
  the real post-patch `kernS` flag computation), NOT axiomatized.
- The marker-generation loop (`while kern in s: kern += choice(...)`) only
  ensures `kern` is *fresh*, i.e. absent from the pre-substitution string; after
  `s = s.replace(' ', kern)` the marker is present iff a space was present. The
  randomness (`choice`) does not affect the modeled flag and is not modeled.
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Flag dependency
The membership read is reached only when the bracket-handling branch is active
(`parenBranch = true`). G-AX / G-CONF fuzz both `parenBranch` values and both
space-presence configurations, with the discriminating case being
`parenBranch = true ∧ no space` (the pre-patch crash, post-patch `hit = False`).

## G-CONF fuzz seed
Pinned seed: **19637**. ≥10^5 fuzzed (parenBranch, s) pairs over an alphabet
that oversamples the space character and parenthesis/operator tokens.
