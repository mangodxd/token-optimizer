"use strict";
/**
 * Cost calculation for token usage.
 *
 * Ported from fleet.py calculate_cost(). Multiplies token counts
 * by per-token rates for the given model.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.calculateCost = calculateCost;
exports.calculateCostOnModel = calculateCostOnModel;
const pricing_1 = require("./pricing");
/**
 * Calculate USD cost for a token breakdown at the given model's rates.
 *
 * Falls back to sonnet pricing if model is unknown.
 * For OpenClaw where hasCacheBreakdown is false, cacheRead/cacheWrite
 * will be 0 and input contains total input tokens priced at the input rate.
 */
function calculateCost(tokens, model) {
    const rates = pricing_1.DEFAULT_PRICING[model] ?? pricing_1.DEFAULT_PRICING["sonnet"];
    let cost = 0;
    cost += tokens.input * rates.input;
    cost += tokens.output * rates.output;
    cost += tokens.cacheRead * rates.cacheRead;
    cost += tokens.cacheWrite * rates.cacheWrite;
    return cost;
}
/**
 * Calculate what the same token usage would cost on a different model.
 * Used for "switch to haiku" savings calculations.
 */
function calculateCostOnModel(tokens, targetModel) {
    return calculateCost(tokens, targetModel);
}
//# sourceMappingURL=cost-calculator.js.map