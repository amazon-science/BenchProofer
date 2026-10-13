# mapping.md — psf__requests-5414

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 39d0fdd9096f7dceccbc8f82e1eda7dd64717a8e`, states the Lean↔Python
type bijection (used by G-CONF and G-AX), and records callee provenance.

Repo file under change: `requests/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateAsciiHostLabel (host : List Char) → Bool` | the leading-label acceptance step inside `PreparedRequest.prepare_url(self, url, params)` — `requests/models.py:360` (the `elif host.startswith(...)` guard at body line `requests/models.py:406`, on the all-ASCII branch) | the modeled changed decision: along the all-ASCII host path, accept the host (proceed) or reject it (signal an invalid-URL condition). |
| `startsWithInvalidLabel (host : List Char) → Bool` | the post-patch membership test `host.startswith((u'*', u'.'))` — `requests/models.py:406` | pure spec helper: does the host open with the wildcard `*` (U+002A) or the separator `.` (U+002E). |
| `hostAccepted (host : List Char) → Bool` | the post-patch accept/reject outcome of the `elif` guard (accept iff the guard does not fire) | pure spec predicate: the post-patch decision, expressed structurally over the host's leading code point. |
| `isAsciiHost (host : List Char) → Bool` *(deep model — A-reference)* | `unicode_is_ascii(u_string)` — `requests/_internal_utils.py:30`, called as `unicode_is_ascii(host)` at `requests/models.py:401` | the unchanged community predicate that **selects** the all-ASCII code path (`if not unicode_is_ascii(host): ... elif host.startswith(...)`); modeled deeply and used only in a `require` to scope the decision. Validated `isAsciiHost == unicode_is_ascii` by axiom_check.py (G-AX), an A-reference, NOT a consumed axiom. |

The repo line the patch CHANGES (for the refinement audit; never referenced from
the consumer spec view): the guard literal goes from `host.startswith(u'*')` to
`host.startswith((u'*', u'.'))` at `requests/models.py:406`; on a fired guard the
constructor raises `InvalidURL('URL has an invalid label.')` at line 407.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `host: str` (the parsed host of the URL) | `host : List Char` (Unicode code points) | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `s[0]` ↔ `l.head?` (`some` iff non-empty); empty `str` `""` ↔ `[]`. |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact. The two needle characters are `'*'` = U+002A and `'.'` = U+002E. |
| `host.startswith((u'*', u'.'))` (str prefix test on single-char prefixes) | `host.head? == some '*' \|\| host.head? == some '.'` | `s.startswith(p)` for a one-character prefix `p` is exactly "`s` is non-empty and `s[0] == p`", i.e. `s.head? == some p`. The tuple form is the disjunction over the two one-character prefixes. |
| `ord(ch) < 128` for every char (i.e. `str.encode('ascii')` succeeds) | `isAsciiHost host` | `unicode_is_ascii(s)` returns `True` iff `s.encode('ascii')` does not raise, i.e. every code point is < 128. `isAsciiHost` is the front-recursive per-code-point conjunction of `c.toNat < 128`. |
| accept (host passes this guard, prepare_url proceeds) vs reject (`raise InvalidURL('URL has an invalid label.')`) | `out = true` (accept) vs `out = false` (reject) | the F2P/P2P tests observe only *whether `InvalidURL` is raised*, not its message. |
| `not host` empty guard at `models.py:394` (`if not host: raise InvalidURL(...)`) | `require host.length > 0` | a host reaching the `elif` has already passed the non-empty guard at line 394, so the modeled decision is scoped to non-empty hosts. |

`str` is modeled as `List Char` throughout (Lean indexing is total/sound). The
decision inspects only the leading code point (`head?`), so it is O(1) — no fold
over the body is needed for the acceptance decision itself.

## 3. Callee provenance

### 3.1 `isAsciiHost` deep model ↔ `unicode_is_ascii` (A-reference)
**Callee:** `requests._internal_utils.unicode_is_ascii(u_string)` (unchanged by
the patch). Source at base_commit:

```python
def unicode_is_ascii(u_string):
    assert isinstance(u_string, str)
    try:
        u_string.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False
```

`u_string.encode('ascii')` succeeds iff every code point is < 128. `isAsciiHost`
encodes exactly that per-code-point conjunction. It is **not** a consumed axiom:
it appears only in a `require` that scopes `validateAsciiHostLabel` to the
all-ASCII branch (the patched `elif` is reached only when
`not unicode_is_ascii(host)` is false). The proof of `validateAsciiHostLabel`
never unfolds `isAsciiHost`'s internal structure; it is carried as an opaque
precondition. G-AX validates the deep model equals the real callee.

**Why the branch matters:** the gold `elif host.startswith((u'*', u'.'))` is
reached only when `unicode_is_ascii(host)` is `True`. A non-ASCII host instead
takes the `if` branch (`_get_idna_encoded_host`), which is **unchanged** by the
patch and irrelevant to the modeled behaviour. Scoping to the ASCII branch is
necessary for `verify ⟹ correct`: the decision the patch changes only governs
ASCII hosts. (G-CONF restricts its fuzz inputs to ASCII hosts for the same
reason; non-ASCII hosts exercise a different, unchanged branch.)

### 3.2 No consumed axioms
The `axioms` region is empty. The acceptance decision is a pure property of the
host's leading code point (`startsWithInvalidLabel` / `hostAccepted`), modeled
deeply in the `pure` region. There is no consumed axiom and no dead axiom; the
only deep-model reference is the A-reference `isAsciiHost` (§3.1, G-AX-checked).
The `if not host:` empty guard and the non-ASCII `_get_idna_encoded_host` branch
are unchanged by the patch and are abstracted away (the first as
`require host.length > 0`, the second as scoping via `require isAsciiHost host`).

**Soundness check (G-AX):** `axiom_check.py` runs the real `unicode_is_ascii`
on boundary inputs (empty, the two needle chars, ASCII/non-ASCII mixtures, the
F2P/P2P host literals) plus randomized fuzz, asserting `isAsciiHost == real
unicode_is_ascii` on every input. Imports only the repo's
`requests._internal_utils`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`5414`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`startsWithInvalidLabel`/`hostAccepted` (R/I-tagged ops) to Python and diffs the
accept/reject decision against the post-patch repo behaviour. Inputs are
restricted to **all-ASCII** non-empty hosts (the `require`-scoped domain), since
the patched `elif` only governs that branch; non-ASCII hosts take the unchanged
IDNA branch and are out of scope for this decision.
