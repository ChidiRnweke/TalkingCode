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
	kind: 'agent_error';
	turnId: string;
	message: string;
	code?: string | null;
	timestamp: string;
}

export interface ToolCallStartedEvent {
	kind: 'tool_call_started';
	turnId: string;
	toolName: string;
	callId?: string;
	iteration?: number;
	visibleArgs: Record<string, unknown>;
	timestamp: string;
}

export interface ToolCallFinishedEvent {
	kind: 'tool_call_finished';
	turnId: string;
	toolName: string;
	callId?: string;
	iteration?: number;
	success: boolean;
	durationMs: number;
	errorCode?: string;
	timestamp: string;
}

export interface IterationStartedEvent {
	kind: 'iteration_started';
	turnId: string;
	iteration: number;
	timestamp: string;
}

export interface PlanChunkEvent {
	kind: 'plan_chunk';
	turnId: string;
	iteration: number;
	chunk: string;
	timestamp: string;
}

export interface PlanDoneEvent {
	kind: 'plan_done';
	turnId: string;
	iteration: number;
	planText: string;
	timestamp: string;
}

export interface AnswerPhaseStartedEvent {
	kind: 'answer_phase_started';
	turnId: string;
	iteration?: number;
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
	| IterationStartedEvent
	| PlanChunkEvent
	| PlanDoneEvent
	| AnswerPhaseStartedEvent
	| ToolCallStartedEvent
	| ToolCallFinishedEvent
	| AssistantTokenEvent
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
	phase: 'answer_started';
	iteration?: number;
	timestamp: string;
}

export type ReasoningStep = PlanReasoningStep | ToolReasoningStep | PhaseReasoningStep;

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
	plan?: AgentPlanView | null;
	planText?: string;
	toolCalls?: ToolCallTimelineItem[];
	reasoningSteps?: ReasoningStep[];
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
