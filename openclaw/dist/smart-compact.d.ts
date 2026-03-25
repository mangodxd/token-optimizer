/**
 * Smart Compaction v2: intelligent extraction + last N messages fallback.
 *
 * v1: capture last N messages as markdown.
 * v2: extract decisions, errors, file modifications, and user instructions
 *     to preserve the most relevant context in fewer tokens.
 */
export declare function captureCheckpoint(session: {
    sessionId: string;
    messages?: Array<{
        role: string;
        content: string;
        timestamp?: string;
    }>;
}, maxMessages?: number): string | null;
export declare function restoreCheckpoint(sessionId: string): string | null;
/**
 * v2 checkpoint: intelligent extraction + recent messages fallback.
 * Produces a more focused checkpoint than v1's raw last-N dump.
 */
export declare function captureCheckpointV2(session: {
    sessionId: string;
    messages?: Array<{
        role: string;
        content: string;
        timestamp?: string;
    }>;
}, maxRecentMessages?: number): string | null;
export declare function cleanupCheckpoints(maxAgeDays?: number): number;
//# sourceMappingURL=smart-compact.d.ts.map