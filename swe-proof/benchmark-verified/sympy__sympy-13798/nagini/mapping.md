# mapping.md — sympy__sympy-13798

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7121bdf1facdd90d05b6994b4c2e5b2865a4638a`, states the type
abstraction, and gives the provenance of the one axiom.

Repo file under change: `sympy/printing/latex.py`.

## 1. Symbol ↔ repo binding

The patched function is `LatexPrinter.__init__` (`sympy/printing/latex.py:138`),
specifically the two assignments that derive the multiplication separators from
the `mul_symbol` setting (`latex.py:159-163` at base_commit). The derived
strings are stored in `self._settings['mul_symbol_latex']` and
`self._settings['mul_symbol_latex_numbers']` and later consumed as the
multiplication separators when printing `Mul`/`Pow` (`latex.py:336,390,391`).
The model exposes the two derivations as two functions.

| model.py symbol | repo counterpart (file:line @ base_commit) | role |
|---|---|---|
| `general_separator(sym)` | computation of `self._settings['mul_symbol_latex']` — `latex.py:159-160` (post-patch the `try/except KeyError` block) | the general multiplication separator derived from `mul_symbol` |
| `numeric_separator(sym)` | computation of `self._settings['mul_symbol_latex_numbers']` — `latex.py:162-163` (post-patch the `try/except KeyError` block) | the between-numbers multiplication separator derived from `mul_symbol` |
| `trimmed(s)` *(axiom — A-reference)* | `str.strip()` — Python builtin, called post-patch at `latex.py` inside the second `except KeyError` (`self._settings['mul_symbol'].strip()`) | unchanged whitespace-trim callee the numeric branch keys on |
| `token_sep(s)` | the dict literal `mul_symbol_table` (`latex.py:152-157`) restricted to its non-`None` keys | pure spec: the fixed separator for a recognised token |
| `tok_dot/tok_times/tok_ldot` | the dict keys `"dot"`, `"times"`, `"ldot"` | pure spec: the recognised token strings |
| `sep_blank/sep_ldot/sep_dot/sep_times` | the dict values `r" "`, `r" \,.\, "`, `r" \cdot "`, `r" \times "` | pure spec: the fixed separators as code-point sequences |
| `is_known_token(s)` | `mul_symbol in mul_symbol_table` for a non-`None` token (i.e. the `try` succeeds) | pure spec: token is one of the four recognised keys |
| `is_spacing_only(t)` | the membership test `... in ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']` (`latex.py`, the second `except` body, post-patch) | pure spec: a trimmed token that is LaTeX spacing only |
| `is_visible_ascii(c)` / `no_outer_blank(s)` | (no repo symbol) | the precondition under which `str.strip` is the identity — used only to give the `trimmed` axiom a sound, executable-checkable contract |

The pre-patch repo behaviour the change fixes: at base_commit the two
assignments are *unguarded* dict lookups
(`mul_symbol_table[self._settings['mul_symbol']]` and
`mul_symbol_table[self._settings['mul_symbol'] or 'dot']`), so any `mul_symbol`
outside `{None, "dot", "times", "ldot"}` raises `KeyError` and the printer
cannot be constructed at all — a user-supplied separator is rejected. The patch
wraps each lookup in `try/except KeyError`, honouring an unrecognised selector.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `mul_symbol` setting: `None` or a `str` | `Optional[List[int]]`: `None` ↔ the unset value, else `List[int]` of Unicode code points | `s[k]` ↔ `sym[k] == ord(s[k])`; `len(s)` ↔ `len(sym)`; `str` `==` ↔ `PSeq` `==` via `ToSeq`; the `None` dict key ↔ the `None` carrier |
| `str` separator value (the two derived settings, and the dict values/keys) | `PSeq[int]` of code points (materialized result `List[int]`) | `ToSeq(list)` materializes; `PSeq` `==`/`take`/index mirror `str` `==`/slice/index |
| `mul_symbol_table[k]` dict lookup (4 keys) | `is_known_token` + `token_sep` (None handled separately) | the dict is finite; the lookup ↔ a value chosen by key equality |
| `mul_symbol or 'dot'` (the `None`→`'dot'` defaulting for the numbers key) | the `sym is None -> sep_dot()` branch of `numeric_sep_of` | `None or 'dot' == 'dot'`, and `mul_symbol_table['dot'] == r" \cdot "` ↔ `sep_dot()` |
| `mul_symbol.strip()` | `trimmed(ToSeq(sym))` (axiom) | `str.strip` ↔ `trimmed`; see §3 |

`str` indexing/iteration is banned in Nagini, so the carrier is
`Optional[List[int]]` and the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `trimmed` ↔ `str.strip()` (A-reference)
**Callee:** the Python builtin `str.strip()` (no arguments) — removes leading
and trailing characters for which `str.isspace()` is true (the ASCII whitespace
`\t\n\v\f\r\x1c-\x1f ` plus the Unicode whitespace set). Docs:
https://docs.python.org/3/library/stdtypes.html#str.strip.

The axiom encodes only the obligation the numeric branch relies on: a token
with no outer whitespace is left unchanged by the trim, i.e.

  `no_outer_blank(s)  ⇒  trimmed(s) == s`.

`no_outer_blank(s)` is defined conservatively in the model: `s` is empty, or its
first and last code points are printable non-space ASCII (`33..126`). **No code
point that `str.strip()` removes lies in `33..126`** (the stripped class is
`{9..13, 28..32, 133, 160, 5760, 8192..8202, 8232, 8233, 8239, 8287, 12288}`),
so the predicate is a sound under-approximation of "`str.strip` is the identity
here".

The proof does **not** consume this `Ensures` (it is an **A-reference**, not
A-consumed): the numeric postcondition `ToSeq(Result()) == numeric_sep_of(sym)`
discharges by functional congruence — the impl and the oracle call the *same*
`trimmed(s)` and take the same `is_spacing_only` branch, so they agree for *any*
value of `trimmed`. (Verified empirically with the verifier: replacing the
axiom's `Ensures` with `Ensures(True)`, or even with a contradictory always-empty
`Ensures`, still yields "Verification successful".) The axiom is load-bearing
only via **refinement fidelity**: the oracle's spacing-only test models the real
`str.strip` behaviour exactly because `trimmed` ≈ `str.strip`, which is what G-AX
validates. (For intuition, the discriminating consequence the *gold* relies on is
that the thin-space selector `\,` — code points `92, 44`, both visible ASCII —
satisfies `no_outer_blank`, so the real `str.strip` leaves it unchanged and the
numeric separator for `mul_symbol="\\,"` is the centred dot.)

**Soundness check (G-AX):** `axiom_check.py` runs the real `str.strip()` on the
seven recognised spacing tokens, whitespace-padded variants built from the full
stripped-whitespace class, all-whitespace tokens, and ~80 000 randomized fuzz
strings (ASCII spacing/command alphabet + astral-plane code points). For every
input whose model predicate `no_outer_blank` is True it asserts
`s.strip() == s`; it never finds a violation. It also pins the discriminating
fact `"\\,".strip() == "\\,"`. Exit 0 iff sound. It imports nothing
repo-specific (`str.strip` is a builtin — the same operation the patch calls).
