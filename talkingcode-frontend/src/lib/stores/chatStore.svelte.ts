/** Chat store with multi-turn conversation support */
import type { AgentStreamEvent, ToolCallTimelineItem, AgentPlanView, ChatMessage } from '$lib/models';

type TurnPhase = 'idle' | 'planning' | 'tools' | 'streaming' | 'done' | 'error';

function createChatStore() {
	let messages = $state<ChatMessage[]>([]);
	let activeMessageId = $state<string | null>(null);
	let detailPanelMessageId = $state<string | null>(null);
	let selectedModel = $state<string | null>(null);
	let currentTurnStartTime = $state<number | null>(null);

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
		get selectedModel() {
			return selectedModel;
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
				if (active.plan || active.planText || active.toolCalls?.length) return 'tools';
				return 'planning';
			}
			if (active.plan || active.planText || active.toolCalls?.length) return 'done';
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
			currentTurnStartTime = Date.now();
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
				case 'iteration_started':
					messages[idx] = {
						...current,
						planText: current.planText ?? ''
					};
					break;

				case 'plan_chunk':
					messages[idx] = {
						...current,
						planText: (current.planText ?? '') + event.chunk
					};
					break;

				case 'plan_done':
					messages[idx] = {
						...current,
						planText: event.planText
					};
					break;

				case 'tool_call_started': {
					const newToolCall: ToolCallTimelineItem = {
						turnId: event.turnId,
						toolName: event.toolName,
						callId: event.callId,
						iteration: event.iteration,
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
						(event.callId ? t.callId === event.callId : true) &&
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

				case 'assistant_token': {
					const update: Partial<ChatMessage> = {
						content: current.content + event.token,
						isStreaming: true
					};

					if (!current.content && currentTurnStartTime) {
						update.thoughtDurationS = Math.max(1, Math.round((Date.now() - currentTurnStartTime) / 1000));
						currentTurnStartTime = null;
					}

					messages[idx] = { ...current, ...update };
					break;
				}

				case 'assistant_done': {
					const update: Partial<ChatMessage> = { isStreaming: false };

					if (!current.thoughtDurationS && currentTurnStartTime) {
						update.thoughtDurationS = Math.max(1, Math.round((Date.now() - currentTurnStartTime) / 1000));
						currentTurnStartTime = null;
					}

					messages[idx] = { ...current, ...update };
					break;
				}

				case 'agent_error':
					messages[idx] = {
						...current,
						isStreaming: false,
						error: event.message
					};
					currentTurnStartTime = null;
					break;
			}
		},

		openDetailPanel(messageId: string) {
			detailPanelMessageId = messageId;
		},

		closeDetailPanel() {
			detailPanelMessageId = null;
		},

		setSelectedModel(model: string) {
			selectedModel = model;
		},

		retry(messageId: string): string | null {
			const idx = messages.findIndex((m) => m.id === messageId);
			if (idx < 0) return null;

			// Find preceding user message
			let userMsgContent = null;
			for (let i = idx - 1; i >= 0; i--) {
				if (messages[i].role === 'user') {
					userMsgContent = messages[i].content;
					break;
				}
			}

			if (userMsgContent !== null) {
				// Remove the assistant message being retried and anything after it
				messages = messages.slice(0, idx);
			}

			return userMsgContent;
		},

		clear() {
			messages = [];
			activeMessageId = null;
			detailPanelMessageId = null;
		}
	};
}

export const chatStore = createChatStore();
