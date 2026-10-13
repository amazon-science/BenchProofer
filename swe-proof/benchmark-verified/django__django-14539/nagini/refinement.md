# refinement.md — django__django-14539

The operation-by-operation correspondence between `model.py`'s implementation
(the `trim_trailing_punct` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model / a callee summary is validated against the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed site — `urlize.trim_punctuation` trailing-trim block

Gold hunk (`django/utils/html.py`, inside the `if middle_unescaped != stripped:`
branch):
```
- trail = middle[len(stripped):] + trail
- middle = middle[:len(stripped) - len(middle_unescaped)]
+ punctuation_count = len(middle_unescaped) - len(stripped)
+ trail = middle[-punctuation_count:] + trail
+ middle = middle[:-punctuation_count]
```

| # | model.py impl op (`trim_trailing_punct`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `middle: List[int]`, `trail: List[int]` | the `str` locals `middle`, `trail` of `trim_punctuation` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| 2 | `decoded_len`, `kept_len` int parameters | `len(html.unescape(middle))` (`middle_unescaped`) and `len(html.unescape(middle).rstrip(...))` (`stripped`) | A-reference | the two unchanged callees enter only as their length outputs; the model assumes only `0 <= decoded_len <= len(middle)` and `0 <= kept_len <= decoded_len` (mapping.md §3.1), validated against the real `html.unescape`+`rstrip` by axiom_check.py / G-AX. NOT a consumed axiom — there is no `@ContractOnly` the proof's `Ensures` rely on; the facts are encoded as the function's `Requires`. |
| 3 | `Requires(kept_len < decoded_len)` | the enclosing `if middle_unescaped != stripped:` guard | I | `middle_unescaped != stripped` ⇔ `rstrip` removed ≥1 char ⇔ `len(stripped) < len(middle_unescaped)` ⇔ `kept_len < decoded_len` (mapping.md §1). |
| 4 | `punctuation_count = decoded_len - kept_len` | `punctuation_count = len(middle_unescaped) - len(stripped)` | I | identical integer arithmetic on the refined-type lengths. |
| 5 | `split = len(middle) - punctuation_count` | (implicit in `middle[-punctuation_count:]` / `middle[:-punctuation_count]`) | R | Python negative-index slicing `s[-k:]`/`s[:-k]` for `0 < k <= len(s)` equals `s[len(s)-k:]`/`s[:len(s)-k]`; the model uses the equivalent non-negative `split` (mapping.md §2). |
| 6 | `moved = middle[split:]`; `new_trail = moved + trail` | `trail = middle[-punctuation_count:] + trail` | R+I | slice (`ToSeq.drop(split)`, R) then list `+` (I); identical operation under the carrier bijection. |
| 7 | `new_middle = middle[:split]` | `middle = middle[:-punctuation_count]` | R+I | slice (`ToSeq.take(split)`, R); identical. |
| 8 | `return new_middle, new_trail` | the reassigned `middle`, `trail` carried out of the block (`return lead, middle, trail`) | R | the block's net effect on the `(middle, trail)` pair; `lead` and `trimmed_something` are untouched by this hunk and outside the modeled operation. |

The discriminating content of the change lives in step 6/7's **boundary**:
the gold moves the last `punctuation_count = decoded_len - kept_len` code points
of the ENCODED `middle` (boundary `split = len(middle) - punctuation_count`),
whereas the pre-fix code used `len(stripped) = kept_len` — an index into the
DECODED form — as the boundary. The two agree only when `len(middle) ==
decoded_len` (no entities). `model_prepatch.py` transcribes the pre-fix
slicing (`moved = middle[kept_len:]`, `new_middle = middle[:kept_len -
decoded_len]`) and **fails** the postcondition

  `ToSeq(Result()[1]) == ToSeq(middle).drop(len(middle) - (decoded_len -
  kept_len)) + ToSeq(trail)`

(equivalently the lossless-split clause) — exactly the spec sensing the change
(G-DIFF). Note the pre-fix `new_middle` is *identical* to the gold `new_middle`
(`middle[:kept_len - decoded_len] == middle[:-punctuation_count]`), so the only
observable behavioural difference — and the only failing clause — is in the
moved suffix `trail`, which is precisely the bug the issue reports (extra `lt`
characters leaking into the trailing text).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — which boundary of `middle` to cut at — is modeled **deeply** (the
non-negative `split` arithmetic and the two slices spelled out in the impl, and
pinned by the postconditions over `PSeq` `take`/`drop`), not hidden behind an
axiom about the function under change. There is **no consumed `@ContractOnly`
axiom**: the unchanged decode/strip callees appear only as the A-reference
length summaries `decoded_len`/`kept_len`, whose bounds G-AX validates against
the real `html.unescape`+`rstrip`.

## verify(model) ⇒ resolved

`trim_trailing_punct` verifies only if its output is the lossless split of
`middle` at the boundary `len(middle) - (decoded_len - kept_len)`, moving
exactly `decoded_len - kept_len` code points (the count derived from the decoded
form) onto the front of `trail`. By R (str ↔ List[int], negative ↔ non-negative
slice) the verified block equals the gold `middle[-punctuation_count:]` /
`middle[:-punctuation_count]` assignment on every `str` input; by G-AX
(axiom_check.py) the real `html.unescape`+`rstrip` satisfy the length bounds the
proof assumed AND feeding their real outputs into the model reproduces the gold
block exactly. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee summaries — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: callee-summary soundness (G-AX) and refinement fidelity (this
document, G-EQ).
