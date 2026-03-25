/**
 * Quality Scoring for OpenClaw.
 *
 * 5-signal quality metric adapted for OpenClaw's architecture.
 * Score: 0-100 with color bands (Good/Fair/Needs Work/Poor).
 */
import { AgentRun } from "./models";
import { ContextAudit } from "./context-audit";
export interface QualitySignal {
    name: string;
    weight: number;
    score: number;
    description: string;
}
export interface QualityReport {
    score: number;
    band: string;
    signals: QualitySignal[];
    recommendations: string[];
}
export declare function contextWindowForModel(model: string): number;
export declare function scoreQuality(runs: AgentRun[], contextAudit?: ContextAudit | null): QualityReport;
/**
 * Score a single AgentRun's quality on a 0-100 scale.
 *
 * Signals (weights):
 *   1. Context fill (25%): input tokens / model context window
 *   2. Message count risk (25%): >50 messages = degraded
 *   3. Cache hit rate (20%): higher = better (OpenClaw: typically 0)
 *   4. Output/input ratio (15%): low ratio = wasteful
 *   5. Duration risk (15%): >60min sessions = risk
 */
export declare function scoreSessionQuality(run: AgentRun): {
    score: number;
    band: string;
};
//# sourceMappingURL=quality.d.ts.map