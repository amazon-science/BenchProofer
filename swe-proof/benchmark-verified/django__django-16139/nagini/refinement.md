# refinement.md — django__django-16139

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_action_reference` impl region and the deep `resolve` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, the proof uses the
axiom's `Ensures`, and **A-reference**, a deep model validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `UserChangeForm.__init__` (`django/contrib/auth/forms.py:162`)

Gold hunk (`django/contrib/auth/forms.py:166`):
```
- password.help_text = password.help_text.format("../password/")
+ password.help_text = password.help_text.format(
+     f"../../{self.instance.pk}/password/"
+ )
```

The only thing that changes is the **relative reference** substituted into the
help-text link's `href`. The model's `build_action_reference` produces that
reference as a list of path-segment steps; everything else (the `<a href="{}">`
markup, the `.format` insertion, the `mark_safe`/help-text wrapping) is unchanged
boilerplate that the F2P test does not observe except through the resolved
`href`.

| # | model.py impl op (`build_action_reference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `prefix: List[int]`, `token`, `current_action`, `pk`, `secondary_action` | the URL path of the current change page `/admin/<app>/<model>/<token>/change/` and `self.instance.pk` | R | URL path ↔ `List[int]` segment ids (mapping.md §2); `pk` ↔ `self.instance.pk`; `token` ↔ the access identifier (pk OR `to_field` value), quantified universally. |
| A2 | `result = [DOTDOT(), DOTDOT(), pk, secondary_action]` | the f-string `f"../../{self.instance.pk}/password/"` | R + I | two `..` steps, the pk segment, then the password-action segment ↔ `"../../" + str(pk) + "/password/"`. The list construction is the identical sequence of steps under the segment-id refinement. |
| A3 | `password.help_text.format(...)` inserting `result` into the `href` | the `.format(...)` call | omitted (R, identity) | `str.format` only substitutes the reference into the `{}` of `<a href="{}">`; the F2P test extracts exactly that `href` (`re.search('<a href="(.*?)">', ...)`). Modeled as returning the reference itself. |
| A4 | the resolution clause `resolve(prefix+[token]+[current_action], ToSeq(Result())) == prefix+[pk]+[secondary_action]` | the F2P obligation: `urllib.parse.urljoin(change_url_via_to_field, href) == reverse(password_change, args=(pk,))` | A-reference | the relative-reference RESOLVER is modeled **deeply**: `resolve` (the spelled-out segment fold in the `pure` region) IS hierarchical `..`-resolution. There is no consumed `urljoin` axiom — the proof never depends on one. The deep model is validated **== the real callee** out of band: G-AX (axiom_check.py) runs `urllib.parse.urljoin` on boundary+fuzz and asserts `resolve == urljoin` on the bundle's domain, plus the end-to-end token/pk witnesses. (mapping.md §3.) |

The discriminating content of the change — the resolved password URL must be
keyed by the **primary key**, independent of the access token — lives in the
postcondition
`resolve(prefix+[token]+[current_action], rel) == prefix+[pk]+[secondary_action]`,
which is quantified over **all** `token`. The pre-patch reference `[.., sa]`
(`"../password/"`) resolves to `prefix+[token]+[secondary_action]`
(TOKEN-keyed); `model_prepatch.py` reproduces that and **fails** the
postcondition exactly when `token != pk` — which is the access-via-`to_field`
scenario the F2P test exercises. That is the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation whose RESULT
genuinely changed — the relative reference built into the link — is modeled
directly as the list construction (A2, R+I). The unchanged callee whose
semantics makes the fix correct — relative-reference resolution
(`urllib.parse.urljoin`) — is modeled **deeply** (`resolve`, an **A-reference**
validated by G-AX), not hidden behind a consumed axiom: there is **no consumed
`@ContractOnly` axiom** in this bundle. (No dead axiom; no over-claim.)

## C. verify(model) ⇒ resolved

`build_action_reference` verifies only if the reference it returns resolves
(under `resolve`) to the pk-keyed target for **every** access token (A4). By R
(URL path ↔ segment ids; `.format`/markup identities) the verified reference
equals `f"../../{pk}/password/"` inserted into the `href`, exactly the gold
patch's expression. By G-AX the deep model `resolve` equals the real
`urllib.parse.urljoin` (A-reference) on the bundle's domain, and the
end-to-end witnesses confirm the gold reference lands on the pk-keyed password
page for every token while the pre-patch reference does not. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited resolver — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom/deep-model soundness
(G-AX) and refinement fidelity (this document, G-EQ). There is no consumed
axiom, so the first trust point reduces to the single A-reference check.
