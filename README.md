<p align="center">
  <img src="skills/token-optimizer/assets/logo.svg" alt="Token Optimizer" width="780">
</p>

<p align="center">
  <a href="https://github.com/alexgreensh/token-optimizer/releases"><img src="https://img.shields.io/badge/version-2.6.0-green" alt="Version 2.6.0"></a>
  <a href="https://github.com/alexgreensh/token-optimizer"><img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet" alt="Claude Code Plugin"></a>
  <a href="https://github.com/alexgreensh/token-optimizer/tree/main/openclaw"><img src="https://img.shields.io/badge/OpenClaw-Plugin-brightgreen" alt="OpenClaw Plugin"></a>
  <a href="https://github.com/alexgreensh/token-optimizer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/alexgreensh/token-optimizer" alt="License"></a>
  <a href="https://github.com/alexgreensh/token-optimizer/stargazers"><img src="https://img.shields.io/github/stars/alexgreensh/token-optimizer" alt="GitHub Stars"></a>
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey" alt="Platform">
</p>

<h2 align="center">Your AI is getting dumber and you can't see it.</h2>

<p align="center"><em>Find the ghost tokens. Survive compaction. Track the quality decay.</em></p>

<p align="center">
Opus 4.6 drops from 93% to 76% accuracy across a 1M context window. Compaction loses 60-70% of your conversation. Ghost tokens burn through your plan limits on every single message. Token Optimizer tracks the degradation, cuts the waste, checkpoints your decisions before compaction fires, and tells you what to fix.
</p>

<p align="center">
  <img src="skills/token-optimizer/assets/hero-terminal.svg" alt="Token Optimizer Quick Scan" width="800">
</p>

## Install (one line)

```bash
/plugin marketplace add alexgreensh/token-optimizer
```

Then: `/token-optimizer`

---

## The Problem

Every message re-sends everything: system prompt, tool definitions, MCP servers, skills, CLAUDE.md, MEMORY.md. The API is stateless. A typical power user burns 50-70K tokens before typing a word.

- **Quality degrades as context fills.** MRCR drops from 93% to 76% across 256K to 1M. Your AI gets measurably dumber with every message.
- **You hit rate limits faster.** Ghost tokens count toward your plan's usage caps on every message, cached or not. 50K overhead x 100 messages = 5M tokens burned on nothing.
- **Compaction is catastrophic.** 60-70% of your conversation gone per compaction. After 2-3 compactions: 88-95% cumulative loss.

Prompt caching makes this [cheaper](https://code.claude.com/docs/en/costs). But cheaper doesn't mean small. Those tokens still fill your context window, still count toward your plan's rate limits, and still degrade output quality.

![What happens inside a 1M session](skills/token-optimizer/assets/user-profiles.svg)

## What Token Optimizer Does

One command. Six parallel agents audit your entire setup. Prioritized fixes with exact token savings. Everything backed up before any change.

![How Token Optimizer works](skills/token-optimizer/assets/how-it-works.svg)

You see diffs. You approve each fix. Nothing irreversible.

| Area | What It Catches |
|------|----------------|
| **CLAUDE.md** | Content that should be skills or reference files. Duplication with MEMORY.md. Poor cache structure. |
| **MEMORY.md** | Overlap with CLAUDE.md. Verbose entries. Content past the 200-line auto-load cap. |
| **Skills** | Unused skills loading frontmatter (~100 tokens each). Duplicates. Wrong directory. |
| **MCP Servers** | Broken/unused servers. Duplicate tools. Missing Tool Search. |
| **Commands** | Rarely-used commands (~50 tokens each). |
| **Rules** | `.claude/rules/` overhead. Missing `permissions.deny`. No hooks. |

---

## Per-Turn Analytics and Cost Intelligence (v2.6)

| Feature | What You Get |
|---------|-------------|
| **Per-turn token breakdown** | Click any session to see input/output/cache per API call. Spike detection highlights context jumps. |
| **Cost per session** | Estimated API cost on every session row. Daily totals in trends. |
| **Four-tier pricing** | Anthropic API, Vertex Global, Vertex Regional (+10%), AWS Bedrock. Set once, all costs update. |
| **Cache visualization** | Stacked bars showing input vs output vs cache-read vs cache-write. See how well prompt caching works. |
| **Session quality overlay** | Color-coded quality scores on every session. Green = healthy, yellow = degrading, red = trouble. |
| **Kill stale sessions** | Terminates zombie headless sessions. Dashboard shows kill buttons with explanation. |
| **Live agent tracking** | Statusline shows running subagents with model, description, and elapsed time. |
| **Session duration warning** | Appears in statusline only when quality drops below 75. Contextual, not noise. |

---

## Commands

Standalone Python script. No dependencies. Python 3.8+. Zero context tokens consumed.

| Command | What You Get |
|---------|-------------|
| `quick` | **"Am I in trouble?"** 10-second context health, degradation risk, top offenders. |
| `doctor` | **"Is everything installed?"** Score out of 10. Broken hooks, missing components, fix commands. |
| `drift` | **"Has my setup grown?"** Comparison vs last snapshot. Catches config creep. |
| `quality` | **"How healthy is this session?"** 7-signal analysis: stale reads, wasted tokens, compaction damage. |
| `report` | **"Where are my tokens going?"** Full per-component breakdown. |
| `conversation` | **"What happened each turn?"** Per-message token + cost breakdown with spike detection. |
| `pricing-tier` | **"What am I paying?"** View or switch between Anthropic/Vertex/Bedrock pricing. |
| `kill-stale` | **"Clean up zombies."** Terminate headless sessions running 12+ hours. |
| `trends` | **"What's actually being used?"** Skill adoption, model mix, overhead trajectory. |
| `coach` | **"Where do I start?"** Detects 8 named anti-patterns, recommends specific fixes. |
| `dashboard` | Interactive HTML with all analytics. Auto-regenerates after every session. |
| `/token-optimizer` | **"Fix it for me."** Interactive audit with 6 parallel agents. Guided fixes with diffs. |

```bash
python3 measure.py quick                        # Start here
python3 measure.py conversation                 # Per-turn breakdown
python3 measure.py pricing-tier vertex-regional  # Switch pricing
python3 measure.py kill-stale --dry-run          # Preview zombie cleanup
python3 measure.py dashboard                    # Open the dashboard
```

---

## Quality Scoring: 7 Signals

| Signal | Weight | What It Means |
|--------|--------|---------------|
| **Context fill** | 20% | How close to the degradation cliff? Based on MRCR benchmarks. |
| **Stale reads** | 20% | Files you read have changed. AI is working with outdated info. |
| **Bloated results** | 20% | Tool outputs that were never used. Context wasted on noise. |
| **Compaction depth** | 15% | Each compaction loses 60-70%. After 2: 88% gone. |
| **Duplicates** | 10% | Same system reminders injected repeatedly. Pure waste. |
| **Decision density** | 8% | Real conversation or mostly overhead? |
| **Agent efficiency** | 7% | Are subagents pulling their weight or burning tokens? |

The quality score appears in your status bar. Colors shift from green to red as quality degrades.

![Status Bar Degradation](skills/token-optimizer/assets/status-bar.svg)

This is a real session. 708 messages, 2 compactions, 88% of the original context gone. Without the quality score, you'd have no idea.

![Real session quality breakdown](skills/token-optimizer/assets/quality-example.svg)

---

## Smart Compaction: Don't Lose Your Work

When auto-compact fires, 60-70% of your conversation vanishes. Decisions, error-fix sequences, agent state: gone.

Smart Compaction saves all of it as checkpoints before compaction, then restores what the summary dropped.

```bash
python3 measure.py setup-smart-compact    # checkpoint + restore hooks
python3 measure.py setup-quality-bar      # live quality score in status bar
```

Session continuity: sessions auto-checkpoint on end, /clear, and crashes. Start a new session on the same topic and relevant context is injected automatically.

---

## Interactive Dashboard

After the audit, you get an interactive HTML dashboard. Every component is clickable. Expand any item to see why it matters, the trade-offs, and what to change.

![Token Optimizer Dashboard](skills/token-optimizer/assets/dashboard-overview.png)

The dashboard auto-regenerates after every session via the SessionEnd hook.

```bash
python3 measure.py setup-daemon     # Bookmarkable URL at http://localhost:24842/
```

---

## How It Compares

| Capability | Token Optimizer | `/context` (built-in) | context-mode |
|---|---|---|---|
| Startup overhead audit | Deep (per-component) | Summary (v2.1.74+) | No |
| Quality degradation tracking | MRCR-based bands | Basic capacity % | No |
| Guided remediation | Yes, with token estimates | Basic suggestions | No |
| Runtime output containment | No | No | Yes (98% reduction) |
| Smart compaction survival | Checkpoint + restore | No | Session guide |
| Model recommendation | Yes (Sonnet vs Opus by context) | No | No |
| Usage trends + dashboard | SQLite + interactive HTML | No | Session stats |
| Per-turn cost analytics | Yes (4 pricing tiers) | No | No |
| Multi-platform | Claude Code + OpenClaw | Claude Code | 6 platforms |
| Context tokens consumed | 0 (external Python) | ~200 tokens | MCP overhead |

`/context` shows capacity. Token Optimizer fixes the causes.

---

## OpenClaw Plugin

Native TypeScript plugin for OpenClaw agent systems. Works with any model (Claude, GPT-5, Gemini, DeepSeek, local via Ollama). Reads your OpenClaw pricing config for accurate cost tracking, falls back to built-in rates for 20+ models.

```bash
openclaw plugins install token-optimizer-openclaw
```

Session parsing, cost calculation, waste detection (heartbeat model waste, empty runs, over-frequency, stale configs, session bloat, loops, abandoned sessions), and Smart Compaction. See [`openclaw/README.md`](openclaw/README.md) for full docs.

---

## License

AGPL-3.0. See [LICENSE](LICENSE).

Created by [Alex Greenshpun](https://linkedin.com/in/alexgreensh).
