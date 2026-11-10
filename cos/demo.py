"""Fictional sample briefing so you can try the dashboard with zero setup."""
from .engine import normalize


def generate(cfg=None):
    return normalize({
        "mode": "demo",
        "summary": "Sample briefing (demo mode — all content is fictional). One alert has fired "
                   "for days without an owner and a launch decision from Tuesday's review was never recorded.",
        "urgent_actions": [
            {"title": "Assign an owner to the recurring checkout-latency alert", "when": "Today",
             "detail": "Alert has fired every few hours for 5 days; no acknowledgement in the on-call channel.", "source": "slack"},
            {"title": "Record the go/no-go decision from the pricing experiment review", "when": "Today",
             "detail": "Readout happened Tuesday; epic is 85% complete but no decision is documented.", "source": "meetings"},
            {"title": "Write acceptance criteria for 3 unassigned triage tickets", "when": "This week",
             "detail": "PROJ-101, PROJ-107 and PROJ-112 have no owner or criteria.", "source": "tickets"}],
        "slack_highlights": [
            {"title": "Design asked for a decision on onboarding copy", "detail": "Thread in #product-design, waiting 1 day.", "action": True},
            {"title": "Eng shared a rollout plan for the search revamp", "detail": "No action needed; FYI.", "action": False}],
        "email": [
            {"title": "Quarterly planning template from your manager", "detail": "Due Friday.", "action": True}],
        "meeting_notes": [
            {"title": "Pricing experiment readout", "bullets": ["Treatment shows +2% conversion", "Guardrail metrics flat"],
             "actions": ["Document go/no-go decision"]}],
        "project_updates": [
            {"id": "PROJ-14", "title": "Consolidate onboarding flow", "status": "at_risk",
             "detail": "85% complete; blocked on the unrecorded decision."},
            {"id": "PROJ-22", "title": "Search revamp", "status": "on_track", "detail": "Rollout plan shared."}],
        "coming_up": [
            {"when": "Today 2:30 PM", "title": "Cross-team sync (covering for a teammate)", "prep_needed": True},
            {"when": "Thu", "title": "Bi-weekly planning and grooming", "prep_needed": True}],
        "source_errors": [],
    })
