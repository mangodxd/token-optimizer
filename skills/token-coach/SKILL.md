---
name: token-coach
description: Context window coach. Proactive guidance for token-efficient Claude Code projects, multi-agent systems, and skill architecture.
---

# Token Coach: Plan Token-Efficient Before You Build

Interactive coaching for Claude Code architecture decisions. Analyzes your setup, identifies patterns (good and bad), and gives personalized advice with real numbers.

**Use when**: Building something new, existing setup feels slow, designing multi-agent systems, or want a quick health check.

---

## Phase 0: Initialize

1. **Resolve measure.py path** (same as token-optimizer):
```bash
MEASURE_PY=""
if [ -f "$HOME/.claude/skills/token-optimizer/scripts/measure.py" ]; then
  MEASURE_PY="$HOME/.claude/skills/token-optimizer/scripts/measure.py"
else
  MEASURE_PY="$(find "$HOME/.claude/plugins/cache" -path "*/token-optimizer/scripts/measure.py" 2>/dev/null | head -1)"
fi
[ -z "$MEASURE_PY" ] || [ ! -f "$MEASURE_PY" ] && { echo "[Error] measure.py not found. Is Token Optimizer installed?"; exit 1; }
```

2. **Collect coaching data**:
```bash
python3 $MEASURE_PY coach --json
```
Parse the JSON output. This gives you: snapshot (current measurements), detected patterns, coaching questions, and focus suggestions.

## Phase 1: Intake

Ask ONE question:

> What's your goal today?
> a) Building something new, want it token-efficient from the start
> b) Existing project feels sluggish / context fills too fast
> c) Designing a multi-agent system, want architecture advice
> d) Quick health check with actionable tips

Wait for the answer. Don't dump info before they choose.

## Phase 2: Load Context (based on intake)

Resolve the token-coach skill directory:
```bash
COACH_DIR=""
if [ -d "$HOME/.claude/skills/token-coach" ]; then
  COACH_DIR="$HOME/.claude/skills/token-coach"
elif [ -d "$HOME/.claude/skills/token-optimizer/../token-coach" ]; then
  COACH_DIR="$HOME/.claude/skills/token-optimizer/../token-coach"
else
  COACH_DIR="$(find "$HOME/.claude/plugins/cache" -path "*/token-coach" -type d 2>/dev/null | head -1)"
fi
```

Load references based on intake choice:
- **Option a or b**: Read `$COACH_DIR/references/coach-patterns.md` + `$COACH_DIR/references/quick-reference.md`
- **Option c**: Read `$COACH_DIR/references/agentic-systems.md` + `$COACH_DIR/references/quick-reference.md`
- **Option d**: Read `$COACH_DIR/references/quick-reference.md` only (fast path)

Read the matching example from `$COACH_DIR/examples/` as a few-shot template:
- Option a: `coaching-session-new-project.md`
- Option b: `coaching-session-heavy-setup.md`
- Option c: `coaching-session-agentic.md`
- Option d: Skip example (keep it fast)

Read `$COACH_DIR/references/coaching-scripts.md` for conversation structure.

## Phase 3: Coach (conversation, not report)

This is a CONVERSATION. Not a wall of text.

1. Lead with the 1-2 most impactful findings from the coaching data
2. Reference their actual numbers ("You have 47 skills costing ~4,700 tokens at startup")
3. Ask a follow-up question. Don't dump everything at once.
4. For agentic systems (option c): walk through their architecture step by step
5. Use the coaching scripts for structure, but keep it natural

**Tone**: Knowledgeable friend, not corporate consultant. Be direct about what matters and why. Use real numbers from their data.

**Anti-patterns to call out**: Reference the anti-patterns from coach-patterns.md. Name them ("You've got the 50-Skill Trap going on").

Continue the conversation for 2-4 exchanges. Let the user ask questions. Adjust advice based on what they tell you about their workflow.

## Phase 4: Action Plan

After the conversation, generate a prioritized action plan:

1. Summarize 3-5 concrete actions, ordered by impact
2. Include estimated token savings for each action (use the numbers from quick-reference.md)
3. Flag which actions are quick wins vs deeper changes
4. Offer to run `/token-optimizer` for the full audit + implementation if they want to go beyond coaching

**Format**: Keep it scannable. Numbered list with bold action names, one-line description, estimated savings.

## Phase 5: Dashboard (optional)

If measure.py generated a coach dashboard tab, mention it:
"Your Token Health Score and pattern analysis are in the dashboard. Run `python3 $MEASURE_PY dashboard` to see it."
