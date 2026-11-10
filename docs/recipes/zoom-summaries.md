# Recipe: compile meeting AI summaries into a Word doc

Zoom (and similar tools) email AI-generated meeting summaries. With a search source connected
(e.g. Glean or an email MCP) you can collect them into one document. Paste into Claude Code:

```
Pull all of my Zoom AI meeting summaries from my email for [TIME PERIOD, e.g. "the last 3 months"
or "April 2026"]. Zoom sends these as emails whose subjects start with "Meeting assets" — search
for those emails. For each meeting found, extract the full AI-generated summary (quick recap, key
discussion points, action items). Compile everything into a Word document saved to my Desktop, with
one section per meeting showing the meeting name, date, attendees and full summary content.
If a meeting has no AI summary (just a recording link), skip it.
```

Tips
- Replace `[TIME PERIOD]` with a specific month or range; name one month explicitly to keep the doc focused.
- Needs Claude Code with a search/email MCP connected to the mailbox the summaries arrive in.
- Output name suggestion: `Zoom_AI_Meeting_Summaries_[Month]_[Year].docx`.
- The same pattern works for Meet/Teams notification emails — change the subject prefix.
