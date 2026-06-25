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
	callId?: string;
	iteration?: number;
	visibleArgs: Record<string, unknown>;
	status: ToolCallStatus;
	durationMs?: number;
	timestamp: string;
	errorCode?: string;
	errorMessage?: string;
}

export interface AgentErrorEvent {
	kind: 'turn.error';
	turnId: string;
	message: string;
	code?: string | null;
	timestamp: string;
}

export interface TurnStartedEvent {
	kind: 'turn.started';
	turnId: string;
	model?: string;
	timestamp: string;
}

export interface ToolCallStartedEvent {
	kind: 'tool_call.started';
	turnId: string;
	toolName: string;
	callId?: string;
	iteration?: number;
	index?: number;
	visibleArgs: Record<string, unknown>;
	timestamp: string;
}

export interface ToolCallDeltaEvent {
	kind: 'tool_call.delta';
	turnId: string;
	toolName?: string;
	callId?: string;
	iteration?: number;
	index?: number;
	phase?: string;
	timestamp: string;
}

export interface ToolCallFinishedEvent {
	kind: 'tool_call.completed';
	turnId: string;
	toolName: string;
	callId?: string;
	iteration?: number;
	index?: number;
	success: boolean;
	durationMs: number;
	errorCode?: string;
	timestamp: string;
}

export interface ToolResultAvailableEvent {
	kind: 'tool_result.available';
	turnId: string;
	toolName: string;
	callId?: string;
	iteration?: number;
	index?: number;
	success: boolean;
	errorCode?: string;
	timestamp: string;
}

export interface AssistantTokenEvent {
	kind: 'message.delta';
	turnId: string;
	token: string;
	iteration?: number;
	timestamp: string;
}

export interface ReasoningDeltaEvent {
	kind: 'reasoning.delta';
	turnId: string;
	text: string;
	iteration?: number;
	timestamp: string;
}

export interface StepSummaryEvent {
	kind: 'step.summary';
	turnId: string;
	summary: string;
	iteration?: number;
	timestamp: string;
}

export interface AssistantDoneEvent {
	kind: 'turn.done';
	turnId: string;
	sources?: Array<{
		index: number;
		repository: string;
		path: string;
		startLine: number | null;
		endLine: number | null;
		similarityScore: number;
	}>;
	timestamp: string;
}

export type AgentStreamEvent =
	| TurnStartedEvent
	| ToolCallStartedEvent
	| ToolCallDeltaEvent
	| ToolCallFinishedEvent
	| ToolResultAvailableEvent
	| AssistantTokenEvent
	| ReasoningDeltaEvent
	| StepSummaryEvent
	| AssistantDoneEvent
	| AgentErrorEvent;

export interface PlanReasoningStep {
	id: string;
	kind: 'plan';
	iteration: number;
	text: string;
	timestamp: string;
}

export interface ToolReasoningStep {
	id: string;
	kind: 'tool';
	tool: ToolCallTimelineItem;
	timestamp: string;
}

export interface PhaseReasoningStep {
	id: string;
	kind: 'phase';
	phase: 'tool_streamed' | 'tool_result';
	iteration?: number;
	timestamp: string;
}

export type ReasoningStep = PlanReasoningStep | ToolReasoningStep | PhaseReasoningStep;

export interface AssistantTextPart {
	id: string;
	kind: 'text';
	text: string;
	iteration?: number;
	timestamp: string;
}

export interface AssistantToolPart {
	id: string;
	kind: 'tool';
	tool: ToolCallTimelineItem;
	iteration?: number;
	timestamp: string;
}

export interface AssistantReasoningPart {
	id: string;
	kind: 'reasoning';
	text: string;
	iteration?: number;
	timestamp: string;
}

export type AssistantPart = AssistantTextPart | AssistantToolPart | AssistantReasoningPart;

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
	plan?: AgentPlanView | null;
	planText?: string;
	toolCalls?: ToolCallTimelineItem[];
	reasoningSteps?: ReasoningStep[];
	parts?: AssistantPart[];
	stepSummaries?: Record<number, string>;
	isStreaming?: boolean;
	thoughtDurationS?: number;
	sources?: AssistantDoneEvent['sources'];
	error?: string | null;
}

// =============================================================================
// Repository Management
// =============================================================================

export interface RepositoryView {
	id: string;
	provider: string;
	owner: string;
	name: string;
	defaultBranch: string;
	lastIngestedAt: string | null;
	createdAt: string;
}

export interface IngestionRunView {
	id: string;
	repositoryId: string;
	status: 'running' | 'done' | 'failed';
	startedAt: string;
	completedAt: string | null;
	errorMessage: string | null;
}

export interface RegisterRepoInput {
	owner: string;
	name: string;
	defaultBranch?: string;
}
