/**
 * OpenClaw session JSONL parser.
 *
 * Reads ~/.openclaw/agents/{agentId}/sessions/{sessionId}.jsonl
 * and normalizes into AgentRun objects.
 *
 * OpenClaw JSONL differences from Claude Code:
 * - Token fields: inputTokens, outputTokens, totalTokens (no cache breakdown)
 * - Agent-scoped: sessions live under agent directories
 * - No subagent nesting (agents are top-level)
 */
import { AgentRun } from "./models";
/**
 * Find the first existing OpenClaw data directory.
 */
export declare function findOpenClawDir(): string | null;
/**
 * Discover all agent directories under the OpenClaw data root.
 */
export declare function listAgents(openclawDir: string): string[];
/**
 * Find all session JSONL files for a given agent, optionally filtered by age.
 *
 * Returns array of { filePath, agentName, sessionId, mtime } sorted newest-first.
 */
export declare function findSessionFiles(openclawDir: string, agentName: string, days?: number): Array<{
    filePath: string;
    agentName: string;
    sessionId: string;
    mtime: number;
}>;
/**
 * Parse a single OpenClaw session JSONL file into an AgentRun.
 *
 * OpenClaw JSONL format:
 * - Each line is a JSON object with at minimum a "type" field
 * - Token data in assistant messages under "usage" or top-level fields
 * - Model ID in "model" field of assistant messages
 */
export declare function parseSession(filePath: string, agentName: string, openclawDir?: string): AgentRun | null;
/**
 * Scan all agents and sessions within the given day window.
 *
 * Returns all parsed AgentRuns sorted by timestamp (newest first).
 */
export declare function scanAllSessions(openclawDir: string, days?: number): AgentRun[];
/**
 * Classify runs as heartbeat/cron based on OpenClaw cron config.
 *
 * Reads ~/.openclaw/cron/ for heartbeat configurations and marks
 * matching agent runs accordingly.
 */
export declare function classifyCronRuns(openclawDir: string, runs: AgentRun[]): void;
//# sourceMappingURL=session-parser.d.ts.map