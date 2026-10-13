import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of the
--  five connection-option values: each option is forwarded to the launched client
--  process exactly when it is set, and dropped when it is unset. The option values
--  are read directly from the connection configuration; nothing about how the
--  client process is subsequently launched is consulted, so no callee contract is
--  assumed. Every step is an R/I refinement, validated against the real
--  construction by conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- The canonical name an option is forwarded under. Carried as a `String`; the
   forwarded entry pairs this name with the option's value. -/
abbrev OptName := String

/- One forwarded entry: the option's canonical name paired with its value
   (`List Char`, the option value's code points — mapping.md §2). -/
abbrev Entry := OptName × List Char

/- Forward a single option: when the option is SET (a non-empty value) it
   contributes one entry under its canonical `name`; when it is UNSET (the empty
   value, i.e. absent from the configuration) it contributes nothing. This is the
   per-option rule the whole construction iterates. -/
def forwardOne (name : OptName) (value : List Char) : List Entry :=
  if value ≠ [] then [(name, value)] else []

@[grind] lemma forwardOne_set (name : OptName) (value : List Char) (h : value ≠ []) :
    forwardOne name value = [(name, value)] := by simp [forwardOne, h]
@[grind] lemma forwardOne_unset (name : OptName) :
    forwardOne name [] = [] := by simp [forwardOne]

/- The full set of options forwarded to the launched client process, given the
   five option values in a set configuration order. Each option is
   forwarded under its own canonical name exactly when it is set; the result is
   the in-order concatenation of the per-option contributions. The credentials
   option (`password`) is listed first and is forwarded by the same set-then-keep
   rule; the four transport-security options (`sslmode`, `sslrootcert`,
   `sslcert`, `sslkey`) follow and are forwarded by that identical rule. -/
def forwardedEnv (password sslmode sslrootcert sslcert sslkey : List Char) :
    List Entry :=
  forwardOne "password" password ++
  forwardOne "sslmode" sslmode ++
  forwardOne "sslrootcert" sslrootcert ++
  forwardOne "sslcert" sslcert ++
  forwardOne "sslkey" sslkey

-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the set of connection options forwarded to a freshly launched
   database client process. Each option is read from the connection
   configuration as a value that is either SET (a non-empty value) or UNSET (the
   empty value — the option was not configured).

   Desired behaviour: every configured option must be forwarded to the client
   process under its own name, and an unconfigured option must NOT be forwarded.
   In particular the transport-security options — the connection mode, the
   trusted-authority certificate, and the client certificate and its key
   (`sslmode`, `sslrootcert`, `sslcert`, `sslkey`) — are each forwarded exactly
   when configured, alongside the credentials option that was already forwarded
   this way. The forwarded set is the in-order concatenation of these per-option
   contributions.

   All five option values are read-only (none `mut`): the construction only reads
   them and emits the forwarded set, mutating no input (directive 5). Each value
   is modeled as `List Char` (mapping.md §2); the result is the list of forwarded
   `(name, value)` entries. -/
method clientEnv (password : List Char) (sslmode : List Char)
    (sslrootcert : List Char) (sslcert : List Char) (sslkey : List Char)
    return (out : List Entry)
  ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey
  do
    -- impl-start
    -- Start with nothing forwarded; forward each option, in configuration order,
    -- exactly when it is set (non-empty). The credentials option is forwarded
    -- first by this rule; the four transport-security options follow by the same
    -- rule.
    let mut env : List Entry := []
    if password ≠ [] then
      env := env ++ [("password", password)]
    if sslmode ≠ [] then
      env := env ++ [("sslmode", sslmode)]
    if sslrootcert ≠ [] then
      env := env ++ [("sslrootcert", sslrootcert)]
    if sslcert ≠ [] then
      env := env ++ [("sslcert", sslcert)]
    if sslkey ≠ [] then
      env := env ++ [("sslkey", sslkey)]
    return env
    -- impl-end

prove_correct clientEnv by
  loom_solve <;>
    simp_all [forwardedEnv, forwardOne]
