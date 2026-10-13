# refinement.md — django__django-12193

Maps every operation in `implementation_buildInputContext` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom),
**A-reference** (deep model, validated == real callee by G-AX/G-CONF), **I**
(identical concrete op).

## patch.diff (post-patch `CheckboxInput.get_context`)
```python
def get_context(self, name, value, attrs):
    if self.check_test(value):
        attrs = {**(attrs or {}), 'checked': True}
    return super().get_context(name, value, attrs)
```
`super().get_context` ultimately exposes
`context['widget']['attrs'] = build_attrs(self.attrs, attrs)
                            = {**self.attrs, **(attrs or {})}`.

## Operation correspondence

| # | Lean op (`implementation_buildInputContext`) | patch.diff op | tag |
|---|---|---|---|
| 1 | `attrs : Option AttrMap` binder | the `attrs` parameter (`dict` or `None`) | **R** — `None ↔ none`, a `dict ↔ some (assoc list)`; key→Bool payload bijection (see mapping.md). |
| 2 | `let mut cur := attrs.getD []` | `(attrs or {})` materialized into the local name | **R** — `None`/empty `↔ []`; Python `dict` ↔ insertion-ordered assoc list. |
| 3 | `if checkTest then` | `if self.check_test(value):` | **R** — the unchanged callee's Boolean result is supplied as the input `checkTest`. |
| 4 | `cur := dictSet cur markerKey true` | `{**(attrs or {}), 'checked': True}` (the `'checked': True` overlay onto a FRESH dict bound to the local name) | **A-reference** — `dictSet`/last-write-wins models Python dict key assignment on a fresh object; validated by G-CONF. The crux of the fix: the write lands on a fresh local, not the caller's object. |
| 5 | `mergeDict base cur` (in the returned `contextAttrs`) | `build_attrs(self.attrs, attrs) = {**self.attrs, **(attrs or {})}` inside `super().get_context` | **A-reference** — `mergeDict` models the `{**base, **extra}` spread (extra wins on collision); validated by G-CONF. |
| 6 | `callerAttrs := attrs` (returned unchanged) | the caller's `attrs` object, observed after the call — untouched because the patched code rebinds its local name to a fresh dict | **R/I** — referential transparency makes the read-only frame the identity; this is the behavioral discriminator (frame, directive 5). Pre-patch mutated it in place; post-patch does not. |

No changed op is left inexpressible. No consumed axiom is used (the changed ops
are modeled deeply as A-reference); `axiom_check.py` is therefore a skip stub and
the R/A-reference legs are mechanically refuted by `conformance_check.py`
(G-CONF).

## The hard subtlety (aliasing in a pure language)
Lean is referentially transparent: an in-place dict mutation cannot occur, so the
bug cannot be reproduced by "mutating a value". The fix is entirely about whether
the caller's dict OBJECT is observed mutated after the call. We model this by
making the caller-visible attribute object an explicit output component
`callerAttrs` and pinning it to the input (`result.callerAttrs = attrs`, directive
5 frame). The post-patch impl returns `attrs` untouched; the pre-patch impl
returns `attrs` with the marker written through (`Solution_prepatch.lean`), which
violates that clause exactly on the FAIL_TO_PASS case.
