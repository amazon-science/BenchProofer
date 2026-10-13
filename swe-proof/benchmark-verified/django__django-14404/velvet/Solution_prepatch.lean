import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The deployment mount point under which a request is
--  served is an environment-supplied prefix that is prepended, verbatim, to the
--  per-request local path to recover the request's full, client-facing
--  path. That full path is modeled DEEPLY (`fullPath` below) as the
--  concatenation of the two carriers, and `fullPath == the request's real full
--  path` is validated executably by axiom_check.py (G-AX) — an A-reference, not
--  a consumed axiom. Nothing about an unchanged library callee is assumed.)
-- axioms-end

-- pure-start
/- The request's full, client-facing path: the deployment mount-point
   prefix under which the application is served, followed by the per-request
   local path. When the application is mounted at the server root the prefix is
   empty and the full path coincides with the local path; otherwise the prefix
   is a genuine, non-empty component of every client-facing URL.

   This is a deep model of the request's full path (an unchanged framework
   attribute); `fullPath == that real attribute` is validated by axiom_check.py
   (G-AX), so it is an A-reference, not a consumed axiom. -/
def fullPath (mountPrefix localPath : List Char) : List Char :=
  mountPrefix ++ localPath

/- The trailing-slash redirect destination: the request's full path with a
   single '/' appended. The destination is assembled from the FULL path — the
   client-facing one that includes the deployment mount-point prefix — so
   that a client served under a non-root mount point is redirected to a URL that
   stays under that same mount point. -/
def redirectTarget (mountPrefix localPath : List Char) : List Char :=
  fullPath mountPrefix localPath ++ ['/']

@[grind] lemma redirectTarget_def (mountPrefix localPath : List Char) :
    redirectTarget mountPrefix localPath = mountPrefix ++ localPath ++ ['/'] := by
  simp [redirectTarget, fullPath, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the trailing-slash redirect destination for a request that is missing
   its trailing slash, from two read-only inputs:

   - `mountPrefix`: the deployment mount-point prefix under which the
     application is served (empty when mounted at the server root, a genuine
     non-empty prefix otherwise);
   - `localPath`: the per-request local path within the application.

   Neither input is mutated (directive 5). The destination MUST be built from
   the request's FULL client-facing path — the mount-point prefix followed
   by the local path — with a single trailing '/' appended, so that the prefix
   is preserved in the redirect. A destination assembled from the local path
   alone would strip the mount-point prefix and send the client outside the
   application's mount point; that is exactly the behaviour this specification
   forbids. -/
method appendSlashRedirect (mountPrefix : List Char) (localPath : List Char)
    return (out : List Char)
  ensures out = redirectTarget mountPrefix localPath
  ensures out = mountPrefix ++ localPath ++ ['/']
  ensures ∃ rest, out = mountPrefix ++ rest
  do
    -- impl-start
    -- Pre-image skeleton: the destination is assembled from the per-request
    -- LOCAL path alone, with a single trailing '/' appended. The deployment
    -- mount-point prefix is never prepended, so whenever the application is
    -- served under a non-empty mount point the frozen spec (which requires the
    -- full, prefix-including path) is not met and prove_correct MUST fail.
    let result := localPath ++ ['/']
    return result
    -- impl-end

prove_correct appendSlashRedirect by
  loom_solve
  all_goals first
    | (exact ⟨localPath ++ ['/'], by simp [fullPath, List.append_assoc]⟩)
    | simp [redirectTarget, fullPath, List.append_assoc]
