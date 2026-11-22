# Designing filters

The inbox holds only mail that needs attention (Inbox Zero); labels exist to find mail later. Rules follow event-condition-action: one condition, one action.

1. **One rule, one condition.** Labeling, skipping the inbox and marking read are separate actions; the tool turns each into its own filter, so a message matching several rules gets all of them.
2. **Smallest unit: one source × one kind of notice.** Prefer an exact sender address (plus a subject phrase when one address sends several kinds) over a whole domain, which mixes notices, receipts and marketing. Small rules change without touching others; do not merge them into one big sender list.
3. **Unlabeled mail stays in the inbox** so it gets seen. Archive only mail that is labeled or is noise.
4. **Archiving does not mark read** unless the user asks for it.
5. **Allowlists for receipts and statements:** sender plus subject keywords that mean "this is the document" (invoice, receipt, statement). Marketing from the same sender stays out.
6. **Blocklists for marketing from mixed senders** (e.g. banks): match marketing keywords, but exempt anything about payments, debits, statements, transaction results, and replies or forwards (`RE`, `FW`). Real notices stay in the inbox.
7. **Login and security notices** get their own label; archive routine ones, keep new-device alerts in the inbox.
8. **Unsubscribe first.** A filter is for senders that cannot be unsubscribed or that you want to keep.
9. **Check before trusting.** Search Gmail with the exact criteria before adding a rule; after applying, audit recent mail. A skip-inbox rule must contain at least one positive term — a rule built only from exclusions matches nearly everything.
10. **Write down the why.** Keep a human-readable list of rule decisions (in the user's notes) next to `filters.toml`, and point it to `filters.toml` instead of copying the rules.
