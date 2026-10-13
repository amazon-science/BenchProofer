import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. This operation renders a resolved-URL match object as a
   single human-readable text line. Every component the line is built from is
   already in hand as a value on the match record (the callable's identity and
   its two textual forms, the already-rendered argument/keyword/name-list
   components, and the optional name and route strings); there is no unchanged
   callee whose contract the proof consumes, hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable slice of a resolved-URL match that the text rendering reads:

     * `isPartialFunc`  — whether the matched callable is a partial-application
                          callable (one carrying pre-bound arguments). Such a
                          callable is shown by its full textual form so the
                          underlying callable and its bound arguments are
                          visible; an ordinary callable is shown by its
                          dotted-path form instead;
     * `funcPartialText` — the full textual form of a partial-application
                          callable (used only when `isPartialFunc`);
     * `funcPath`       — the dotted import path of an ordinary callable;
     * `argsText`       — the already-rendered positional-argument tuple;
     * `kwargsText`     — the already-rendered keyword-argument mapping;
     * `urlName`        — the optional symbolic name of the match;
     * `appNamesText`   — the already-rendered application-namespace list;
     * `namespacesText` — the already-rendered instance-namespace list;
     * `route`          — the optional route pattern string of the match.

   The two textual `func` forms and the three already-rendered list/mapping
   components are carried verbatim (mapping.md §2): they are produced by
   rendering operations this line does not itself vary. The optional name and
   route are carried as their underlying strings so the quoted form below is
   computed here. -/
structure MatchView where
  isPartialFunc : Bool
  funcPartialText : String
  funcPath : String
  argsText : String
  kwargsText : String
  urlName : Option String
  appNamesText : String
  namespacesText : String
  route : Option String
deriving DecidableEq

/- A hexadecimal digit character for a value below sixteen: `0`-`9` then
   `a`-`f` (lowercase). -/
def hexDigit (n : Nat) : Char :=
  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (87 + n)

/- One character of a quoted textual form: the escape character and the
   wrapping quote mark render escaped (preceded by the escape character);
   the tab, line-feed and carriage-return controls render as their
   two-letter escape codes; any other control character, and the delete
   character, renders as a two-hex-digit escape; every other character
   renders as itself. -/
def escChar (delim : Char) (c : Char) : String :=
  if c = '\\' then "\\\\"
  else if c = delim then "\\" ++ String.singleton delim
  else if c = '\t' then "\\t"
  else if c = '\n' then "\\n"
  else if c = '\r' then "\\r"
  else if c.toNat < 32 ∨ c.toNat = 127 then
    "\\x" ++ String.singleton (hexDigit (c.toNat / 16))
          ++ String.singleton (hexDigit (c.toNat % 16))
  else String.singleton c

/- The quoted textual form of a string value: the value wrapped in quote
   marks, each inner occurrence of the wrapping mark or the escape character
   escaped, and each control character rendered by its escape code. The
   wrapping mark is the single quote, except that a value containing a
   single quote but no double quote wraps in double quotes instead (so no
   inner escaping of the quote is needed in that case). (Faithful across
   the whole ASCII plane, the modeled domain of the name and route strings;
   mapping.md §2.) -/
def quoted (s : String) : String :=
  let delim : Char := if s.contains '\'' && !(s.contains '"') then '"' else '\''
  String.singleton delim
    ++ String.join (s.toList.map (escChar delim))
    ++ String.singleton delim

/- The textual form of an optional string field: an absent value renders as the
   literal `None`; a present value renders quoted. -/
def quotedOpt (o : Option String) : String :=
  match o with
  | none   => "None"
  | some s => quoted s

/- An optional string drawn from the ASCII plane — the modeled domain of the
   symbolic name and route pattern (the graded inputs are ASCII; outside it
   the printability classification of the underlying text rendering is
   standard-library specific and is not claimed; mapping.md §2). -/
def asciiOpt : Option String → Prop
  | none   => True
  | some s => ∀ c ∈ s.toList, c.toNat < 128

/- The full text line a resolved-URL match renders to. The callable component
   is the partial-application callable's full textual form when the callable is
   one, otherwise its dotted import path. The optional symbolic name and route
   render quoted (an absent one as `None`); the positional/keyword/list
   components are inserted by their already-rendered text. -/
def matchRepr (m : MatchView) : String :=
  let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
  "ResolverMatch(func=" ++ funcStr ++
  ", args=" ++ m.argsText ++
  ", kwargs=" ++ m.kwargsText ++
  ", url_name=" ++ quotedOpt m.urlName ++
  ", app_names=" ++ m.appNamesText ++
  ", namespaces=" ++ m.namespacesText ++
  ", route=" ++ quotedOpt m.route ++ ")"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a resolved-URL match as its text line: a partial-application callable
   shown by its full textual form (exposing the underlying callable and its
   bound arguments), an ordinary callable by its dotted path, and the symbolic
   name and route shown quoted. The name and route range over the ASCII plane
   (the modeled domain; mapping.md §2). -/
method resolverMatchRepr (m : MatchView) return (out : String)
  require asciiOpt m.urlName
  require asciiOpt m.route
  ensures out = matchRepr m
  do
    -- impl-start
    -- Pre-image skeleton: the optional symbolic name and route are inserted by
    -- their underlying string (an unquoted textual form), without surrounding
    -- quotes. The frozen spec (`matchRepr`) shows these fields quoted, so
    -- `prove_correct` MUST fail on the `url_name`/`route` clauses.
    let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
    let nameStr := match m.urlName with | none => "None" | some s => s
    let routeStr := match m.route with | none => "None" | some s => s
    return "ResolverMatch(func=" ++ funcStr ++
      ", args=" ++ m.argsText ++
      ", kwargs=" ++ m.kwargsText ++
      ", url_name=" ++ nameStr ++
      ", app_names=" ++ m.appNamesText ++
      ", namespaces=" ++ m.namespacesText ++
      ", route=" ++ routeStr ++ ")"
    -- impl-end

prove_correct resolverMatchRepr by
  loom_solve <;> simp_all [matchRepr]
