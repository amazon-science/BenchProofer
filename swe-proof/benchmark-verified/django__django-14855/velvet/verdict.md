# P2 adversarial audit — django__django-14855

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-14855", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED** (both agentic gates pass)

Instance: `django.contrib.admin.helpers.AdminReadonlyField.get_admin_url` — thread the
page's own admin-site context (`current_app=self.model_admin.admin_site.name`) into the
`reverse(...)` call so a readonly FK link on a *custom* admin site resolves to
`/custom-admin/...` rather than the ambient default `/admin/...`. F2P =
`test_readonly_foreignkey_links_custom_admin_site`.

Frozen spec: `ensures out = render (resolveAddress viewName pk (some appName)) objLabel`.

## Per-gate table

| Gate | Verdict | Basis |
|------|---------|-------|
| G-EQ | **pass** | G-EQ SOUND + spec-strength TIGHT + no kind-3 refinement. 8/8 wrong impls share spec (`same_spec=True`) and all FAIL verification; positive control (structurally different, correct) VERIFIES → spec non-vacuous and not over-restrictive. |
| G-PANEL | **pass** | faithfulness FAITHFUL (in-container real-`reverse` comparison: 12/12 LINK + PLAIN/NoReverseMatch legs match spec, 0 fails) AND G-AX SOUND (bare callee declaration; real `reverse` deterministic, context-sensitive, NoReverseMatch on unregistered routes over 2007 inputs) AND leakage NO-LEAKAGE. |

Sub-components:
- G-EQ soundness: **SOUND**
- spec-strength: **TIGHT**
- kind-3 refinement: **none**
- faithfulness: **FAITHFUL**
- G-AX: **SOUND**
- leakage: **NO-LEAKAGE**

## Concrete defects + precise fixes

**None.** No counterexample was exhibited by any reviewer:
- No verifying-but-wrong impl (8 attacks all rejected; positive control verifies).
- No unfaithful divergence (real post-gold semantics match spec on every F2P input shape).
- No unsound axiom (`resolveAddress` is the weakest sufficient contract on the UNCHANGED
  `reverse` callee; modeling assumption — deterministic + context-determinant — holds against
  the real callee, rc 0).
- No leak (spec view is strictly *less* revealing than the public problem_statement, which
  itself publishes the complete gold patch verbatim; the only repo-echoing identifier
  `getAdminUrl` is named in the PS).

No fix required.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (quoted verbatim)

> atk_8 (link to `pk` instead of the resolved address) shares spec and fails — the postcondition pins the link's address to be exactly the resolved address `a`, not any other input. Comprehensive.
>
> All checks complete. Final verdict.
>
> VERDICT — django__django-14855
>
> G-EQ: SOUND. spec-strength: TIGHT.
>
> Spec (frozen): `ensures out = render (resolveAddress viewName pk (some appName)) objLabel`. The impl region is the result-producing block; axioms/pure/pre/post were left byte-identical for every attack (same_spec=True confirmed for all). NOTE: `/tmp` is shared by parallel reviewers using colliding filenames — my first pass got clobbered (saw stale content from unrelated instances django-autoreloader / sklearn-DType); I re-ran everything and re-confirmed. All results below are from the namespaced dir.
>
> 1. Spec-too-weak (machine-checked) — 8 wrong impls, all share spec (same_spec=True) and all FAIL verification (exit 1):
> - atk_1 = the prepatch bug: `resolveAddress viewName pk none` (ambient default, no current_app). Rejected by the ensures clause — opaque `resolveAddress ... none` is not provably equal to `resolveAddress ... (some appName)`. Goal left: `Rendered.link i objLabel = match resolveAddress viewName pk (some appName) ...`.
> - atk_2 = always `Rendered.plain objLabel`. Rejected: `Rendered.plain objLabel = match resolveAddress viewName pk (some appName) ...` unsolved (some-leg fails).
> - atk_3 = always `Rendered.link [] objLabel` (empty addr). Rejected (none-leg + wrong addr).
> - atk_4 = swapped branches (plain on resolve / link on fail). Rejected.
> - atk_5 = args swapped `resolveAddress pk viewName (some appName)`. Rejected (opaque, different args).
> - atk_6 = link captioned with `viewName` not `objLabel`. Rejected (label pinned).
> - atk_7 = wrong context `some viewName`. Rejected (opaque, different 3rd arg).
> - atk_8 = link to `pk` instead of the resolved address `a`. Rejected (address pinned to the resolver output).
> - POSITIVE CONTROL (pos) = structurally different but correct: `let r := resolveAddress viewName pk (some appName); return render r objLabel`. same_spec=True, VERIFIES (exit 0) — spec is non-vacuous.
>
> The rejecting clause for every attack is the single `ensures out = render (resolveAddress viewName pk (some appName)) objLabel`: it pins (i) the exact 3 arguments to the opaque resolver including the context `some appName`, (ii) link-vs-plain dispatch on the resolution outcome, (iii) the link address = the resolved address, (iv) the caption = `objLabel`. No degree of freedom is left for a wrong impl.
>
> 2. Refinement audit — no kind-3. Every step in refinement.md §A is R / A-consumed / R+I. The one op that genuinely changed (adding `current_app=self.model_admin.admin_site.name`) is captured exactly as the third argument `some appName` to the A-consumed `resolveAddress` (the UNCHANGED `reverse` callee) — not hand-waved. mapping pins `appName ← self.model_admin.admin_site.name` and `patch.diff` is the gold verbatim (matches instance.json). Bundle `Solution_prepatch.lean` FAILS (exit 1) at the right discriminating clause — identical goal to my atk_1: `resolveAddress viewName pk none` ≠ `resolveAddress viewName pk (some appName)`. No verifying model whose refined patch would fail to resolve was exhibited; the type refinement (str↔List Char, current_app↔Option) hides no mismatch.
>
> 3. Ungrounded-oracle probe — clean. `resolveAddress` is opaque but is NOT an echoable answer-key: the postcondition forces the impl to invoke it with the exact `(viewName, pk, some appName)` triple and dispatch correctly. atk_1/atk_5/atk_7 (echoing the oracle with the wrong arguments) and atk_2/atk_3/atk_8 (returning constants/wrong addresses) all fail — there is no constant or alternate call that provably equals the pinned expression. The behavior must be produced by the modeled branch (directive 8 satisfied).
>
> G-AX (re-run in-container): rc 0 — real `django.urls.reverse` over a 2-instance-namespace urlconf is deterministic, context-sensitive (custom `/custom-admin/` vs default `/admin/` prefixes differ), and raises NoReverseMatch on unregistered routes, over 2007 inputs (seed 14855). The axiom is the weakest sufficient contract on the unchanged callee and is sound.

## Sub-review 2 — FAITHFULNESS + G-AX (quoted verbatim)

> VERDICT: faithfulness = FAITHFUL, G-AX = SOUND.
>
> ## Audit of django__django-14855 (AdminReadonlyField.get_admin_url — thread current_app into reverse)
>
> The bug: a readonly FK link on a page served by a *custom* admin site resolved its URL against the ambient/default site (no current_app), emitting `/admin/...` instead of the page's own `/custom-admin/...`. Gold fix adds `current_app=self.model_admin.admin_site.name` to the `reverse(...)` call. F2P = `test_readonly_foreignkey_links_custom_admin_site`.
>
> ### Mechanical re-checks (independent, not trusting the gates)
> - G-VERIFY: `Solution.lean` verifies, exit 0.
> - G-DIFF: `Solution_prepatch.lean` FAILS (exit 1) with a genuine unsolved-goals error — its impl resolves with `none` (ambient default) but the frozen spec demands `some appName`; since `resolveAddress` is opaque, `... none` is not provably equal to `... (some appName)`. This is exactly the bug delta.
> - `same_spec(Solution, Solution_prepatch) = True` — they share the identical frozen spec, so the prepatch is a legitimate discriminator, not a re-specced strawman.
> - `#print axioms getAdminUrl_correct` → `[propext, resolveAddress, Classical.choice, Quot.sound]`. Only the one declared bundle axiom; no hidden equational axioms about `resolveAddress`.
>
> ### Faithfulness — FAITHFUL (Docker evidence: spec == real post-gold)
> I materialized the REAL patched `get_admin_url` semantics in-container against a real namespaced urlconf (two instance namespaces `default_site`/`custom_site` sharing app namespace `app`) and compared it to the spec model `out = render (resolveAddress viewName pk (some appName)) objLabel` on the F2P input shapes:
> - All 12 LINK cases (custom & default contexts × 6 pks) matched exactly: real `('LINK','/custom-admin/obj/1/',...)` == spec prediction, real `('LINK','/admin/obj/1/',...)` == spec, etc.
> - PLAIN/NoReverseMatch leg matched: unregistered route → `('PLAIN','OBJLABEL')` both sides (the `try/except NoReverseMatch` → `none` modeling is correct).
> - Discriminating subtlety confirmed: custom (`/custom-admin/obj/1/`) ≠ default (`/admin/obj/1/`) — the context genuinely changes the URL, which is the whole point of the fix.
> - FAILS: 0. The spec pins exactly the post-gold behavior; it rejects nothing a correct impl would do (any verifying impl must call `resolveAddress` with `some appName`, = the gold patch up to type refinement). No over-restriction, no drift from the F2P observable.
>
> ### G-AX — SOUND
> The sole axiom `resolveAddress : List Char → List Char → Option (List Char) → Option (List Char)` is a bare function declaration with no value-pinning Ensures, modeling the UNCHANGED callee `django.urls.base.reverse(viewname, args, current_app=...)`. The only modeling assumption is that `reverse` is a deterministic function of `(viewname, args, current_app)`, and (load-bearing for G-DIFF) that current_app is a genuine determinant of the result. I ran `axiom_check.py` in-container (rc 0, 2007 inputs, seed 14855): real `reverse` is deterministic, custom vs default contexts yield different and correctly-prefixed URLs, and unregistered routes raise NoReverseMatch. There is no equational axiom that could be violated; the modeling assumption holds against the real callee. (G-CONF is a legitimate skip: impl region is all-A-tagged — the observable only materializes by serving a real admin page, which the F2P test does end-to-end.)
>
> faithfulness = FAITHFUL; G-AX = SOUND.

## Sub-review 3 — LEAKAGE (quoted verbatim)

> I have everything needed for the leakage verdict. Let me do the reconstruction analysis.
>
> **Public problem_statement contains (verbatim):**
> - The exact symbol: `get_admin_url` in `django.contrib.admin.helpers`
> - The exact buggy line: `url = reverse(url_name, args=[quote(remote_obj.pk)])`
> - The exact fix, character for character: `url = reverse(url_name, args=[quote(remote_obj.pk)], current_app=self.model_admin.admin_site.name)`
> - The symptom: `/admin/...` instead of `/custom-admin/...` in a custom Admin Site
> - The mechanism: "Other parts of the admin use the current_app keyword parameter to identify the correct current name of the Admin Site"
>
> This is one of the rare instances where the public issue *already publishes the complete gold patch*. So any leakage standard is trivially satisfied — the spec view cannot reveal anything not already in the PS.
>
> **Spec view content vs PS:**
> - `resolveAddress` (axiom) — generic abstraction of `reverse`; `reverse` is named in PS anyway. No leak.
> - `getAdminUrl` — echoes the repo symbol `get_admin_url`, which PS names verbatim. Not a leak beyond PS.
> - "application context" / `appName` / `some appName` vs `none` (ambient default) — direct, de-narrated abstraction of `current_app` / Admin Site name; PS explicitly states "current_app keyword parameter to identify the correct current name of the Admin Site," and the `/admin/` vs `/custom-admin/` distinction is the PS symptom.
> - `Rendered.link`/`plain`, `render` — generic display model; not repo-specific. PS does not even need this.
> - No diff line, no `format_html`, no `quote`, no file path appears in the spec view.
>
> The spec view is, if anything, *less* revealing than the PS (it abstracts `reverse`→`resolveAddress`, `current_app`→application context). The only repo-echoing identifier is `getAdminUrl`, which is named in the PS.
>
> **Reconstruction from spec view alone:** A reader would infer "a function that builds a display for a related object reference, resolving an address within a named application context (`some appName`) rather than the ambient default." This maps to threading the page's context into an address resolver — which is exactly the public bug. No information beyond PS is gained.
>
> NO-LEAKAGE.
>
> Reconstruction attempt from the spec view alone: the spec view describes `getAdminUrl(viewName, pk, appName, objLabel)` whose output is `render (resolveAddress viewName pk (some appName)) objLabel` — i.e. "resolve the target address WITHIN the page's own application context `appName`, not within the ambient default." This reconstructs the gold's intent (thread the page's admin-site context into the address resolver) but reveals nothing the public `problem_statement` does not already state far more explicitly. The PS itself publishes the COMPLETE gold patch verbatim: it names the file (`django.contrib.admin.helpers`), the symbol (`get_admin_url`), the exact buggy line `url = reverse(url_name, args=[quote(remote_obj.pk)])`, and the exact fix `current_app=self.model_admin.admin_site.name`, plus the `/admin/...` vs `/custom-admin/...` symptom and the `current_app` mechanism. So the leakage bar is trivially met.
>
> Examined every spec-view token for leakage beyond PS:
> - `resolveAddress` axiom — a generic abstraction of `reverse`; strictly LESS revealing than PS (which names `reverse` and `current_app` outright). No leak.
> - `getAdminUrl` — echoes repo symbol `get_admin_url`, but that symbol is named verbatim in the PS ("django.contrib.admin.helpers get_admin_url"). Not beyond PS.
> - "application context" / `some appName` vs `none` (ambient default) — de-narrated abstraction of `current_app` / "current name of the Admin Site," which the PS states explicitly. Not beyond PS.
> - `Rendered.link`/`plain`, `render` — generic display model, repo-agnostic; no diff line, no `format_html`/`quote`/`reverse`/file path appears.
>
> No leaking token exists. The single repo-echoing identifier (`getAdminUrl`) is published in the PS. This is NOT a RELAXED case — the discriminator (resolve within the page's context vs the default) is fully present in the public `problem_statement`, not confined to `hints_text`/gold/`test_patch`. No relaxed-leakage rationale is needed or claimed (meta.json G-LEAK = "pass", not "relaxed").
>
> Verdict: NO-LEAKAGE.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 11 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 11 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Rigorous faithfulness audit of the spec for django__django-14855 (get_admin_url). VERDICT: FAITHFUL — no input found where the modeled function disagrees with the real (patched) callee; the spec is not over-strong.

### Evidence
1. Spec-region byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True. The frozen spec (axiom resolveAddress; Rendered; render; getAdminUrl signature + `ensures out = render (resolveAddress viewName pk (some appName)) objLabel`) is identical between the passing and pre-patch skeletons — only the impl `do` block differs (some appName vs none).
2. Lean verification: scripts/lean_verify.sh Solution.lean -> exit 0 (verifies). Solution_prepatch.lean -> exit 1, unsolved `ensures` goals (G-DIFF confirmed: resolveAddress …none not provably == …some appName under an opaque axiom).
3. Real repo confirmed at base_commit 475cffd1d64c690cdad16ede4d5e81985738ceb4: pre-patch `url = reverse(url_name, args=[quote(remote_obj.pk)])`; gold patch (patch.diff, verbatim) adds `current_app=self.model_admin.admin_site.name`. reverse signature reverse(viewname, urlconf, args, kwargs, current_app) — UNCHANGED by patch. AdminSite.name is always a str ('admin' default, or custom), so the modeled call site legitimately always passes `some appName`, never `none` — the `some appName` modeling is faithful, not an over-restriction.

### Faithfulness of each abstraction
- appName<-admin_site.name always present => some appName (verified AdminSite().name=='admin').
- reverse success (str URL) <-> render (some a) = Rendered.link <-> format_html('<a href=…>', url, obj). NoReverseMatch raised <-> none = Rendered.plain <-> str(remote_obj); the try/except makes the raise observationally 'no address' — matches Option result.
- resolveAddress is the WEAKEST contract (function of route,arg,context jointly; pins no URL) over the UNCHANGED reverse callee. It does not exclude any real reverse behavior. G-AX (axiom_check.py) independently validates determinism + context-sensitivity + NoReverseMatch on the real reverse over a 2-namespace urlconf.
- args taken already-projected (viewName from url_name, pk from quote(remote_obj.pk), objLabel from remote_obj) — a refinement-audit-only projection, consistent with mapping.md; not part of consumer view.

**No diverging input exists:** the ensures pins exactly the patched behavior and the modeled function equals the real patched get_admin_url on the modeled domain up to the documented str<->List Char / current_app<->Option / format_html/str display refinements. meta.json conf_skip=true and G-CONF status=skip are appropriate (all-A-tagged impl region; the only behaviorally-meaningful op is the A-consumed reverse call). Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage attacker (gold-reconstruction) baseline is the PUBLIC problem_statement, which for django__django-14855 already contains the gold edit VERBATIM in literal Python: `url = reverse(url_name, args=[quote(remote_obj.pk)], current_app=self.model_admin.admin_site.name)`, plus the full diagnosis (/admin vs /custom-admin) and the exact changed line. That is the most concrete disclosure possible; nothing in the spec view can leak 'beyond' it. The spec view (rendered via markers.spec_view with the velvet backend, impl + prove_correct body elided) restates the fix only ABSTRACTLY: ensures out = render (resolveAddress viewName pk (some appName)) objLabel, i.e. 'resolve within the page's own application context, not the ambient default.' This is the legitimate behavioral specification and is strictly less revealing than — and fully subsumed by — the public statement. Impl region collapses to a placeholder and the proof body is elided, so the solver never sees the some appName / none choice in the impl. Docstring references to mapping.md/axiom_check.py are provenance pointers, not reconstruction aids. Confirmed spec region is frozen: same_spec(Solution.lean, Solution_prepatch.lean)=True — the discriminator differs only in the elided impl. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
