/** Domain models for agentic chat */

export type Area = 'backend' | 'frontend' | 'infra' | 'scripts' | 'docs' | 'tests';

export type FileType = 'source' | 'config' | 'migration' | 'test' | 'docs' | 'ci' | 'unknown';

export type ToolCallStatus = 'started' | 'finished' | 'failed';

export interface AgenticAskInput {
	conversationId: string | null;
	question: string;
	model: string | null;
}

export interface RetrievalFilterView {
	areas: Area[];
	languages: string[];
	fileTypes: FileType[];
	pathGlobs: string[];
	repoScopes: string[];
	symbolHints: string[];
	tags: string[];
}

export interface ToolGroupView {
	name: string;
	calls: Array<{
		toolName: string;
		arguments: Record<string, unknown>;
		nonBlocking?: boolean;
	}>;
	parallel: boolean;
}

export interface AgentPlanView {
	intent: string;
	filters: RetrievalFilterView;
	toolGroups: ToolGroupView[];
}

export interface ToolCallTimelineItem {
	turnId: string;
	toolName: string;
	visibleArgs: Record<string, unknown>;
	status: ToolCallStatus;
	durationMs?: number;
	timestamp: string;
	errorCode?: string;
	errorMessage?: string;
}

export interface AgentErrorEvent {
	kind: 'agent_error';
	turnId: string;
	message: string;
	code?: string | null;
	timestamp: string;
}

export interface PlannerStartedEvent {
	kind: 'planner_started';
	turnId: string;
	timestamp: string;
}

export interface PlannerReadyEvent {
	kind: 'planner_ready';
	turnId: string;
	intent: string;
	filters: RetrievalFilterView;
	timestamp: string;
}

export interface ToolCallStartedEvent {
	kind: 'tool_call_started';
	turnId: string;
	toolName: string;
	visibleArgs: Record<string, unknown>;
	timestamp: string;
}

export interface ToolCallFinishedEvent {
	kind: 'tool_call_finished';
	turnId: string;
	toolName: string;
	success: boolean;
	durationMs: number;
	timestamp: string;
}

export interface AssistantTokenEvent {
	kind: 'assistant_token';
	turnId: string;
	token: string;
	timestamp: string;
}

export interface AssistantDoneEvent {
	kind: 'assistant_done';
	turnId: string;
	timestamp: string;
}

export type AgentStreamEvent =
	| PlannerStartedEvent
	| PlannerReadyEvent
	| ToolCallStartedEvent
	| ToolCallFinishedEvent
	| AssistantTokenEvent
	| AssistantDoneEvent
	| AgentErrorEvent;
