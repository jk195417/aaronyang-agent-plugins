---
name: aaronyang-orchestrating
description: Shape long or multi-part agent work — scope one goal per session, decide what to run here, in a subagent or in a separate session, keep a visible stack of detours, hand work off with provenance, and close a session out (recap, save knowledge, check loose ends, archive). Use when a request has several independent parts, a conversation drifts to a new topic, the user asks to split, hand off, recap, wrap up or archive a session, or asks "what next" after a long stretch of work.
license: CC-BY-SA-4.0
---

# Orchestrating agent work

Long sessions lose detail when context is compacted, and mixed topics make every later step slower. Keep each session to one goal and make every transition explicit.

## Scope

- One session, one goal with a clear "done". Write the goal and the done condition at the start when the request is large.
- Optimize only the bottleneck (Theory of Constraints): do the step that unblocks the most, not the easiest one.
- When a new request is unrelated to the current goal, offer to start it in its own session instead of mixing it in.

## Where work runs

| Run it | When |
|---|---|
| Here | It needs this conversation's context, or a few tool calls settle it |
| Subagent | A self-contained piece (wide search, review, verification) whose result this session needs now |
| Separate session | An independent task with its own outcome (a branch, a PR, a document) that the user may follow or steer on its own |

Parallel pieces must not touch the same files. Verify what a subagent or session reports before calling it done.

## Detours

Keep a visible stack: when the work branches off, say where it came from and roughly how long the detour should take. When the detour runs long, say so and offer to finish it later or move it to its own session. Return to the stack and name the next item when the detour ends.

## Handoff

A handoff brief (to a new session, another machine, or a later day) lets a reader with no context act at once:

1. Goal and done condition.
2. Decisions already made, each marked user-stated, observed, from a reference, or inferred, and verified or not.
3. Current state: what is done, what is in progress, where files and branches are.
4. Next steps in order, and what needs the user (sign-ins, approvals, decisions).
5. Constraints: what must not be changed or sent without asking.

Paths and identifiers in full; no "as discussed above".

## Close-out

Before a session ends or is archived:

1. Recap: what changed, what was verified, what was not.
2. Save what should outlive the session — lessons to the reflection queue (aaronyang-reflection when installed), knowledge to the knowledge base (aaronyang-knowledge-notes when installed), facts to memory, procedures to a skill. Pointers, not copies.
3. Check loose ends: uncommitted or unpushed changes, open PRs, running processes, temporary files, promises made to the user.
4. Name the next goal, and whether it belongs in a new session.
5. Archive only after the user agrees.
