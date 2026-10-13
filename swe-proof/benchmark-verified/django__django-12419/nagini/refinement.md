# refinement.md — django__django-12419

The operation-by-operation correspondence between `model.py`'s implementation
(the `apply_referrer_policy` impl region, the `HeaderSlot` model, and the deep
`normalized_policy` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** if
the proof uses the axiom's `Ensures`, **A-reference** if a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested input, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The gold hunk — the configured default

Gold hunk (`django/conf/global_settings.py:640`):
```
-SECURE_REFERRER_POLICY = None
+SECURE_REFERRER_POLICY = 'same-origin'
```

The setting flows, unchanged, into the security response filter
(`django/middleware/security.py`):
```
self.referrer_policy = settings.SECURE_REFERRER_POLICY            # line 18
...
if self.referrer_policy:                                          # line 47
    response.setdefault('Referrer-Policy', ','.join(              # line 50-52
        [v.strip() for v in self.referrer_policy.split(',')]
        if isinstance(self.referrer_policy, str) else self.referrer_policy))
```
The F2P test (`project_template.test_settings.test_middleware_headers`) renders
a response through the default middleware and asserts the serialized headers now
include `Referrer-Policy: same-origin`.

| # | model.py impl op (`apply_referrer_policy`) | patch.diff / consumer op | tag | justification |
|---|---|---|---|---|
| A1 | `policy = [115,97,…,110]` (the impl-region local), asserted `ToSeq(policy) == baseline_policy()` | the new value `'same-origin'` of `SECURE_REFERRER_POLICY` read into `self.referrer_policy` | R + I | `str` ↔ `List[int]` code points (mapping.md §2). The value is the carrier of the gold change; it lives in the **impl region**, so the prepatch can change it (to the falsy `None`) while keeping the spec byte-identical. |
| A2 | `if len(policy) > 0:` | `if self.referrer_policy:` (truthiness of the configured value) | R | a non-empty `str` is truthy ↔ `len(policy) > 0`; `None`/`''` falsy ↔ `len(policy) == 0` (mapping.md §2). |
| A3 | `if not slot.present:` then write `slot.present, slot.value`; else leave `slot` unchanged | `response.setdefault('Referrer-Policy', value)` | R | `setdefault` writes only if the key is absent (`django/http/response.py:204-207`); the present-flag + value-write model that, and the untouched-else models "leave an already-present header". |
| A4 | `value` built as the per-token-trim/comma-rejoin of `policy`, equal to `normalized_policy(ToSeq(policy))`, computed by the verified copy loop | `','.join([v.strip() for v in self.referrer_policy.split(',')] if isinstance(…, str) else …)` | A-reference | the value-construction chain is modeled **deeply** by the `@Pure normalized_policy` (with `is_ws`/`has_comma`/`has_ws`) and the verified loop; there is **no consumed axiom**. G-AX (axiom_check.py) validates `normalized_policy == the real chain` on its modeled domain (comma-/whitespace-free single tokens), which includes the baseline `'same-origin'` (mapping.md §3.1). On that domain the chain is the identity, so `value == policy`. |
| A5 | `slot.value` ends as `ToSeq(slot.value) == baseline_policy()`; `slot.present` true | the `Referrer-Policy` header value observed by the F2P test == `same-origin`, header present | R + I | by A1+A4, the attached value is `'same-origin'`; the discriminating postcondition `ToSeq(slot.value) == baseline_policy()` is exactly what the F2P test asserts. |

## B. The discriminating clause (G-DIFF)

The change observed by the test is purely the **configured default value**:
pre-patch it is `None` (falsy), so `if self.referrer_policy:` is false and the
header is never attached; post-patch it is `'same-origin'` (truthy, non-empty),
so the header is attached with that value.

`model_prepatch.py` keeps the spec **byte-identical** (verified: the spec view
through `# impl-start` is diff-clean) and reverts the impl-region `policy` to
the pre-patch falsy default `[]` (the `List[int]` image of `None`/empty). With
`len(policy) == 0` the `if len(policy) > 0:` guard is false, the slot is never
made present, and the postcondition

  `Ensures(slot.present)`

**fails** for a slot that started absent — precisely the spec sensing the
change. (It would equally fail the `ToSeq(slot.value) == baseline_policy()`
clause, but Nagini reports the present-flag clause first.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation the gold changes —
the configured default value `None → 'same-origin'` — is modeled **concretely**
as the impl-region `policy` carrier (R+I, step A1), not hidden behind an axiom.
The only kind-A construct is the **A-reference** deep model `normalized_policy`
of the **unchanged** value-construction chain `','.join([v.strip() …])`, which
G-AX validates against the real chain; there is **no consumed `@ContractOnly`
axiom** (the `axioms` region is empty).

## D. verify(model) ⇒ resolved

`apply_referrer_policy` verifies only if, starting from an absent header slot,
the slot ends present with value equal to `normalized_policy(baseline_policy())`
== `baseline_policy()` (clauses A4, A5) — i.e. the `Referrer-Policy` header is
attached with `same-origin`. By R (the `str ↔ List[int]` carrier, the
truthiness and `setdefault` refinements) the verified filter equals the real
`process_response` referrer-policy branch on the baseline configuration; by
G-AX the deep model `normalized_policy` equals the real value chain on the
baseline token (A-reference). The gold hunk makes the baseline configuration
supply `'same-origin'`, so a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited callee chain —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two
of PLAN §1.1: callee-chain soundness (G-AX) and refinement fidelity (this
document, G-EQ).
