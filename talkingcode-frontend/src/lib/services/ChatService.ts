/** Chat service implementation with SSE parsing */
import { env } from '$env/dynamic/public';
import type {
	AgenticAskInput,
	AgentStreamEvent,
	ToolCallTimelineItem,
	Area,
	FileType
} from '$lib/models';
import type { IChatService } from './IChatService';

export class ChatService implements IChatService {
	private backendUrl: string;

	constructor() {
		this.backendUrl = env.PUBLIC_BACKEND_URL || 'http://localhost:8000';
	}

	async *askAgentic(input: AgenticAskInput): AsyncGenerator<AgentStreamEvent> {
		const response = await fetch(`${this.backendUrl}/chat/agentic`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				conversation_id: input.conversationId,
				question: input.question,
				selected_model: input.model
			})
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const reader = response.body?.getReader();
		if (!reader) {
			throw new Error('No response body');
		}

		const decoder = new TextDecoder();
		let buffer = '';

		try {
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					const event = this.parseSSELine(line);
					if (event) {
						yield event;
					}
				}
			}
		} finally {
			reader.releaseLock();
		}
	}

	private parseSSELine(line: string): AgentStreamEvent | null {
		if (!line.trim()) return null;

		// Parse event: and data: lines
		if (line.startsWith('event:')) {
			this.currentEventType = line.slice(6).trim();
			return null;
		}

		if (line.startsWith('data:')) {
			const data = line.slice(5).trim();
			return this.parseEventData(this.currentEventType, data);
		}

		return null;
	}

	private currentEventType: string = '';

	private parseEventData(eventType: string, data: string): AgentStreamEvent | null {
		try {
			const parsed = JSON.parse(data);
			const timestamp = parsed.timestamp || new Date().toISOString();
			const turnId = parsed.turn_id || '';

			switch (eventType) {
				case 'iteration_started':
					return {
						kind: 'iteration_started',
						turnId,
						iteration: parsed.iteration || 1,
						timestamp
					};

				case 'plan_chunk':
					return {
						kind: 'plan_chunk',
						turnId,
						iteration: parsed.iteration || 1,
						chunk: parsed.visible_args?.chunk || parsed.message || '',
						timestamp
					};

				case 'plan_done':
					return {
						kind: 'plan_done',
						turnId,
						iteration: parsed.iteration || 1,
						planText: parsed.visible_args?.plan_text || parsed.message || '',
						timestamp
					};

				case 'planner_started':
					return { kind: 'planner_started', turnId, timestamp };

				case 'planner_ready':
					return {
						kind: 'planner_ready',
						turnId,
						intent: parsed.visible_args?.intent || '',
						filters: {
							areas: (parsed.visible_args?.filters?.areas || []) as Area[],
							languages: parsed.visible_args?.filters?.languages || [],
							fileTypes: (parsed.visible_args?.filters?.file_types || []) as FileType[],
							pathGlobs: parsed.visible_args?.filters?.path_globs || [],
							repoScopes: parsed.visible_args?.filters?.repo_scopes || [],
							symbolHints: parsed.visible_args?.filters?.symbol_hints || [],
							tags: parsed.visible_args?.filters?.tags || []
						},
						timestamp
					};

				case 'tool_call_started':
					return {
						kind: 'tool_call_started',
						turnId,
						toolName: parsed.tool_name || '',
						callId: parsed.call_id || undefined,
						iteration: parsed.iteration || undefined,
						visibleArgs: parsed.visible_args || {},
						timestamp
					};

				case 'tool_call_finished':
					return {
						kind: 'tool_call_finished',
						turnId,
						toolName: parsed.tool_name || '',
						callId: parsed.call_id || undefined,
						iteration: parsed.iteration || undefined,
						success: parsed.visible_args?.success || false,
						durationMs: parsed.visible_args?.duration_ms || 0,
						errorCode: parsed.visible_args?.error_code || parsed.code || undefined,
						timestamp
					};

				case 'assistant_token':
					return {
						kind: 'assistant_token',
						turnId,
						token: parsed.message || '',
						timestamp
					};

				case 'assistant_done':
					return { kind: 'assistant_done', turnId, timestamp };

				case 'agent_error':
					return {
						kind: 'agent_error',
						turnId,
						message: parsed.message || 'Unknown error',
						code: parsed.visible_args?.code || null,
						timestamp
					};

				default:
					// Reject unknown events
					console.warn(`Unknown event type: ${eventType}`);
					return null;
			}
		} catch (e) {
			console.error('Failed to parse SSE data:', e);
			return null;
		}
	}

	async getToolTimeline(conversationId: string): Promise<ToolCallTimelineItem[]> {
		const response = await fetch(
			`${this.backendUrl}/chat/timeline?conversation_id=${conversationId}`
		);

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();
		return data.timeline || [];
	}
}

export const chatService = new ChatService();
