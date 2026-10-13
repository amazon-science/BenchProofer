# refinement.md — psf__requests-1142

Operation correspondence between `implementation_prepare_content_length`
(Solution.lean) and the gold `patch.diff`. Tags: **R** (type refinement),
**A-consumed** (proof uses an axiom's property), **A-reference** (deep model
validated == real callee by G-AX), **I** (identical concrete op).

## Modeled function: `prepare_content_length`

The function mutates the `Content-Length` header of a prepared request. The
POST-patch Python body is:

```python
def prepare_content_length(self, body):
    if hasattr(body, 'seek') and hasattr(body, 'tell'):
        body.seek(0, 2)
        self.headers['Content-Length'] = str(body.tell())
        body.seek(0, 0)
    elif body is not None:
        self.headers['Content-Length'] = str(len(body))
    elif self.method not in ('GET', 'HEAD'):
        self.headers['Content-Length'] = '0'
```

The modeled output is the post-state of the single touched header slot
(`Option String`); the input carrier is
`(method : String, pre : Option String, body : Option Nat)` per mapping.md,
where `pre` is that same slot's PRE-call state (the function never clears the
slot, so on the no-write path the pre-state is retained and must be modeled).

| # | `implementation_prepare_content_length` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `body : Option Nat` (`none`/`some n`) | the `body` argument: `None`, a measurable value, or a seekable stream | R | The two length-producing branches (`str(body.tell())`, `str(len(body))`) both observably yield the decimal content length; the refinement collapses the seek/tell vs. len distinction to the length `n` (see mapping.md). G-CONF realises BOTH branches and confirms they agree, then compares to the shadow. |
| 2 | `let mut clen : Option String := pre` | the header slot's state before any assignment in this function (the unconditional `'0'` pre-set is REMOVED by the patch, so the slot enters the function holding its pre-call value — possibly a user-supplied header copied in by `prepare_headers`) | R / I | initial value of the modeled header slot = its pre-state `pre`. The patch's key change is precisely deleting the leading `self.headers['Content-Length'] = '0'`; afterwards the function performs no write on the no-body GET/HEAD path, so the slot retains `pre` there. |
| 3 | `match body with \| some n => clen := some (toString n)` | `if hasattr(seek/tell): … str(body.tell())` **and** `elif body is not None: … str(len(body))` | R / I | when a body is present, the header is its content length rendered in decimal (`toString n` ↔ `str(...)`). Both real branches map here under refinement #1. |
| 4 | `\| none => if method ≠ "GET" ∧ method ≠ "HEAD" then clen := some "0"` | `elif self.method not in ('GET', 'HEAD'): self.headers['Content-Length'] = '0'` | I | identical concrete op: with no body, set the literal `"0"` exactly for methods outside `{GET, HEAD}`; otherwise perform NO write, leaving the slot at its pre-call value `pre`. This is the line ADDED by the patch and the discriminating behavior. |
| 5 | `return clen` | the resulting `self.headers` Content-Length slot (present value or absent) | R | the modeled output is the post-state of that one header slot (`Option String`); `none` ⟺ key absent. |

No op in `implementation_prepare_content_length` is changed-inexpressible: the
whole behavior is a finite case analysis modeled directly. There is **no consumed
axiom** and **no opaque callee** (the `axioms` region is empty); the proof
discharges by case analysis on `body` and on the `method ∈ {GET,HEAD}` decision
(no induction needed). The R/I legs are mechanically refuted by G-CONF over
≥10⁵ fuzzed inputs (both body realisations); there are no A legs (G-AX = skip).

## Out-of-scope gold-patch edits

None — the gold patch edits only `prepare_content_length`, a single
independently-observable fixed behavior. `patch.diff` is the gold verbatim.
