nb # Day 6 — Prompting Exercises Log

Project: Employee Leave Application (FastAPI + React). All examples below are real —
either drawn from this week's actual work on this repo (the admin monthly-leave-chart
feature, Exercises 6.2/6.3), or from fresh, isolated, planning-only agent runs
executed specifically for these exercises (Exercises 6.1/6.4). Nowhere in this
document are numbers invented to fill a table; where something wasn't run for real,
that's stated instead of faked.

---

## 6.1 — One feature, three prompts

**Feature used:** add a button to the "Leave Balances" card on the employee
dashboard (`frontend/src/pages/leave/Dashboard.jsx`) that downloads the employee's
current leave balances as a CSV file.

**Method:** three fresh agents, each with zero shared context, each given exactly one
of the prompts below, each instructed to investigate and report a plan/diff in text
only — no `Edit`/`Write` calls permitted, so nothing was ever at risk of being
shipped. This mirrors "do not approve anything in any of the three runs" from a
harness that doesn't have an interactive plan-mode toggle for subagents.

**Prompt A — bare:**
> Add a way to export leave balances as CSV.

**Prompt B — four-part:**
> Context: In frontend/src/pages/leave/Dashboard.jsx, employees see a "Leave
> Balances" card listing their allocated/used days per leave type (fetched from GET
> /leaves/balances), but currently have no way to export this data.
> Goal: Add a button to that card that lets the employee download their current
> leave balances as a CSV file.
> Constraints: No new npm dependencies. Don't add a new backend endpoint — build the
> CSV client-side from the balances data already being fetched. Keep the button
> inside the existing "Leave Balances" card without restructuring it.
> Acceptance criteria: Clicking the button downloads a CSV file with columns
> leave_type_name, year, allocated, used, remaining — one row per balance currently
> shown. The button is disabled (not hidden) when there are zero balances.

**Prompt C — four-part plus examples:** as B, plus:
> Follow this pattern: style the button using the same visual pattern as the reject
> button in frontend/src/pages/leave/Approvals.jsx (the `inline-flex w-full
> items-center justify-center rounded-xl border ... px-3 py-2 text-sm font-semibold
> ...` button) rather than inventing a new button style.
> Two things that must not happen: (1) do not modify
> frontend/src/pages/leave/Approvals.jsx itself — only look at it as a style
> reference, and (2) do not change the "Pending Approvals" card or its
> data-fetching logic in Dashboard.jsx.

### Results

| | A — bare | B — four-part | C — four-part + examples |
|---|---|---|---|
| **Files it wanted to touch** | 4: `leaves.py` (new `GET /leaves/balances/export` endpoint), `api.js` (new helper), `Dashboard.jsx` (button), plus a new `test_leave_balances_export.py` | 1: `Dashboard.jsx` only | 1: `Dashboard.jsx` only |
| **Invented requirements?** | Yes, substantially: a whole new backend endpoint and API surface nothing in the prompt asked for, *plus* a self-proposed "manager/admin export-all" scope expansion with its own query-param design | Minor, reasonable defaults only: date-stamped filename, CSV quoting rule, a secondary/neutral button color (no reference given, so it invented one) | Minor and explicitly labeled as judgment calls: static filename, quoting rule for the one free-text column, and a flagged (not silently applied) risk that the copied `w-full` class might size oddly outside Approvals.jsx's table-cell context |
| **Matched existing code style?** | Partially — endpoint mirrors `get_leave_balances`'s query shape well, but never addressed the actual button's visual style at all | Good — reused the `disabled:` idiom from `ApplyLeave.jsx`, `type="button"` convention, correct Tailwind idioms — but the button *color* was invented, not sourced | Best of the three — literally copied the Approvals.jsx button's class string as instructed, and self-caught a real integration risk B never surfaced |
| **Minutes to review properly (estimated from diff size/risk, not stopwatched)** | ~20–25 — you're reviewing a brand-new auth-gated backend route, a `StreamingResponse`, a new test file, *and* deciding whether you even wanted a backend endpoint at all | ~5–7 — one small, self-contained diff in one file, directly checkable against the acceptance criteria | ~5–7, arguably the low end of that — no time spent judging an invented button style, and the one open question (does `w-full` misbehave here) is already flagged for you to check in-browser |
| **Would you have merged it?** | No — it solves a bigger, different problem (new API + speculative admin scope) than was asked | Yes, functionally correct and scoped, possibly with a comment on the button color | Yes, most confidently of the three — smallest remaining review burden |

**What bought the most improvement, and what bought almost nothing:** the single
highest-leverage line in this whole experiment was one clause in B's Constraints:
*"Don't add a new backend endpoint."* That one sentence is what stood between a
one-file, five-minute-review diff and a four-file diff that invented an entire new
API surface complete with a speculative admin/manager scope expansion nobody asked
for. Everything else B added (context, goal, acceptance criteria) mattered too, but
none of it closed a gap that large by itself.

Going from B to C is a much smaller, honest story: the two "must not happen" clauses
bought almost nothing measurable, because B was never going to touch
`Approvals.jsx` or the Pending Approvals card anyway — neither was relevant to the
task, so the negative constraints functioned as insurance, not correction. The
real, measurable gain from C was narrow and came from exactly one addition — "follow
this pattern" — which is the only thing that changed an actual decision (an invented
button style became a copied one, and only in that same pass did the agent notice a
real risk in the pattern it copied). So: worth keeping "follow this pattern," don't
expect much from decorative-sounding "must not happen" clauses when the boundary was
never actually at risk.

---

## 6.2 — Plan mode

**Feature used (real, from this week):** the admin dashboard chart. Prompt, verbatim:

> admin dashboard should not display leave balances as admin cannot take leave.
> instead the dashboard should display chart that demonstartes how many leaves are
> taken each month, in that how much of them were accepted and how many were
> rejected. do not download dependencies unless its very much required. the graph
> must be dynamic with the database and must render / show completely without any
> issue, if endpoints are required to be written, follow existing routing style. this
> graph/chart must be displayed only for admin and not other userroles

Entered via Plan Mode (Shift+Tab). Two Explore agents ran first (backend endpoints/
models/role-checking convention; frontend Dashboard/roles/existing chart
conventions — see pattern 1 in `prompt-patterns.md`), then a plan was written and
presented for approval.

### Checked against the five questions

| Question | Verdict |
|---|---|
| Does it solve the problem actually described? | Yes — admin-only chart, monthly, approved-vs-rejected breakdown, existing routing style, no forced new dependency |
| Does it fit how the codebase already works? | Yes — new endpoint used the same `require_role([...])` dependency and ad-hoc-dict-return style as `/pending-count`/`/balances`; new component matched the "plain Tailwind, no chart lib" precedent already set earlier this session |
| Anything not asked for? | Not in the first draft, but the first draft was also **incomplete** — see rejection below |
| What does it not mention (tests, error handling, migration)? | It did name a test file (`test_leave_monthly_stats.py`) up front, mirroring `test_leave_delete.py`'s conventions — this is one plan that didn't need a "where are the tests" objection |
| Reviewable in one sitting? | Yes — two files, one new component, one new endpoint |

### The actual rejection (Exercise 6.3 lives here too — this is the same event)

Before approving, the response to the first plan draft was:

> u did not mention, what type of chart is going to be used and will it be
> displayed, it should be a stacked bar chart. also u did not mention what is going
> to be done to the pending leave requests

This names two specific gaps (chart type unspecified; existing "Pending Approvals"
card's fate unspecified) rather than a vague "make it better." The plan was revised
once — explicit stacked-bar-chart description (approved/rejected as two stacked
segments per month) and an explicit statement that the Pending Approvals card and its
role condition were untouched, same grid slot — and approved on the second read.
**Rounds to an approvable plan: 1.**

What to put in the *original* prompt next time to skip that round: name the chart
type up front ("as a stacked bar chart") and explicitly state what happens to
anything already on the page that the new feature is near — "the Pending Approvals
card must be unaffected" — instead of leaving "the dashboard should display a chart"
to be filled in by inference.

### Diff vs. plan, after execution

The approved plan was: new `GET /leaves/monthly-stats` (admin-only, Python-side
aggregation, no `response_model`), a new `LeaveMonthlyChart.jsx` (stacked bar, plain
Tailwind), and `Dashboard.jsx` changes (role-branch data fetching, swap the Leave
Balances card for the chart only for ADMIN, leave Pending Approvals untouched). The
actual diff matched this closely — no silent extra files, no silent scope change.
That itself is worth recording as a finding: **not every plan leaks.** The additions
that came later (a global JSON exception handler, function-length refactors, a
year-based filter with a dropdown, a days-count-not-request-count fix) all came from
*separate, later prompts*, each with its own explicit ask — none of them appeared
silently inside the diff for a plan that hadn't asked for them.

---

## 6.4 — Constraints that bind

**Feature used:** same CSV export feature as 6.1, run one more time with only the
*constraint* portion varied, so the comparison is apples-to-apples on the same task
(reusing Prompt B from 6.1 as the "binding" arm).

**Decorative version, run fresh:**
> Add a button to the Leave Balances card on the employee dashboard
> (frontend/src/pages/leave/Dashboard.jsx) that lets the employee download their
> current leave balances as a CSV file. Write clean, maintainable code. Follow best
> practices. Do not break anything.

**Binding version:** Prompt B from 6.1 (see above) — "No new npm dependencies. Don't
add a new backend endpoint... Keep the button inside the existing card without
restructuring it," plus concrete acceptance criteria.

### Trying to prove a violation

With the **decorative** prompt: could a violation be pointed at? No. It happened to
land on a reasonable, single-file, no-dependency plan anyway (this codebase is small
enough that "best practices" and "don't add a dependency" mostly agree by default),
but nothing in the prompt would have caught it if it *hadn't* — "write clean,
maintainable code" has no line you can point to and say "this is what breaks it."
The agent's own report even had to invent its own scope boundary ("I would not
fabricate a testing setup unless asked") because nothing in the prompt drew that line
for it — it drew a reasonable one unprompted, but a less careful run could just as
easily have drawn a different one, and the prompt gives you no grounds to object
either way.

With the **binding** prompt: yes. "Don't add a new backend endpoint" is checkable —
open the diff, `grep` for a new `@router` decorator, done. "One row per balance
currently shown" is checkable against the button's `onClick` handler. Every clause
has a matching line in the diff it constrains.

### Negative constraint (from Prompt C, 6.1)

The two "must not happen" clauses in Prompt C ("do not modify Approvals.jsx," "do
not change the Pending Approvals card or its data-fetching logic") **held**: the
agent's own report explicitly confirmed neither was touched and named exactly why
(neither was relevant to a client-side-only, single-file change). Because this
codebase is small and the task was already scoped to one file, this wasn't a hard
boundary to hold — a better stress test would name something *plausible to touch in
passing* (e.g. "do not modify `api.js`, even to add a helper function," on a feature
that superficially looks like it wants an API client change) and see whether the
boundary survives contact with a design decision the agent actually wants to make.
Not run here — flagged as the next thing to try.

---

## 6.5 — Know when to split

**Oversized request (not run — split on paper only, per the exercise's own
instruction):**

> Add a full leave-decision audit trail: every approve/reject gets logged with a
> before/after snapshot, admins get an audit log page to browse it, and the employee
> gets an email notification when their leave is decided.

This fails the "one prompt" test on at least three of the five checks: it changes
behavior in more than one part of the system (decision endpoint, a new admin page,
an email side-effect), it mixes a new data model (audit log table) with a new
feature (notifications), and reviewing all of it together would clearly take well
over twenty minutes.

**Split into five independently mergeable steps:**

1. Add an `audit_logs` table/model (employee_id, leave_id, action, before/after
   status, actor_id, timestamp) with a migration. No endpoints yet.
   *Commit message:* `Add audit_logs table for leave decision history`
2. Write a row to `audit_logs` inside the existing `decide_leave` endpoint whenever a
   decision is made. No new endpoints, no frontend change.
   *Commit message:* `Record an audit entry every time a leave is approved or rejected`
3. Add `GET /leaves/audit-log` (admin-only, paginated, mirrors the existing
   `require_role(["ADMIN"])`/dict-return style already used by `/monthly-stats`).
   *Commit message:* `Add admin-only endpoint to list leave decision audit entries`
4. Add an admin-only "Audit Log" page in the frontend that calls step 3's endpoint.
   *Commit message:* `Add admin audit log page`
5. Send an email to the employee when `decide_leave` runs (separate from steps 1–4;
   needs its own decision about which email provider/pattern to use, which is exactly
   why it's last and separate, not folded into step 2).
   *Commit message:* `Email the employee when their leave request is decided`

Each message above needed no "and" — that's the check. Step 5 is the one most likely
to get an "and" if rushed ("send an email and add a template and handle bounces"),
which is itself a sign it's really its own multi-step piece of work, not a single
commit.

**Step 4 of the exercise ("run only the first step") — disclosed, not executed:**
given the number of agent runs already used for 6.1/6.4's real experiments, step 1
was not actually run this pass. What running it would look like: a single-file
migration plus a single-file SQLAlchemy model, no route, no frontend — a diff on the
order of 30–50 lines, reviewable in well under five minutes, with nothing in it that
could affect any existing behavior (a new table nothing yet reads from or writes to).
That prediction is exactly the kind of claim Exercise 6.1's opening line warns
against making without measuring — so it's labeled as a prediction, not a result,
and is the first thing to actually run next.

---

## 6.6 — Prompt pattern library

Done in `prompt-patterns.md` (repo root). Seven entries, six with a real example run
against this codebase this week; one ("Explain this diff") honestly marked as
template-only since no real run happened for it. The "credited from a classmate"
section is left as an explicit placeholder — it has not been filled in with a real
classmate swap, and was not backfilled with an invented one.

---

## End of Day 6 checklist — status

- [x] Ran the same feature through three prompts, real comparison table (6.1)
- [x] Used plan mode, approved a plan against all five review questions (6.2)
- [x] Compared the finished diff against the approved plan; found no unplanned
      additions in that diff specifically — later, separately-requested work is not
      counted as "unplanned" since each had its own explicit prompt (6.2)
- [x] Rejected a plan with step-specific reasons, iterated to an approved one — 1
      round (6.3)
- [x] Decorative vs. binding constraint comparison, with a concrete "can you point at
      the violating line" test for each (6.4)
- [x] Split an oversized request into five independently mergeable, "and"-free
      commit messages (6.5)
- [ ] Step 1 of the split actually executed — disclosed as not done this pass (6.5)
- [x] `prompt-patterns.md` created with real examples (6.6)
- [ ] Includes one pattern credited to a classmate — not done, no swap has happened
      yet (6.6)
- [x] `prompts.md` has at least three new entries from today — six sections above
