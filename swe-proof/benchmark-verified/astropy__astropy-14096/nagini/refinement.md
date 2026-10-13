# refinement.md — astropy__astropy-14096

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_missing` impl region and the consumed per-leg step axioms) and
`patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** here,
the proof uses the axiom's `Exsures`), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fallback resolver — `SkyCoord.__getattr__` (`sky_coordinate.py:869`)

Gold hunk:
```
-        # Fail
-        raise AttributeError(
-            f"'{self.__class__.__name__}' object has no attribute '{attr}'"
-        )
+        # Call __getattribute__; this will give correct exception.
+        return self.__getattribute__(attr)
```

The four domain-resolution branches above the hunk (`_is_name`, the frame
attribute, the frame passthrough, the transform target) are **unchanged** by the
patch; the change replaces only the final fail branch.

| # | model.py impl op (`resolve_missing`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `name: int` | `attr: str` parameter | R | a `str` attribute name ↔ an `int` symbol id (mapping.md §2). The only observable the F2P test reads is *which name* the error blames (`match="random_attr"`) — an identity comparison `int` equality models faithfully. |
| A2 | `if is_alias: return alias_value` | `if self._is_name(attr): return self` (`:875-876`) | R + I | identical control flow (test-then-return, highest priority). This leg is TOTAL — `return self` cannot fail — so the consumer pins it with an unconditional value equality and no selector/capability. |
| A3 | `if is_frame_attr: return frame_attr_step(name, frame_attr_value)` | `if attr in frame_transform_graph.frame_attributes: …` (`:881-885`) | R + A-consumed | identical second-priority branch. The branch's value expression is PARTIAL: `getattr(self, "_" + attr, None)` runs a subclass descriptor that can raise (measured: `__getattr__(obj,"equinox")` → `TypeError`), and since the branch is a `return` of it, that failure becomes `__getattr__`'s own. `frame_attr_step` is the weakest axiom capturing both paths. |
| A4 | `if is_frame_passthrough: return passthrough_step(name, passthrough_value)` | `… return getattr(self._sky_coord_frame, attr)` (`:889-890`) | R + A-consumed | identical third-priority branch, likewise partial in its value expression. |
| A5 | `if is_transform: return transform_step(name, transform_value)` | `… return self.transform_to(attr)` (`:893-895`) | R + A-consumed | identical fourth-priority branch, and the most conspicuously PARTIAL one: measured on the repo, `transform_to` raises for many registered frame names the coordinate cannot be transformed to — `altaz`/`hadec` (`AttributeError`, no observer `location`), `teme` (`AttributeError`), `lsr`/`galacticlsr` (`TypeError`), `galactocentric` (`ConvertError`), `hcrs`/`heliocentric*ecliptic` (`UnitsError`). The resolver surfaces those failures. |
| A6 | `return residual_step(name)` (the residual leg) | `return self.__getattribute__(attr)` | A-consumed | the changed operation. The op is a **`return` of a call**, so the callee's outcome becomes `__getattr__`'s own on BOTH of the callee's paths — the step is the ordinary resolver and returns normally for every name that resolves. `residual_step` is the **weakest** axiom about the unchanged callee that captures both: where `residual_step_succeeds(name)` it returns `residual_step_value(name)` (`Ensures`), otherwise it surfaces an `AttributeError` whose blamed subject is `residual_step_subject(name)` — the underlying missing name, in GENERAL distinct from `name` (`Exsures`) — and both paths grant `residual_step_performed(name)`. G-AX confirms the value-level facts against the real callee in both directions (mapping.md §3.1). |

**Every leg but the alias is PARTIAL, and the consumer states exactly that.** The
resolver does not guarantee that a selected leg returns; it guarantees it is a
**conduit** for the leg its guards selected, on both of that leg's paths. Per leg:

1. a **normal-return `Ensures`** — the leg's step SUCCEEDED
   (`*_step_succeeds(name)`), the value is that step's value, and the return
   carries that step's capability. So a normal return is legal only as the
   selected step's own success passed through: the value is not the resolver's to
   choose, the capability cannot be forged, and the selector forbids returning
   where the step FAILED; and
2. a per-leg arm of the **`Exsures`** — the leg's `*_step_succeeds(name)` must be
   FALSE (so the resolver may not fail where its step succeeded) and the failure
   must carry that leg's own capability (so it may be neither fabricated nor
   borrowed from a different leg). On leg 5 the arm additionally pins the
   discriminating observable: `RaisedException().subject ==
   residual_step_subject(name)`, the underlying missing name, which the spec does
   NOT assume equals `name`.

Both directions are load-bearing, and each closes holes the other cannot:

* Without (1), a leg was constrained ONLY by the `Exsures`, so a same-spec impl
  whose residual leg returned normally (e.g. `return name` or `return
  alias_value`) satisfied it *vacuously* and verified while NOT resolving (the F2P
  test then reports "DID NOT RAISE AttributeError").
* The **selector conjuncts** forbid path conversion. An impl that genuinely
  performs a step — and so legitimately holds its capability — but swallows the
  step's failure and returns a value is rejected only by (1)'s selector; the
  capability cannot see it. Symmetrically, an impl that performs the step and then
  raises even where it SUCCEEDED is rejected only by (2)'s negated selector. Both
  rivals are in `properties.py`, on the residual leg
  (`atk-swallow-step-failure`, `atk-invert-step-path`) **and** on a partial domain
  leg (`atk-swallow-transform-step`, `atk-invert-frame-attr-step`).
* The capabilities are **per leg**, which is what stops a leg from passing another
  leg's work off as its own (`atk-borrowed-step-token`).

**Why the legs are partial rather than total.** An earlier form of this spec
pinned all four domain legs as TOTAL (`Implies(guard, Result() == value)`), which
silently asserts that every selected leg RETURNS. That is **false of the real
function**: measured on the repo at `base_commit` and identically with the change
applied, `type(base).__getattr__(base, "altaz")` RAISES
`AttributeError("'NoneType' object has no attribute 'to_geodetic'")` with flags
`(alias, frame_attr, passthrough, transform) = (False, False, False, True)`, and
the same holds for `hadec`, `teme`, `lsr`, `galactocentric` and the heliocentric
family. The total form therefore rejected a faithful implementation of the real
branch. It has been corrected in the honest direction: each leg now states what
the real step GUARANTEES — its two paths, on its own condition — instead of
asserting a totality the step does not have. The discriminating strength is
preserved: every rival the total form rejected is still rejected, on the
selector/value/capability conjuncts rather than on a false blanket totality, and
five NEW rivals aimed at the partiality itself are rejected too.

**Why leg 1 stays total.** `return self` cannot fail, so the alias leg keeps its
unconditional equality and the `Exsures` is unconditional in `not is_alias`: no
failure may escape that leg at all. `atk-alias-leg-made-partial` is the control
confirming this was not relaxed along with the others.

The pre-change behaviour fabricated a failure blaming `name` itself;
`model_prepatch.py` reproduces that (`raise AttributeAccessError(name)`). It
**fails** the `Exsures`: it never performs the residual step, so it can present
neither `residual_step_performed(name)` nor the selector fact `not
residual_step_succeeds(name)`, and its subject is `name`, which the spec does NOT
assume equals `residual_step_subject(name)`. Any one of the three suffices — that
is the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
fail branch's delegation to the ordinary attribute-lookup mechanism — is an
**A-consumed** axiom (`residual_step` / `residual_step_subject`) about the
**unchanged** callee `object.__getattribute__` (the patch calls it but does not
change it), whose soundness G-AX audits against the real callee. There is no
axiom about the function under change (`__getattr__` itself is modelled deeply
as `resolve_missing`). No step is a changed operation Nagini cannot express.

## C. verify(model) ⇒ resolved

`resolve_missing` verifies only if, on each leg, whichever way it terminates, that
outcome is the outcome of the step its guards selected. If it raises, the leg's
`*_step_succeeds(name)` must be false, the failure must carry that leg's own
capability, and on the residual leg the blamed subject must equal
`residual_step_subject(name)`; if it returns, the leg's selector must be true, the
value must be that step's value, and the return must carry the same capability.
The capabilities force the work to actually be done: although an impl COULD echo a
pure oracle to match a value or a subject, only a step's own two paths produce its
capability, so performing the step is the sole way to discharge either clause —
and the selector conjuncts additionally stop an impl that DOES perform a step from
converting one of its outcomes into the other. Together these close the "return
normally and satisfy the conditional Exsures vacuously" escape, the
swallow/invert escapes on every partial leg, and the borrowed-capability escape,
**without** asserting the counterfactual "these legs always return" — which is
what the measurements in §A and mapping.md §3.1 refute.

By R (str ↔ int symbol id, booleans ↔ the runtime guards) the verified resolver
equals the gold `__getattr__` on the tested inputs; by G-AX the axioms soundly
approximate the real callees in both directions (the surfaced error on the
residual leg blames the inner missing name, e.g. `random_attr`, not the requested
`prop`; and a resolving name returns normally). G-CONF shadows the model against
the real function on 102183 inputs — including every registered frame name on
several objects, so both outcomes of the partial transform leg are covered by
construction — with 0 disagreements, and reports the 12 velocity/differential
inputs that lie outside the type bridge rather than dropping them silently. The
same generator, run against the OLD total-transform shadow, reports the
disagreement at `altaz` immediately, so this coverage is not blind to the defect
it was extended for.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callees — and the gold patch resolves
(G-RESOLVE; the F2P test `test_subclass_property_exception_error` asserts the
surfaced `AttributeError` matches `random_attr`). The trust points are exactly the
two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ).
