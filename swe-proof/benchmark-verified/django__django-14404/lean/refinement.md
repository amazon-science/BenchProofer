# refinement.md — django__django-14404

Maps every op in `implementation_catchAll` to its `patch.diff` counterpart.
Tags: **R** type refinement / **A-consumed** proof uses callee axiom /
**A-reference** deep model validated == real callee (G-AX) / **I** identical op.

| # | Lean impl op | patch.diff / repo counterpart | tag |
|---|---|---|---|
| 1 | `if appendSlash && !(url.endsWith "/")` | `if settings.APPEND_SLASH and not url.endswith('/')` | R (Bool ↔ truthy setting; `endsWith` ↔ `endswith`) |
| 2 | `let urlconf := req.urlconf` | `urlconf = getattr(request, 'urlconf', None)` | R (`Urlconf` opaque carrier ↔ urlconf object/None) |
| 3 | `resolveLoc (req.routingPath ++ "/") urlconf` | `resolve('%s/' % request.path_info, urlconf)` | A-reference (unchanged callee `resolve`; signature-only `opaque`, no consumed property — appears identically in spec; arg built from `path_info` both pre/post-patch) |
| 4 | `match … | some m => … | none => …` | `try: match = resolve(...) except Resolver404: pass else:` | R (`Option`/match ↔ success-vs-`Resolver404`) |
| 5 | `if m.shouldAppend` | `if getattr(match.func, 'should_append_slash', True)` | R (Bool ↔ truthy attr w/ default True) |
| 6 | `return Outcome.redirect (req.visiblePath ++ "/")` | `return HttpResponsePermanentRedirect('%s/' % request.path)` | **R — THE FIX**: redirect target is `request.path` (visible, incl. script name), NOT `request.path_info`. Pre-patch impl uses `routingPath` (= `path_info`); this is the discriminating clause. |
| 7 | `return Outcome.notFound` (fallthrough / no match / shouldAppend false) | `raise Http404` | R (`Outcome.notFound` ↔ `Http404`) |

## Notes

- No changed op is left inexpressible: the entire behavior change (op #6) is
  modeled deeply and concretely as a string-construction difference between two
  request-path fields. Nothing is axiomatized away.
- `resolveLoc` (op #3) is the one opaque callee. It is UNCHANGED by the patch and
  occurs identically in spec and impl, so it is an A-reference with no consumed
  `_prop` axiom (axioms region declares the signature only). G-AX is therefore a
  skip stub (no callee property is consumed by the proof).
- G-CONF differential-tests the R/I legs (ops 1,2,4,5,6,7) by building the shadow
  of the post-patch impl and diffing against an independent reconstruction of the
  patched `catch_all_view` redirect behavior. The `resolve` A-reference is held
  fixed (same success/failure decision feeds both sides), so the differential
  isolates the redirect-target leg.
- The prepatch (`Solution_prepatch.lean`) flips op #6 back to
  `req.routingPath ++ "/"` — the real bug — making `correct_catchAll`
  unclosable on the discriminating clause (G-DIFF).
