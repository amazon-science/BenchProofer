import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The display operation under spec produces the bracketed
   token for a fixture parameter using a size-limited *safe representation* of
   the parameter value. That safe representation is modeled DEEPLY by
   `quotedRepr` (the `pure` region) on BOTH payload shapes the observed
   behaviour distinguishes (a text value and a byte-string value), not hidden
   behind a consumed axiom; G-AX (axiom_check.py) validates `quotedRepr` == the
   real size-limited safe representation over the whole `simpleParam` domain
   (an A-reference, mapping.md §3). There is no module-level `axiom` and no
   `:|` callee stub. -/
-- axioms-end

-- pure-start
/- Short, printable content: every code point is printable ASCII other than
   the apostrophe and the backslash. On such content a safe representation
   escapes nothing, so the deep model below can spell it out exactly. -/
def simpleChars (s : List Char) : Prop :=
  ∀ c ∈ s, 32 ≤ c.toNat ∧ c.toNat ≤ 126 ∧ c ≠ '\'' ∧ c ≠ '\\'

/- The parameter payload shapes this behaviour distinguishes:
     * `textVal s`  — a plain text value (a sequence of code points);
     * `bytesVal s` — a byte-string value whose bytes decode to the code
                      points `s`. A byte-string has no plain textual form
                      under strict byte/text separation — taking one is an
                      error — so its display must go through the safe
                      representation. -/
inductive ParamValue where
  | textVal  (s : List Char)
  | bytesVal (s : List Char)
  deriving Inhabited

/- The parameter values this behaviour concerns: short, printable payloads.
   A text value may carry at most 40 code points and a byte-string at most 39
   (its representation also carries a one-character type prefix). On exactly
   this domain the size-limited safe representation introduces no truncation
   marker, so the deep model `quotedRepr` below is exact (mapping.md §2,
   §3.1). -/
def simpleParam : ParamValue → Prop
  | .textVal s  => s.length ≤ 40 ∧ simpleChars s
  | .bytesVal s => s.length ≤ 39 ∧ simpleChars s

/- A size-limited *safe representation* of a short, printable parameter value:
   a text value is its content surrounded by apostrophes; a byte-string value
   is its decoded content surrounded by apostrophes and marked with the
   one-character byte-string prefix. This is the deep model of the safe
   representation used by the display, validated against the real one by G-AX
   over the `simpleParam` domain (an A-reference). On this domain the value
   never exceeds the size limit, so no truncation marker is introduced. -/
@[grind] def quotedRepr : ParamValue → List Char
  | .textVal s  => '\'' :: (s ++ ['\''])
  | .bytesVal s => 'b' :: '\'' :: (s ++ ['\''])

/- Wrap a rendered token in the surrounding square brackets that the parameter
   display emits. -/
def bracket (s : List Char) : List Char := '[' :: (s ++ [']'])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the bracketed display token for a fixture's parameter value.

   Desired behaviour: the value is displayed through a size-limited *safe
   representation* — so a text value appears surrounded by apostrophes (e.g.
   `foo` is shown as `'foo'`) and a byte-string value appears with its
   byte-string prefix and apostrophes (e.g. the bytes of `Hello World` are
   shown as `b'Hello World'`) — rather than through its plain textual form.
   The plain textual form would show a text value's bare characters, and on a
   byte-string it is not even well-defined under strict byte/text separation
   (the display would error out rather than produce a token). The whole token
   is then wrapped in the surrounding square brackets the display uses.

   `param` is read-only: the method builds and returns a fresh token and never
   mutates its input. -/
method renderParameterDisplay (param : ParamValue) return (out : List Char)
  require simpleParam param
  ensures out = bracket (quotedRepr param)
  ensures ∀ s : List Char, param = ParamValue.textVal s →
    out = bracket ('\'' :: (s ++ ['\'']))
  ensures ∀ s : List Char, param = ParamValue.bytesVal s →
    out = bracket ('b' :: '\'' :: (s ++ ['\'']))
  do
    -- impl-start
    -- Pre-image skeleton: the value is displayed through its plain textual
    -- form (the bare characters of its content), NOT the size-limited safe
    -- representation. The frozen spec requires the quoted representation, so
    -- prove_correct MUST fail (the apostrophes and the byte-string prefix are
    -- absent).
    let r := match param with
      | ParamValue.textVal s  => s
      | ParamValue.bytesVal s => s
    return bracket r
    -- impl-end

prove_correct renderParameterDisplay by
  loom_solve
