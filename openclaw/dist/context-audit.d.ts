/**
 * Context Optimization Audit for OpenClaw.
 *
 * Scans all system prompt components and reports per-component token overhead.
 * Includes individual skill breakdown, MCP server scanning, and manage data.
 */
export interface ContextComponent {
    name: string;
    path: string;
    tokens: number;
    category: "config" | "personality" | "memory" | "skills" | "tools" | "agents" | "system";
    isOptimizable: boolean;
}
export interface SkillDetail {
    name: string;
    path: string;
    tokens: number;
    fullFileTokens: number;
    description: string;
    isArchived: boolean;
}
export interface McpServer {
    name: string;
    command: string;
    toolCount: number;
    isDisabled: boolean;
}
export interface ManageData {
    skills: {
        active: SkillDetail[];
        archived: SkillDetail[];
    };
    mcpServers: {
        active: McpServer[];
        disabled: McpServer[];
    };
}
export interface ContextAudit {
    totalOverhead: number;
    components: ContextComponent[];
    skills: SkillDetail[];
    mcpServers: McpServer[];
    recommendations: string[];
    manage: ManageData;
}
export declare function auditContext(openclawDir: string): ContextAudit;
//# sourceMappingURL=context-audit.d.ts.map