# Token Optimizer for OpenClaw

Find the ghost tokens. Audit your OpenClaw setup, see where 15-20% of your context goes (up to 87% on smaller models), and fix it.

## How Much Context Are You Losing?

Before you type a single word, your context window is already partially consumed by overhead. Real-world breakdown from a power user setup:

| Component | Tokens | % of 1M window | % of 200K window |
|-----------|--------|----------------|------------------|
| 60 loaded skills | 142,405 | 14.2% | 71.2% |
| System prompt | ~15,000 | 1.5% | 7.5% |
| MCP tool definitions | ~9,000 | 0.9% | 4.5% |
| CLAUDE.md / SOUL.md | ~5,000 | 0.5% | 2.5% |
| MEMORY.md | ~3,000 | 0.3% | 1.5% |
| **Total overhead** | **~174K** | **17.4%** | **87%** |

On a 1M window (Opus/Sonnet since March 13, 2026), 174K overhead is manageable but still means earlier compaction and degraded output quality as context fills. On a 200K window (Haiku, GPT-4o), the same setup is nearly unusable.

Token Optimizer shows you exactly where those tokens go, per-skill and per-server, and lets you trim what you don't need.

For API users, overhead also translates to cost ($5-355/month depending on volume and model).

## Install

```sh
openclaw plugins install token-optimizer-openclaw
```

Or from source:

```sh
cd openclaw && npm install && npm run build
openclaw plugins install ./openclaw
```

## What It Does

- **Scans** all agent sessions for token usage and cost
- **Detects** 7 waste patterns with monthly $ savings and fix snippets
- **Dashboard** with 8-tab HTML visualization
- **Context audit** with per-skill and per-MCP-server token breakdown
- **Quality scoring** with 5 signals and model-aware context windows (Claude 1M, GPT-5 400K, Gemini 2M)
- **Manage tab** to toggle skills and MCP servers on/off (accumulated clipboard commands)
- **Smart Compaction v2** preserves decisions, errors, and user instructions during compaction
- **Drift detection** snapshots config and diffs to catch creep

## CLI

```sh
npx token-optimizer detect                # Is OpenClaw installed?
npx token-optimizer scan --days 30        # Scan sessions, show usage
npx token-optimizer audit --days 30       # Detect waste, show $ savings
npx token-optimizer audit --json          # JSON output for agents
npx token-optimizer dashboard             # Generate HTML dashboard, open in browser
npx token-optimizer context               # Show context overhead breakdown
npx token-optimizer context --json        # Context audit as JSON
npx token-optimizer quality               # Show quality score (0-100)
npx token-optimizer drift                 # Check for config drift
npx token-optimizer drift --snapshot      # Capture current config snapshot
```

## Dashboard

The interactive dashboard has 8 tabs:

| Tab | What It Shows |
|-----|--------------|
| Overview | Stat cards (runs, cost, quality score, savings), agent cards, context overhead bar |
| Context | Per-component token breakdown, individual skill bars, MCP server list, recommendations |
| Quality | 5-signal quality score (0-100) with per-signal breakdown and recommendations |
| Waste | Waste cards with severity, confidence, fix snippets with Copy Fix button |
| Agents | Per-agent cost, model mix stacked bars (multi-model only), top agents table |
| Sessions | Individual session history grouped by date with outcome, cost, and model |
| Daily | Daily cost/token and run count charts with Y-axis labels and custom tooltips |
| Manage | Toggle skills and MCP servers on/off. Changes accumulate, copy all at once |

Dashboard auto-regenerates on session end. Open manually with `npx token-optimizer dashboard`.

## Waste Patterns Detected

| Pattern | What It Means | Typical Savings |
|---------|--------------|-----------------|
| Heartbeat Model Waste | Cron agent using opus/sonnet instead of haiku | $2-50/month |
| Heartbeat Over-Frequency | Checking more often than every 5 minutes | $1-10/month |
| Empty Heartbeat Runs | Loading 50K+ tokens, finding nothing to do | $2-30/month |
| Stale Cron Config | Hooks pointing to non-existent paths | Varies |
| Session History Bloat | 500K+ tokens without compaction | 40% of bloated input |
| Loop Detection | 20+ messages with near-zero output | $1-20/month |
| Abandoned Sessions | Started, loaded context, then left | $0.20-5/month |

## Quality Signals

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| Context Fill | 25% | Token usage relative to model context window (per-model: Claude 1M, GPT-5 400K, Gemini 2M) |
| Session Length Risk | 20% | Message count vs compaction threshold |
| Model Routing | 20% | Expensive models used for cheap tasks |
| Empty Run Ratio | 20% | Runs that load context but produce nothing |
| Outcome Health | 15% | Success vs abandoned/empty/failure ratio |

## Context Audit

Scans every component OpenClaw injects into context:

| Component | Source | Optimizable |
|-----------|--------|-------------|
| Core system prompt | Built-in | No |
| SOUL.md | Personality/instructions | Yes |
| MEMORY.md | Persistent memory | Yes |
| AGENTS.md | Agent definitions | Yes |
| TOOLS.md | MCP tool definitions | Yes |
| Skills | Individual SKILL.md files | Yes (archive unused) |
| Agent configs | Per-agent config.json | Yes |
| Cron configs | cron/*.json | Yes |
| MCP Servers | config.json mcpServers | Yes (disable unused) |

## Smart Compaction v2

Hooks into `session:compact:before` and `session:compact:after`. Instead of saving the last 20 raw messages (v1), v2 extracts:

- **User instructions**: "always", "never", "make sure" directives
- **Decisions**: "decided to", "going with", "switching to"
- **Errors**: stack traces, error messages, failure patterns
- **File changes**: write, edit, create operations

Result: more relevant context in fewer tokens after compaction.

## Drift Detection

```sh
npx token-optimizer drift --snapshot      # Save current state
# ... time passes, skills added, configs changed ...
npx token-optimizer drift                 # See what changed
```

Tracks: skill count, agent count, SOUL.md/MEMORY.md size changes, model config changes, cron configs.

## Pricing

Covers 30+ models with verified March 2026 rates: Claude (Opus/Sonnet/Haiku), GPT-5 family, GPT-4.1 family, o3/o4, Gemini 2.0-3.1, DeepSeek, Qwen, Mistral, Grok, and more. User-configured pricing overrides via openclaw.json.

## License

AGPL-3.0-only
