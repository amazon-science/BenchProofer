# mapping.md — django__django-11532

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a5308514fb4bc5086c9a16a8a24a945eeebb073c`, states the type
abstraction (the Lean↔Python bijection that G-CONF and G-AX use to bridge
values), and gives the provenance of each axiom.

## 0. What the change does (the one independently-observable behavior)

The patch factors the recurring idiom `domain.encode('idna').decode('ascii')`
into a new module-level helper and routes the host name through it in one place
that previously did **not** normalize at all. Concretely:

* `django/utils/encoding.py`: a new helper is added whose body is exactly the
  pre-existing idiom `domain.encode('idna').decode('ascii')` (an ASCII-Compatible
  Encoding of the domain — IDNA/RFC 3490). This helper is *new code*, but its
  behavior is the *unchanged* stdlib codec idiom already used at four call sites.
* `django/core/mail/utils.py` `CachedDnsName.get_fqdn`: the cached host name was
  returned verbatim from the OS lookup; it is now routed through the new helper
  before being cached and returned. **This is the only site that changes
  observable behavior** — a non-ASCII host name now yields its ASCII-compatible
  encoding instead of raw non-ASCII text. The F2P test
  `test_non_ascii_dns_non_unicode_email` mocks the OS lookup to return a CJK host
  and asserts the resulting Message-ID contains the ASCII-compatible form
  (`xn--p8s937b`), which no longer crashes when the message encoding is a
  single-byte (non-Unicode) charset.
* The four other touched sites (`sanitize_address`, two `validators.py` sites,
  two `html.py` sites) replace the inline idiom with a call to the new helper.
  Each is a behavior-identical extraction (same codec, same exception surface):
  pure refactors, no observable change. They are NOT modeled (no new behavior;
  refinement.md tags them I-refactor with justification).

The modeled function is therefore `get_fqdn`: "the cached host name, normalized
to its ASCII-compatible encoding." The normalization callee (the IDNA ACE codec)
is **unchanged** library behavior → an A-consumed axiom (`aceEncode`), checked by
G-AX against the real codec. The OS host lookup is also an unchanged callee.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `punycodeDomain (host : List Char)` | `CachedDnsName.get_fqdn` — `django/core/mail/utils.py:14` (changed line 16) | the modeled changed function: returns the host name's ASCII-compatible encoding |
| `aceEncode` *(axiom — A-consumed)* | `domain.encode('idna').decode('ascii')` — the IDNA/RFC-3490 ASCII-Compatible-Encoding codec, CPython stdlib `encodings/idna.py`, invoked by the new helper `django/utils/encoding.py` (post-patch `punycode`, body line ~222) | unchanged library callee: encodes a domain to its ACE form |
| `aceEncode_ascii` *(axiom — A-consumed)* | the post-condition of `.decode('ascii')`: every code point of the result is ASCII | the weakest property the fix relies on: the normalized host is single-byte-safe |

The OS host lookup `socket.getfqdn()` (`utils.py:16`) supplies the input `host`;
it is an unchanged callee whose value is the method's input parameter, so it is
modeled as the free input `host`, not axiomatized (no obligation is placed on it).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§4) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the host name; the codec's input and output) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; per code point `ch ↔ Char.ofNat (ord ch)`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]`. On the BMP this is total and exact. |
| "the string is ASCII-safe" (`s.encode('ascii')` would not raise) | `∀ c ∈ out, c.val.toNat < 128` | a Python `str` is ASCII-encodable iff every code point is `< 128`; the Lean predicate is the exact per-code-point statement of that. |
| `domain.encode('idna').decode('ascii')` | `aceEncode : List Char → List Char` | the abstract ACE codec as a pure function `List Char → List Char`; G-AX validates the `aceEncode_ascii` post-condition against the real codec. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point (ASCII-ness is a
per-code-point predicate).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `aceEncode` / `aceEncode_ascii` ↔ the IDNA ACE codec (A-consumed)

**Callee:** the CPython idiom `domain.encode('idna').decode('ascii')` — the
RFC-3490 IDNA "ToASCII" transformation followed by an ASCII decode. The new
helper added by the patch is exactly this idiom; the four pre-existing inline
sites are identical.

**Axiom contract (the WEAKEST sufficient for the fix):** the only property the
modeled fix relies on is that the *result is ASCII* — `aceEncode_ascii` states
`∀ c ∈ aceEncode host, c.val.toNat < 128`. This is precisely what makes the host
name safe to place in a header that is later encoded with a single-byte charset
(the bug: a non-ASCII host crashed `'ascii'`/`'latin-1'` header encoding). We do
**not** axiomatize the exact ACE output value (e.g. that `漢字 → xn--p8s937b`):
that would over-claim the codec's behavior (directive 7) and is unnecessary — the
spec needs only the ASCII guarantee. The exact value is exercised end-to-end by
the F2P test, not pinned in the axiom.

**Why ASCII-ness alone is strong enough (directive 4):** the prepatch returns the
host *unchanged* (`out = host`); a host that is already non-ASCII then violates
`∀ c ∈ out, c.val.toNat < 128`, so the prepatch fails verification on exactly the
clause the bug concerns (G-DIFF). A `mut`-frame `ensures` (`out = aceEncode host`)
additionally pins that the result is *the codec's output*, not an arbitrary ASCII
string an attacker could echo (directive 8: grounded in the real computation, the
A-consumed callee).

**Soundness check (G-AX):** `axiom_check.py` runs the real
`domain.encode('idna').decode('ascii')` on boundary inputs (ASCII labels, CJK
labels including `漢字`/`正宗`, mixed dotted names, latin-accented labels) plus
randomized fuzzing, and asserts that **every successful** observation satisfies
the axiom's post-condition `aceEncode_ascii` (all code points `< 128`). Inputs on
which the real codec *raises* `UnicodeError` (empty/over-long labels) are out of
scope for the axiom: the modeled `get_fqdn` is only reached with a real OS host
name and the axiom constrains only the values the codec actually produces — it
never claims the codec is total. axiom_check.py records the raise rate for
transparency and asserts the post-condition on every non-raising result. Imports
only the Python standard library (the `idna` codec is built in). Exit 0 iff sound.

## 4. G-CONF — skipped (impl region all-A-tagged)

The `punycodeDomain` impl region is a single A-tagged op: `out :| out = aceEncode
host` (the imperative-callee stub for the unchanged ACE codec). There is no R/I
computational content to transliterate and differentially test, so
`meta.json conf_skip=true` and `conformance_check.py` exits with `status=skip`
(SPEC_GUIDE §"conformance_check.py … all-A-tagged"). The A leg's soundness is
covered by G-AX; the refinement narrative by G-EQ.
</content>
</invoke>
