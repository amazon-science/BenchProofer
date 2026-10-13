import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two value-dependent operations the routine can
--  perform on a value it does NOT recognise as binary — encoding a text value in
--  the response charset, and rendering an arbitrary object then encoding it — are
--  UNCHANGED and irrelevant to the modeled behaviour, so they are taken as FREE
--  INPUTS: `encodeStr` (the charset encoder) and `fallback` (the encoded textual
--  rendering of a non-binary, non-text value). The spec makes no behavioural
--  claim about either, so it holds for every value of them; nothing here needs
--  validation against a real callee, hence no G-AX axioms. The one semantic fact
--  the model relies on — that materialising a byte-buffer view yields its
--  underlying bytes, identical to materialising a plain byte string — is an
--  A-reference validated against the real builtin by axiom_check.py, NOT an
--  axiom consumed by the proof.)
-- axioms-end

-- pure-start
/- The kinds of body value the routine must turn into a bytestring, classified by
   how the value carries its content:
   * `bytes b`  — a plain byte string whose bytes are `b`;
   * `buffer b` — a read-only view over a byte region whose underlying bytes are
                  `b` (materialising it yields exactly `b`, the same as a plain
                  byte string — see axiom_check.py);
   * `text s`   — a textual value, to be encoded in the response charset;
   * `other`    — any other value, rendered textually then encoded.
   This is the value-shape the routine dispatches on. -/
inductive Body where
  | bytes  : List UInt8 → Body
  | buffer : List UInt8 → Body
  | text   : List Char  → Body
  | other  : Body
  deriving Inhabited

/- The output bytestring for one body value. A byte string and a byte-buffer view
   both yield their underlying bytes unchanged; a textual value is encoded with
   the charset encoder `encodeStr`; anything else yields `fallback`, the encoded
   textual rendering. The discriminating point: a byte-buffer view yields its
   CONTENT `b`, never the (charset-encoded) rendering `fallback`. -/
def bodyBytes (encodeStr : List Char → List UInt8) (fallback : List UInt8) : Body → List UInt8
  | .bytes  b => b
  | .buffer b => b
  | .text   s => encodeStr s
  | .other    => fallback

@[grind, simp] lemma bodyBytes_bytes (e) (f) (b : List UInt8) :
    bodyBytes e f (.bytes b) = b := rfl
@[grind, simp] lemma bodyBytes_buffer (e) (f) (b : List UInt8) :
    bodyBytes e f (.buffer b) = b := rfl
@[grind, simp] lemma bodyBytes_text (e) (f) (s : List Char) :
    bodyBytes e f (.text s) = e s := rfl
@[grind, simp] lemma bodyBytes_other (e) (f) :
    bodyBytes e f .other = f := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Turn a response body value into its output bytestring. A byte string and a
   read-only byte-buffer view both yield their underlying bytes; a textual value
   is encoded with the charset encoder; any other value is rendered textually and
   encoded. `encodeStr`, `fallback` and `value` are read-only — the routine
   mutates nothing it is handed (directive 5). -/
method makeBytes (encodeStr : List Char → List UInt8) (fallback : List UInt8) (value : Body)
    return (out : List UInt8)
  ensures out = bodyBytes encodeStr fallback value
  do
    -- impl-start
    match value with
    | .bytes  b => pure b
    | .buffer b => pure b
    | .text   s => pure (encodeStr s)
    | .other    => pure fallback
    -- impl-end

prove_correct makeBytes by
  loom_solve
