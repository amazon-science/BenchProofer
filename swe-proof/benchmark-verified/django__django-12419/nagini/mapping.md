# mapping.md — django__django-12419

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7fa1a93c6c8109010a6ff3f604fda83b604e0e97`, states the type
abstraction, and gives the provenance of the one kind-A reference (the deep
model validated against a real callee chain by G-AX).

Repo files involved:
- `django/conf/global_settings.py` — the changed default (the gold hunk).
- `django/middleware/security.py` — the unchanged consumer (`SecurityMiddleware`)
  that turns the default into the observable `Referrer-Policy` header.
- `django/http/response.py` — the unchanged `HttpResponseBase.setdefault`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `apply_referrer_policy(slot)` | the referrer-policy branch of `SecurityMiddleware.process_response` — `django/middleware/security.py:47-53` (the `if self.referrer_policy: response.setdefault('Referrer-Policy', …)` block) | the modeled behaviour: attach the header to the outgoing response under the configured policy |
| the `policy` local in the impl region (`[115,97,…,110]`) | `self.referrer_policy = settings.SECURE_REFERRER_POLICY` — `django/middleware/security.py:18`, sourced from `SECURE_REFERRER_POLICY` — `django/conf/global_settings.py:640` | the configured policy value the change edits (the carrier of the gold change) |
| `baseline_policy()` | the post-change value `'same-origin'` of `SECURE_REFERRER_POLICY` (`global_settings.py:640` post-patch) | pure spec: the non-empty baseline policy value as code points |
| `HeaderSlot{present,value}` | the `Referrer-Policy` slot of the `HttpResponse._headers` mapping (touched by `response.setdefault('Referrer-Policy', …)`, `setdefault` at `django/http/response.py:204-207`) | minimal model of the touched response fields: header-present flag + header value |
| `normalized_policy(s)` *(deep model — A-reference)* | the value expression `','.join([v.strip() for v in self.referrer_policy.split(',')] if isinstance(self.referrer_policy, str) else self.referrer_policy)` — `django/middleware/security.py:50-52` | pure spec: per-token whitespace-trim + comma-rejoin; deep model of the unchanged value-construction chain, validated `normalized_policy == real chain` (on its modeled domain) by axiom_check.py (G-AX), NOT consumed as an axiom |
| `is_ws` / `has_ws` / `has_comma` | the whitespace semantics of `str.strip()` and the `,` split delimiter | pure spec helpers fixing the deep model's modeled domain (single token, no comma, no whitespace) |

The pre-patch value the change replaces (for the refinement audit, not
referenced from the consumer spec view): `SECURE_REFERRER_POLICY = None`
(`global_settings.py:640` pre-patch) — a falsy configured value, so the
`if self.referrer_policy:` guard is false and the header is never attached.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` policy value / header value | `List[int]` of Unicode code points | `s[k]` ↔ `policy[k] == ord(s[k])`; `len(s)` ↔ `len(policy)`; empty/`None`/falsy `str` ↔ `[]`; specification carried by `PSeq[int]` via `ToSeq` |
| `self.referrer_policy` truthiness `if self.referrer_policy:` | `len(policy) > 0` | a non-empty `str` is truthy; `None`/`''` is falsy ↔ `len(policy) == 0` |
| `response` header slot + `response.setdefault('Referrer-Policy', value)` | `HeaderSlot.present` / `HeaderSlot.value`; "set only if absent" ↔ the `if not slot.present:` guard | `setdefault` writes the value iff the key is absent; an already-present header is preserved (modeled by leaving `slot` untouched and the `Old(slot.present) ⇒ slot.value is Old(slot.value)` postcondition) |
| `','.join([v.strip() for v in p.split(',')])` | `normalized_policy(ToSeq(policy))` | identity on a comma-/whitespace-free single token (mapping.md §3); the baseline `'same-origin'` is exactly such a token |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A reference — checked by G-AX / axiom_check.py)

### 3.1 `normalized_policy` deep model ↔ the `','`-join / strip chain (A-reference)
**Callee chain:** `','.join([v.strip() for v in policy.split(',')])`
(`django/middleware/security.py:50-52`). When `self.referrer_policy` is a
`str` (Django's default is a `str`), the `isinstance(..., str)` branch is taken
and the value is built by this chain. The chain is modeled **deeply** by the
`@Pure normalized_policy` (with `is_ws`/`has_comma`/`has_ws`) in the `pure`
region; there is **no consumed `@ContractOnly` axiom**. The deep model is
validated equal to the real chain out-of-band by axiom_check.py (G-AX),
restricted to the property the proof consumes:

> **`normalized_policy(s) == s`** for any single token `s` that contains **no
> comma and no ASCII whitespace.**

For such a token, `p.split(',') == [p]`, `p.strip() == p` (no surrounding
whitespace), and `','.join([p]) == p` — so the chain is the identity, which is
what `normalized_policy` returns. The pinned baseline `'same-origin'`
(`PSeq(115,97,109,101,45,111,114,105,103,105,110)`) is exactly such a token, so
the header value the F2P test observes is `same-origin` verbatim. G-AX asserts
`real_chain(s) == normalized_policy(s)` on the baseline + 13 boundary single
tokens + 20 000 fuzz comma-/whitespace-free tokens, and confirms the chain is
genuinely non-identity off that domain (so the restriction is non-vacuous).

**Flag/configuration dependency:** soundness holds for the `str` policy path
(`isinstance(self.referrer_policy, str)` True), which is the path Django's
`str` default takes. axiom_check.py runs the `str` chain. The iterable-of-
values branch is not exercised by the modeled baseline behaviour.

`axiom_check.py` imports only the standard library (`random`, `string`, `sys`);
the real chain is a plain `str`-method composition with no repo-specific
import. Exit 0 iff sound.
