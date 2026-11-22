---
name: aaronyang-reflection
description: Capture lessons and improvement ideas into the user's reflection queue as they happen, and periodically review the queue to decide where each lesson belongs — a rule with evals, a skill, a hook, a note, a life principle, or letting it go. Use when something went wrong or was learned during work, when the user says to remember a lesson or "記下來／反省", or asks to review, prioritize or clean up the reflection queue.
license: Apache-2.0
---

# Reflection queue

Continuous improvement of the way of working itself: capture cases, review them in batches, and move each lesson to the one place where it changes behavior (PDCA, Kaizen).

## Where the queue lives

Read the user's instruction files for the queue's location (a database or a file in their knowledge base); otherwise ask. Follow its existing fields. A queue usually has: title, status (pending / in progress / done / let go), kind (reflection / improvement / to-do / idea), area (for example life / agent), impact 1–5, cost 1–5, what was learned, disposition, related notes.

## Capture

When a mistake, surprise or lesson happens:

1. Search the queue first; extend an existing case instead of adding a duplicate.
2. Write the case as an After Action Review: what was expected, what happened, why, what to do next time. Keep it concrete: dates, what was observed, what was verified.
3. Blameless: describe the system and the steps, not a person's fault.
4. Estimate impact and cost; leave the disposition empty unless it is already obvious and done.

Capture in the moment and keep it short; review is a separate step.

## Review

1. List pending items by priority: impact × 2 − cost + weeks waited (a simple WSJF with aging, so small items cannot starve).
2. For each item, pick one disposition by asking where it would change behavior:

   | Disposition | Use when |
   |---|---|
   | Rule + evals | It applies to every task; write it with the aaronyang-writing-rules skill when available, and verify with evals |
   | Skill | It is a procedure for one kind of task |
   | Hook | A single miss would cause harm, so it must be enforced |
   | Note | It is knowledge for people; ingest with the aaronyang-knowledge-notes skill when available |
   | Life principle | It is about how the user lives or decides, not about tools |
   | Let go | It will not recur, or fixing it costs more than it saves |

3. Propose the dispositions to the user, then apply the approved ones and fill in "what was learned" with where the lesson now lives (a pointer, not a copy).
4. Mark items done or let go. An item done only in part stays in progress with the remaining step written down.

## Privacy

Real cases stay in the user's private queue. Only distilled principles may go to shared or public places, and evals use synthetic cases with the same structure.
