# refinement.md — django__django-14404

The operation-by-operation correspondence between `model.py`'s implementation
(the `slash_redirect_target` impl region + the deep `with_trailing_slash`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The slash-appending redirect — `catch_all_view()` (`django/contrib/admin/sites.py:419-430`)

Gold hunk:
```
     def catch_all_view(self, request, url):
         if settings.APPEND_SLASH and not url.endswith('/'):
             urlconf = getattr(request, 'urlconf', None)
-            path = '%s/' % request.path_info
             try:
-                match = resolve(path, urlconf)
+                match = resolve('%s/' % request.path_info, urlconf)
             except Resolver404:
                 pass
             else:
                 if getattr(match.func, 'should_append_slash', True):
-                    return HttpResponsePermanentRedirect(path)
+                    return HttpResponsePermanentRedirect('%s/' % request.path)
         raise Http404
```

The pre-patch code computed one local `path = '%s/' % request.path_info` and
reused it BOTH as the `resolve` argument and as the redirect target. The fix
removes that shared local: the `resolve` argument stays `'%s/' % request.path_info`
(unchanged — application-relative routing must use the prefix-stripped path),
while the redirect target is rebuilt from `request.path` (which carries the
deployment prefix). The two `'%s/' % request.path_info` references are
behaviour-equal to the old shared local (resolve sees the same string); the
single observable change is the redirect-target source.

| # | model.py impl op (`slash_redirect_target`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | `append_slash_enabled and not url_has_trailing_slash` outer guard | `if settings.APPEND_SLASH and not url.endswith('/')` | R | the two booleans ↔ the setting and the `endswith` predicate evaluated at the call site (mapping.md §2); `and` / `not` are identical control. |
| A2 | (no node — `urlconf` is not behaviour the redirect target depends on) | `urlconf = getattr(request, 'urlconf', None)` | I (elided) | a plain attribute read passed only to `resolve`; it never reaches the redirect target, so it is not modelled. (No tested behaviour depends on it independently.) |
| A3 | `slash_form_resolves` gate on the inner branch | `try: match = resolve('%s/' % request.path_info, urlconf) except Resolver404: pass else:` | R | the resolve outcome reduces, at this site, to the boolean "did the slash-form resolve" gating the `else` branch (mapping.md §2, §3). The `resolve` argument is UNCHANGED by the patch (still `request.path_info`-derived), so this gate is identical pre/post fix — it is *not* where the bug lives. |
| A4 | `target_view_opts_in` gate | `if getattr(match.func, 'should_append_slash', True)` | R | the per-view opt-in flag (default True) ↔ the boolean (mapping.md §2). |
| A5 | `result = list(full_path); result.append(47); return result`, i.e. `Result() == full_path + [47]` | `return HttpResponsePermanentRedirect('%s/' % request.path)` | **R + I (the FIX)** | the FIX. The redirect target is `'%s/' % request.path` — the full path plus a trailing `'/'`. Modelled deeply: `request.path` ↔ `full_path` (R, `str`↔`List[int]`, mapping.md §2/§2.1); `'%s/' %` ↔ append of code point 47 (`with_trailing_slash`, R); `HttpResponsePermanentRedirect(...)` ↔ identity on the target URL `Result()` (R, the 301 wraps the URL unchanged). This is the single observable change: the base is `request.path` (with prefix), not `request.path_info`. |
| A6 | `raise NotFound()` (fall-through) | `raise Http404` | R | the not-found signal; `Http404` ↔ user-defined `NotFound` (builtin-exception `Exsures` banned, mapping.md §2). Reached on the negation of the four-guard conjunction, exactly as `raise Http404` is reached when any guard fails or resolve raises. |

The discriminating content of the change — the redirect base is
`request.path` (prefix-carrying) rather than `request.path_info` (prefix-
stripped) — lives in step **A5**: `ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))`
(model) ⇔ `HttpResponsePermanentRedirect('%s/' % request.path)` (real). The
pre-patch built the target from `request.path_info`; `model_prepatch.py`
reproduces that (`result = list(app_relative_path); result.append(47)`) and
**fails** the postcondition
`ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))`, which is exactly
the spec sensing the change (G-DIFF).

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: at step A5 it builds the
redirect target from `app_relative_path` (the prefix-stripped `request.path_info`)
instead of `full_path`. With the byte-identical frozen spec it **fails**
verification on the postcondition
`Ensures(ToSeq(Result()) == with_trailing_slash(ToSeq(full_path)))`
(`model_prepatch.py:75` — *Assertion (ToSeq(Result()) ==
with_trailing_slash(ToSeq(full_path))) might not hold*). That is precisely the
behaviour the F2P tests observe:

- `test_missing_slash_append_slash_true_script_name` sets `SCRIPT_NAME='/prefix/'`
  and asserts the redirect goes to `'/prefix' + known_url` (i.e. the prefix is
  present in the target).
- `test_missing_slash_append_slash_true_force_script_name` sets
  `FORCE_SCRIPT_NAME='/prefix/'` and asserts the same.

Because `request.path` carries the prefix and `request.path_info` does not
(mapping.md §2.1), only a target built from `request.path` includes `/prefix`.
The spec is therefore strong enough that no implementation building the target
from the prefix-stripped path can verify (spec sees the bug).

The companion clause
`Ensures(append_slash_enabled and not url_has_trailing_slash and slash_form_resolves and target_view_opts_in)`
plus the `Exsures(NotFound, …)` on the negation pin the control flow exactly:
a redirect is returned on EXACTLY the four-guard conjunction and the not-found
signal is raised otherwise. This keeps the spec faithful to the unchanged
guard logic (the P2P tests `test_missing_slash_append_slash_false`,
`test_missing_slash_append_slash_true_unknown_url`,
`test_missing_slash_append_slash_true_non_staff_user`,
`test_single_model_no_append_slash`, etc. observe exactly these branches), so a
wrong impl cannot satisfy the spec by redirecting when it should 404 or vice
versa, and cannot satisfy it vacuously by overwriting a read-only input
(both `full_path` and `app_relative_path` are held at `Acc(..., 1/2)`,
directive 5).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or an elision of behaviour no tested path depends on
(A2). The one operation that genuinely *changed* — which path the redirect
target is built from — is modelled **deeply** as an **R + I** step (the same
`'%s/' %` append, with the base refined from the `request.path` code-point
list; step A5), NOT hidden behind an axiom about the function under change.
There is therefore **no consumed axiom** and **no A-reference** in the Nagini
proof: the changed string operation (`full_path + [47]`) is spelled out and
verified directly. The unchanged callees (`resolve`, `getattr(...should_append_slash...)`,
`HttpResponsePermanentRedirect`, `Http404`) are reduced to the booleans /
sequences / identities they contribute at this site (mapping.md §3); none is
the function under change, and none needs an over-approximating contract for
the proof. `axiom_check.py` (G-AX) validates the one load-bearing deep-modelling
fact — that `request.path` carries the prefix and `request.path_info` does not
— against the real `WSGIRequest` path construction.

## D. verify(model) ⇒ resolved

`slash_redirect_target` verifies only if (A5) its returned target equals
`full_path + [47]` (the full path with a trailing slash) and (A1/A3/A4/A6) it
returns on exactly the four-guard conjunction and raises otherwise. By R
(`str` ↔ `List[int]`; `request.path` ↔ `full_path`; `'%s/' %` ↔ append 47;
`HttpResponsePermanentRedirect`/`Http404`/the guards ↔ their refined carriers)
the verified path equals the gold branch
`return HttpResponsePermanentRedirect('%s/' % request.path)` /
`raise Http404` on the tested inputs. By the G-AX check, the real `request.path`
is the prefix-carrying path the gold target is built from, so the model's
`full_path` base is exactly `request.path`. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: there is no consumed axiom (so axiom soundness is vacuous here; the
G-AX check instead corroborates the deep-modelling premise) and refinement
fidelity (this document, G-EQ).
