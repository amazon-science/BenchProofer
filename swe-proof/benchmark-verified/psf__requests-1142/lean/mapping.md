# mapping.md — psf__requests-1142

## Modeled function

| Lean | Python | file:line @ base_commit `22623bd8c2` |
|---|---|---|
| `implementation_prepare_content_length` / `problem_spec_prepare_content_length` / `correct_prepare_content_length` | `PreparedRequest.prepare_content_length(self, body)` — set the message-length header on a prepared request | `requests/models.py:388-394` (post-patch: the unconditional `headers['Content-Length'] = '0'` is replaced by a final `elif self.method not in ('GET','HEAD')` branch) |

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `self.method` (a `str`, already upper-cased by `prepare_method`) | `method : String` | the normalized HTTP verb. `prepare_method` upper-cases the method *before* `prepare_content_length` runs (`prepare()` ordering, models.py:220 vs :224), so the `('GET','HEAD')` comparison sees the normalized verb — the model compares against the upper-case literals `"GET"`/`"HEAD"`. |
| `self.headers['Content-Length']` slot **before** the call (present value, or absent) | `pre : Option String` | `some s` ⟺ the header is already set to string `s` (e.g. supplied by the user and copied in by `prepare_headers`, which runs before `prepare_body`→`prepare_content_length`); `none` ⟺ the header key is absent before the call. The post-patch function never *clears* the slot: on the no-body GET/HEAD path NO branch fires, so the slot retains its pre-call value — the pre-state is therefore part of the modeled input. |
| `body` argument: `None`, or a measurable value (`str`/`bytes`, has `len`), or a seekable stream (has `seek`+`tell`) | `body : Option Nat` | `none` ⟺ `body is None`; `some n` ⟺ a body whose content length is `n`. Both real length-producing branches (`str(body.tell())` and `str(len(body))`) collapse to the same observable — the decimal content length — so the abstract carrier is the length `n : Nat`. |
| `self.headers['Content-Length']` slot after the call (present value, or absent) | `result : Option String` | `some s` ⟺ the header is set to string `s`; `none` ⟺ the header key is absent. |
| `str(n)` (decimal rendering of a length) | `toString (n : Nat)` | `toString` on `Nat` yields the decimal numeral with no separators/sign — matches Python `str(int)` for non-negative `n`. |

The real method mutates `self.headers` in place (a `dict`). Only the
`Content-Length` key is ever touched by this function, so the modeled state is
exactly that one slot: its pre-state is the input `pre : Option String` and its
post-state is the output `result : Option String`; every other header is
unchanged by frame discipline (directive 5) and is not part of the modeled
state. Modeling the pre-state is required for faithfulness: for `body is None`
and `method ∈ {GET, HEAD}` the post-patch code writes nothing, so a pre-existing
user-supplied `Content-Length` value is retained (reachable via the public API —
`prepare_headers` copies user headers before `prepare_body` runs).

## Callee provenance / flag deps

- **No UNCHANGED callee is invoked** by the modeled behavior. The body-length is
  obtained in the real code via `body.tell()` (seekable stream) or `len(body)`
  (measurable value); both are abstracted to the length `n : Nat` (a type
  refinement, not a callee). Hence the `axioms` region declares no `opaque` and
  the proof needs no `_prop` axiom — **G-AX = skip**.
- **Flag/branch dependency:** the zero-length-suppression is gated on the
  normalized method being one of `GET`/`HEAD`. G-CONF fuzzes all common verbs
  (incl. lower-case spellings, which are NOT suppressed — only the normalized
  upper-case verbs are), both body realisations, and pre-seeded vs. absent
  pre-call `Content-Length` slot values.

## Out-of-scope edits in the same gold patch

None. The gold patch touches only `prepare_content_length`; there is a single
independently-observable fixed behavior (no body + GET/HEAD ⇒ header absent).

## G-CONF fuzz seed

`conf_seed = 1142` (pinned; see conformance_check.py and meta.json).
