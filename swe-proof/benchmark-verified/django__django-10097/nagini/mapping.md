# mapping.md — django__django-10097

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b9cf764be62e77b4777b3a75ec256f6209a57671`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
compiled matcher the deep model is validated against by G-AX).

Repo file under change: `django/core/validators.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validate_authsegment(seg)` | the user:pass authentication group of `URLValidator.regex`, `django/core/validators.py:97` (the `(?:...@)?` alternative, body `\S+(?::\S*)?` pre-patch → `[^\s:@/]+(?::[^\s:@/]*)?` post-patch) | the modeled changed function: the decision "is this authentication segment well-formed" |
| `accepts(s)` *(deep model — A-reference)* | the compiled userinfo group `[^\s:@/]+(?::[^\s:@/]*)?` (post-patch `django/core/validators.py:97`), matched under `re.IGNORECASE` | pure spec: the acceptance predicate; the deep model of the changed matcher, validated `accepts == real-compiled-group.fullmatch` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `is_uchar(c)` | the character class `[^\s:@/]` | pure spec: a single authentication character (not whitespace / `:` / `@` / `/`). `is_whitespace` enumerates the full Unicode `\s` class (the 29 code points `{9..13,32, 0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000}`) so `not is_whitespace(c)` is exactly `[^\s]`. |
| `is_whitespace(c)` | `\s` (Python `re`, default `re.UNICODE`) | pure spec: the full Unicode whitespace class, enumerated to the exact 29 code points the engine matches |
| `body_ok(s)` | "every code point of the segment is in `[^\s:@/]` or is the one permitted separator `:`" | pure spec: front-recursive body predicate |
| `colons(s)` | the single optional `:` separator in `(?::[^\s:@/]*)?` (at most one) | pure spec: count of separator colons |

The pre-patch repo symbol the change replaces (for the refinement audit, not
referenced from the consumer spec view): the userinfo body `\S+(?::\S*)?`
(`validators.py:97`), whose character class `\S` excludes only whitespace.

`URLValidator.regex` is compiled by `_lazy_re_compile(..., re.IGNORECASE)`
(`validators.py:95-101`, flags from `RegexValidator.__init__`,
`validators.py:50`). The surrounding URL matching (`RegexValidator.__call__`,
`validators.py:52-60`, calls `self.regex.search(str(value))`) anchors the whole
pattern with `^...\Z`; the userinfo group either matches empty (no
authentication) or consumes a segment ending in `@`. The modeled operation is
the acceptance of that segment's content (the text before the `@`), which is a
full match of the inner group.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the authentication segment, the substring of `str(value)` between `://` and the terminating `@`) | `List[int]` of Unicode code points | `s[k]` ↔ `seg[k] == ord(s[k])`; `len(s)` ↔ `len(seg)`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `len`/`[i]`/`drop`/`take` mirror `str` `len`/index/slice |
| regex full match of the userinfo group on the segment | `accepts(ToSeq(seg)) : bool` | a `re.fullmatch` of `[^\s:@/]+(?::[^\s:@/]*)?` ↔ `accepts` returning `True` (validated by axiom_check.py over boundary + 100k fuzz) |
| `re.IGNORECASE` flag | (no effect on the userinfo class) | `[^\s:@/]` and `:` are case-insensitivity-invariant; `IGNORECASE` does not change which code points the class admits. Recorded so G-AX compiles with the same flag. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `accepts` deep model ↔ the compiled userinfo group (A-reference)

**Reference:** the post-patch compiled group `re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?', re.IGNORECASE)`.
The changed matching operation is modelled **deeply** by the `@Pure` predicates
`accepts` / `body_ok` / `colons` / `is_uchar` in the `pure` region; there is
**no consumed `@ContractOnly` axiom**. The deep model is validated equal to the
real compiled matcher out-of-band by axiom_check.py (G-AX).

Characterization (proven equivalent to `fullmatch` over the full
Unicode-whitespace per-code-point sweep, 188 boundary cases, and 100k random
inputs): the group `[^\s:@/]+(?::[^\s:@/]*)?` full-matches a segment
`s` **iff**

  * `s` is non-empty, **and**
  * every code point of `s` other than at most one `:` is in `[^\s:@/]`
    (i.e. is none of whitespace, `:`, `@`, `/`), **and**
  * `s` does not begin with `:` (the leading `[^\s:@/]+` user run is non-empty).

That is exactly `accepts(s) = len(s) > 0 ∧ body_ok(s) ∧ colons(s) ≤ 1 ∧ s[0] ≠ ':'`.

**Flag dependency:** the validator compiles with `re.IGNORECASE`; the userinfo
character class `[^\s:@/]` is unaffected by case folding, so the
characterization holds under that flag. axiom_check.py compiles with the same
flag.

**`\s` is Unicode-aware — the model matches it exactly:** with the default
`re.UNICODE` semantics, `\s` matches ASCII whitespace PLUS the C1 / separator
code points. The deep model excludes the **entire** Unicode whitespace class via
`is_whitespace` (29 code points: `{9..13, 32, 0x1c..0x1f, 0x85, 0xa0, 0x1680,
0x2000..0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000}`), so `is_uchar` is the
exact complement of `[\s:@/]` — the equivalence to the real matcher is
**universal**, not merely "equal on ASCII". This set is the same 29 code points
`re` matches for `\s` in the pinned eval container (Python 3.5), verified
in-container. (Earlier the model excluded only the six ASCII whitespace code
points, so it disagreed with the matcher on the 23 non-ASCII whitespace code
points — e.g. `accepts('foo\xa0bar')` was wrongly `True`; the matcher rejects
it. Tightening `is_uchar` to the full `\s` set closes that hole.)

**Soundness check (G-AX):** `axiom_check.py` compiles the real userinfo group
and asserts `accepts == group.fullmatch` on 188 boundary inputs (each forbidden
char — including every non-ASCII whitespace code point — alone/doubled and
embedded in user/password runs; the issue's discriminating segments `foo/bar`,
`foo@bar`, `foo:bar:baz`, `foo:bar@baz`, `foo:bar/baz`; the explicit non-ASCII
whitespace witnesses `foo\xa0bar`, `user　pass`; the changed valid/invalid
encoded segments), PLUS a programmatic per-code-point sweep over EVERY one of the
29 Unicode-whitespace code points (alone and embedded), PLUS 100 000 randomized
fuzz strings drawn from an alphabet that includes the full Unicode-whitespace
block. Exit 0 iff every observation agrees (verified RC=0 in the pinned
container, Python 3.5). It imports only the standard-library `re` (the engine
the gold patch's compiled regex uses); nothing repo-specific.
