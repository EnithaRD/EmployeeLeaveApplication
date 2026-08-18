# Prompt Pattern Library

Reusable prompt shapes for working with Claude Code on this repo, built from Day 6's
exercises. Each entry has a name, a template with placeholders, and one real example
that was actually run against this codebase (Employee Leave Application, FastAPI +
React) this week — not a hypothetical.

Where an entry has no real run yet, that's stated explicitly rather than backfilled
with an invented example.

---

## 1. Investigate only

**For:** understanding a part of the codebase before deciding what to change, with an
explicit instruction not to touch anything.

**Template:**
```
This is a [stack/framework] app at [path]. I need context to [decision you're about
to make]. Please investigate and report back:
1. [specific question about structure/behavior]
2. [specific question about conventions]
3. [specific question about an existing pattern to reuse]
Report with file paths and code snippets. This is read-only research — do not modify
any files.
```

**Real example (this week):** two parallel Explore-agent briefs used to scope the
admin monthly-leave-chart feature — one told to map the backend leave endpoints,
models, role-checking convention, and existing aggregation-endpoint style; the other
told to map the frontend Dashboard page, role representation, existing chart/visual
conventions, and confirm no chart library was already installed. Both closed with
"This is read-only research — do not modify any files," and both came back as
structured reports (endpoint tables, code snippets, file:line refs) that the actual
plan was built from directly, instead of being re-derived by hand.

---

## 2. Plan first

**For:** getting an approach approved before any edit lands, for anything that touches
more than one or two files.

**Template:**
```
[Feature request, in full — context, goal, constraints, acceptance criteria]
```
issued while in Plan Mode (Shift+Tab to cycle permission modes), so investigation and
a written plan happen before any tool that could mutate the repo is allowed to run.

**Real example (this week):** "admin dashboard should not display leave balances...
instead the dashboard should display chart that demonstrates how many leaves are
taken each month, in that how much of them were accepted and how many were
rejected... this graph/chart must be displayed only for admin and not other
userroles" — run in Plan Mode. Produced a written plan (new admin-only
`/leaves/monthly-stats` endpoint, a new `LeaveMonthlyChart` component, role-gated
rendering in `Dashboard.jsx`) that was read, questioned, revised once, and only then
approved via `ExitPlanMode` before a single file was touched. See `prompts.md` §6.2
for the full trace.

---

## 3. Scoped change (four-part + binding constraints)

**For:** any implementation prompt where you want a reviewable diff, not a surprise.

**Template:**
```
Context: [what exists today, where, and why it's insufficient]
Goal: [the one thing this prompt should produce]
Constraints: [things that must be true of the *implementation* and are checkable
  against the diff — e.g. line limits, no new dependencies, no new files outside X]
Acceptance criteria: [how you or a test would verify this is done]
```

**Real example (this week):** "verify every function is kept under 30 lines,
existing tests must still pass, unmodified, no new files outside routes, every route
returns a JSON error body, never a raw stack trace, also the data for the chart is
not empty but returns actual values that is stored while accepting and rejecting
leave requests." Every clause here is checkable against the diff: a line-count script
found and fixed three over-length functions (backend and frontend), a global FastAPI
exception handler was added and proven with a live `TestClient(raise_server_
exceptions=False)` call showing `application/json` instead of a stack trace, and a
new integration test drove a leave through the real `/apply` → `/decide` flow to
prove the chart reflects persisted data rather than seeded rows. None of these were
"looks fine" judgment calls — each had a pass/fail check.

---

## 4. Follow this pattern

**For:** getting a new piece of UI or code to match an existing convention instead of
inventing a new one, by naming the reference file directly.

**Template:**
```
[Four-part prompt as above], plus:
Follow this pattern: [style/structure] the same way [existing file:selector] does it,
rather than inventing a new one.
```

**Real example (this week, from Exercise 6.1's Prompt C):** "Follow this pattern:
style the button using the same visual pattern as the reject button in
`frontend/src/pages/leave/Approvals.jsx` (the `inline-flex w-full items-center
justify-center rounded-xl border ... px-3 py-2 text-sm font-semibold ...` button)
rather than inventing a new button style." The resulting plan literally reused that
class string instead of the plausible-but-invented button styles the same prompt
without this line produced (Prompt B chose an unreferenced slate/secondary style;
the decorative-constraints run chose an unreferenced indigo style) — see
`prompts.md` §6.1 and §6.4 for the side-by-side.

---

## 5. Reproduce then fix

**For:** bug fixes — pin down the failure with a test that encodes the exact reported
scenario, then fix, so the fix is provably correct and the scenario can't regress
silently.

**Template:**
```
[Bug report, in the reporter's own words if possible]
Before fixing: add a test that reproduces this exact scenario using the real
[endpoint/flow], not a shortcut. Then fix it. Show me the test failing against the
old behavior conceptually, then passing against the fix.
```

**Real example (this week), with an honest caveat:** when told "past leave approvals
and rejects made by manager are not visible," the response was to identify the root
cause (a rolling-12-month window keyed on `start_date`, unrelated to who decided the
leave), fix it, and add `test_monthly_stats_includes_decisions_made_by_a_manager` —
which applies a real leave through `/apply` and approves it with a **manager** token
via the real `/decide` endpoint, then asserts it appears in the admin's stats. That
test is a faithful reproduction of the reported scenario and would have failed
against the old rolling-window code. It was written *alongside* the fix in the same
turn, not committed failing-first in a separate step — so this is the pattern's
*structure*, not its strict red-green-refactor ordering. Worth doing properly
(test-first, shown failing) next time this pattern is used.

---

## 6. Constrained refactor

**For:** changing the shape of code (splitting functions, extracting components)
without changing behavior — and proving it, via an unchanged test suite.

**Template:**
```
Refactor [file/function] so that [structural constraint, e.g. "every function is
under N lines"]. Do not change behavior. The existing test suite ([N] tests) must
still pass, unmodified, after this change.
```

**Real example (this week):** splitting `Dashboard.jsx`'s single ~100-line render
function into `useDashboardData`, `DashboardHeader`, `ErrorBanner`,
`LeaveBalancesCard`, `LeaveBalanceRow`, and `PendingApprovalsCard` (plus a similar
split in `LeaveMonthlyChart.jsx` and in the backend's `leaves.py`), purely to satisfy
a 30-line-per-function ceiling. Verified with a small line-counting script per
function, a `vite build` after every change, and the full backend suite (48/48, later
51/51) re-run after each split — same behavior, smaller functions, nothing else moved.

---

## 7. Explain this diff

**For:** making a change justify itself before you approve it — useful for output
from another tool, a teammate's PR, or a Claude Code run you weren't watching closely.

**Template:**
```
Explain @[diff/PR/commit] to me: what does each hunk do, why might it have been
written this way, and is there anything here that doesn't match [stated goal /
existing convention]? Don't fix anything — just explain and flag concerns.
```

**Status:** not run this week — no diff came up in this project that needed this
treatment (every change here was authored in the same session it was reviewed in).
Template only; first real run goes here next time.

---

## Credited from a classmate

*Pending: this section is reserved for one pattern swapped in from a classmate's
`prompt-patterns.md`, per Exercise 6.6 step 3. Not filled in yet — no classmate
exchange has happened. Do not merge a fabricated entry here; leave this placeholder
until a real swap occurs.*
