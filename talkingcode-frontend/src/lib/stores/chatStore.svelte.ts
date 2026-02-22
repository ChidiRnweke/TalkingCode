/** Chat store with multi-turn conversation support */
import type { AgentStreamEvent, ToolCallTimelineItem, AgentPlanView, ChatMessage } from '$lib/models';

type TurnPhase = 'idle' | 'planning' | 'tools' | 'streaming' | 'done' | 'error';

function createChatStore() {
	let messages = $state<ChatMessage[]>([]);
	let activeMessageId = $state<string | null>(null);
	let detailPanelMessageId = $state<string | null>(null);

	function generateId(): string {
		return crypto.randomUUID();
	}

	return {
		get messages() {
			return messages;
		},
		get activeMessageId() {
			return activeMessageId;
		},
		get detailPanelMessageId() {
			return detailPanelMessageId;
		},
		get activeMessage(): ChatMessage | null {
			if (!activeMessageId) return null;
			return messages.find((m) => m.id === activeMessageId) ?? null;
		},
		get detailMessage(): ChatMessage | null {
			if (!detailPanelMessageId) return null;
			return messages.find((m) => m.id === detailPanelMessageId) ?? null;
		},
		get isStreaming(): boolean {
			return messages.some((m) => m.role === 'assistant' && m.isStreaming);
		},
		get isEmpty(): boolean {
			return messages.length === 0;
		},
		get phase(): TurnPhase {
			const active = this.activeMessage;
			if (!active || active.role === 'user') return 'idle';
			if (active.error) return 'error';
			if (active.isStreaming) {
				if (active.content) return 'streaming';
				if (active.plan || active.toolCalls?.length) return 'tools';
				return 'planning';
			}
			if (active.plan || active.toolCalls?.length) return 'done';
			return 'idle';
		},

		addUserMessage(content: string): string {
			const id = generateId();
			const userMessage: ChatMessage = {
				id,
				role: 'user',
				content,
				timestamp: new Date().toISOString()
			};
			messages = [...messages, userMessage];
			return id;
		},

		startAssistantTurn(): string {
			const id = generateId();
			const assistantMessage: ChatMessage = {
				id,
				role: 'assistant',
				content: '',
				timestamp: new Date().toISOString(),
				plan: null,
				toolCalls: [],
				isStreaming: true,
				error: null
			};
			messages = [...messages, assistantMessage];
			activeMessageId = id;
			return id;
		},

		handleEvent(event: AgentStreamEvent) {
			if (!activeMessageId) return;

			const idx = messages.findIndex((m) => m.id === activeMessageId);
			if (idx < 0) return;

			const current = messages[idx];

			switch (event.kind) {
				case 'planner_started':
					messages[idx] = {
						...current,
						plan: { intent: '', filters: { areas: [], languages: [], fileTypes: [], pathGlobs: [], repoScopes: [], symbolHints: [], tags: [] }, toolGroups: [] }
					};
					break;

				case 'planner_ready':
					messages[idx] = {
						...current,
						plan: {
							intent: event.intent,
							filters: event.filters,
							toolGroups: []
						}
					};
					break;

				case 'tool_call_started': {
					const newToolCall: ToolCallTimelineItem = {
						turnId: event.turnId,
						toolName: event.toolName,
						visibleArgs: event.visibleArgs,
						status: 'started',
						timestamp: event.timestamp
					};
					messages[idx] = {
						...current,
						toolCalls: [...(current.toolCalls ?? []), newToolCall]
					};
					break;
				}

				case 'tool_call_finished': {
					const toolCalls = current.toolCalls?.map((t) =>
						t.turnId === event.turnId &&
						t.toolName === event.toolName &&
						t.status === 'started'
							? {
									...t,
									status: event.success ? 'finished' as const : 'failed' as const,
									durationMs: event.durationMs
								}
							: t
					);
					messages[idx] = { ...current, toolCalls };
					break;
				}

				case 'assistant_token':
					messages[idx] = {
						...current,
						content: current.content + event.token,
						isStreaming: true
					};
					break;

				case 'assistant_done':
					messages[idx] = {
						...current,
						isStreaming: false
					};
					break;

				case 'agent_error':
					messages[idx] = {
						...current,
						isStreaming: false,
						error: event.message
					};
					break;
			}
		},

		openDetailPanel(messageId: string) {
			detailPanelMessageId = messageId;
		},

		closeDetailPanel() {
			detailPanelMessageId = null;
		},

		reset() {
			messages = [];
			activeMessageId = null;
			detailPanelMessageId = null;
		}
	};
}

export const chatStore = createChatStore();
