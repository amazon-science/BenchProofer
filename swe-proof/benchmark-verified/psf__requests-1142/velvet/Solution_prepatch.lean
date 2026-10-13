import Velvet.Std
-- imports-end

/- Total correctness: the real size-announcing routine is a straight-line
   dispatch over the payload shape and always terminates, so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge its postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms: the modeled operation decides the announced payload size from the
-- shape of the payload alone (a seekable/measurable/absent payload) and a single
-- boolean property of the request. It calls no unchanged repository callee whose
-- contract must be assumed, so there is nothing to axiomatize. (G-AX skips.)
-- axioms-end

-- pure-start
/- The three observable shapes a request payload can take, as far as announcing
   its size is concerned:
   * `seekable n` — a payload that can be positioned and queried, so its size
     `n` is read back directly;
   * `measurable n` — an in-memory payload whose size `n` is measured directly;
   * `absent` — no payload is present at all. -/
inductive Payload where
  | seekable   (size : Nat)
  | measurable (size : Nat)
  | absent

/- The announced payload size for a request.

   When a payload is present in either form, its exact size is announced. When
   no payload is present, the announcement depends on whether the request method
   conventionally carries an entity body: a method that does carry one announces
   a zero size, while a method that conventionally carries none announces nothing
   at all (`none` — no size is attached). This is the abstract desired behavior:
   a body-less request whose method conventionally has no entity body must not be
   forced to announce a (zero) size. -/
def announcedSize (p : Payload) (carriesBody : Bool) : Option Nat :=
  match p with
  | .seekable   n => some n
  | .measurable n => some n
  | .absent       => if carriesBody then some 0 else none

@[simp] lemma announcedSize_seekable (n : Nat) (b : Bool) :
    announcedSize (.seekable n) b = some n := rfl
@[simp] lemma announcedSize_measurable (n : Nat) (b : Bool) :
    announcedSize (.measurable n) b = some n := rfl
@[simp] lemma announcedSize_absent (b : Bool) :
    announcedSize .absent b = (if b then some 0 else none) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method contentLength (payload : Payload) (carriesBody : Bool) return (out : Option Nat)
  ensures out = announcedSize payload carriesBody
  do
    -- impl-start
    -- Pre-image skeleton: a zero size is announced up front unconditionally and
    -- then overwritten only when the payload is seekable or directly measurable;
    -- with no payload present the leading zero stands regardless of whether the
    -- method conventionally carries an entity body. The frozen spec requires
    -- `announcedSize` (which attaches nothing for a body-less no-payload request
    -- whose method carries none), so prove_correct MUST fail.
    let mut out : Option Nat := some 0
    out := match payload with
      | .seekable   n => some n
      | .measurable n => some n
      | .absent       => out
    return out
    -- impl-end

prove_correct contentLength by
  loom_solve
  cases payload <;> simp_all [announcedSize]
