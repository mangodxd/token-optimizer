/**
 * Cost calculation for token usage.
 *
 * Ported from fleet.py calculate_cost(). Multiplies token counts
 * by per-token rates for the given model.
 */
import { TokenBreakdown } from "./models";
/**
 * Calculate USD cost for a token breakdown at the given model's rates.
 *
 * Falls back to sonnet pricing if model is unknown.
 * For OpenClaw where hasCacheBreakdown is false, cacheRead/cacheWrite
 * will be 0 and input contains total input tokens priced at the input rate.
 */
export declare function calculateCost(tokens: TokenBreakdown, model: string): number;
/**
 * Calculate what the same token usage would cost on a different model.
 * Used for "switch to haiku" savings calculations.
 */
export declare function calculateCostOnModel(tokens: TokenBreakdown, targetModel: string): number;
//# sourceMappingURL=cost-calculator.d.ts.map