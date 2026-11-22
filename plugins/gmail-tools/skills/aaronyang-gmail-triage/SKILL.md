---
name: aaronyang-gmail-triage
description: Review the Gmail inbox and sort what is there into mail that needs the user's attention, senders that deserve a filter, and documents that belong in the PDF archive. Use when the user asks what in their inbox needs attention, which emails still need rules, which mail should be archived or collected, or for a periodic inbox check.
license: CC-BY-SA-4.0
compatibility: Needs read access to Gmail (a Gmail connector or the Gmail API).
---

# Gmail inbox triage

Read the inbox, then report in three groups. Read only: change nothing in this skill; each follow-up goes through its own skill after the user picks it.

1. **Needs attention** — deadlines, payments due, replies people are waiting for, security alerts the user did not trigger, anything with money or legal effect. For each: sender, subject, date, why it matters, the deadline if any.
2. **Deserves a filter** — recurring senders now landing in the inbox. Group by exact sender address and kind of notice, give the count and a proposed rule (label, archive or not) following the design rules of the `aaronyang-gmail-filters` skill. Suggest unsubscribing instead when that is possible.
3. **Belongs in the PDF archive** — statements, bills, receipts or invoices with PDF attachments from senders not yet in `targets.toml` of the `aaronyang-gmail-pdf-archive` skill (check the file when available). For each: sender, subject pattern, whether the PDF is password protected.

Then ask which group to act on. Look at the actual messages before classifying a sender; one address often sends both notices and marketing.
