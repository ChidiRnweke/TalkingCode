/** Domain models for agentic chat */

export type Area = 'backend' | 'frontend' | 'infra' | 'scripts' | 'docs' | 'tests';

export type FileType = 'source' | 'config' | 'migration' | 'test' | 'docs' | 'ci' | 'unknown';

export interface AgenticAskInput {
	conversationId: string | null;
	question: string;
	model: string | null;
	/** 1-based ordinal of the retried user message; rewinds backend session memory. */
	retryUserOrdinal?: number | null;
}

export interface AgentErrorEvent {
	kind: 'turn.error';
	turnId: string;
	message: string;
	code?: string | null;
	timestamp: string;
}

export interface MarkdownDeltaEvent {
	kind: 'markdown.delta';
	text: string;
	timestamp: string;
}

export interface AssistantDoneEvent {
	kind: 'turn.done';
	turnId: string;
	conversationId: string;
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
	| MarkdownDeltaEvent
	| AssistantDoneEvent
	| AgentErrorEvent;

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
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
