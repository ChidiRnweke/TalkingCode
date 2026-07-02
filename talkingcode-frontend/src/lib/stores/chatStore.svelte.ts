/** Chat store with multi-turn conversation support */
import type { AgentStreamEvent, ChatMessage } from '$lib/models';

type TurnPhase = 'idle' | 'planning' | 'streaming' | 'done' | 'error';

function createChatStore() {
	let messages = $state<ChatMessage[]>([]);
	let activeMessageId = $state<string | null>(null);
	let selectedModel = $state<string | null>(null);
	let currentTurnStartTime = $state<number | null>(null);
	// Server-assigned on the first turn.done; sent with every follow-up turn.
	let conversationId = $state<string | null>(null);

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
		get selectedModel() {
			return selectedModel;
		},
		get conversationId() {
			return conversationId;
		},
		get activeMessage(): ChatMessage | null {
			if (!activeMessageId) return null;
			return messages.find((m) => m.id === activeMessageId) ?? null;
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
			if (active.isStreaming) return active.content ? 'streaming' : 'planning';
			return active.content ? 'done' : 'idle';
		},

		addUserMessage(content: string): string {
			const id = generateId();
			messages = [
				...messages,
				{
					id,
					role: 'user',
					content,
					timestamp: new Date().toISOString()
				}
			];
			return id;
		},

		startAssistantTurn(): string {
			const id = generateId();
			currentTurnStartTime = Date.now();
			messages = [
				...messages,
				{
					id,
					role: 'assistant',
					content: '',
					timestamp: new Date().toISOString(),
					isStreaming: true,
					error: null
				}
			];
			activeMessageId = id;
			return id;
		},

		handleEvent(event: AgentStreamEvent, targetMessageId?: string) {
			const messageId = targetMessageId ?? activeMessageId;
			if (!messageId) return;

			const idx = messages.findIndex((m) => m.id === messageId);
			if (idx < 0) return;
			activeMessageId = messageId;

			const current = messages[idx];

			switch (event.kind) {
				case 'markdown.delta': {
					const update: Partial<ChatMessage> = {
						content: current.content + event.text,
						isStreaming: true
					};

					if (!current.content && currentTurnStartTime) {
						update.thoughtDurationS = Math.max(
							1,
							Math.round((Date.now() - currentTurnStartTime) / 1000)
						);
						currentTurnStartTime = null;
					}

					messages[idx] = { ...current, ...update };
					break;
				}

				case 'turn.done': {
					conversationId = event.conversationId;
					const update: Partial<ChatMessage> = {
						isStreaming: false,
						sources: event.sources
					};

					if (!current.thoughtDurationS && currentTurnStartTime) {
						update.thoughtDurationS = Math.max(
							1,
							Math.round((Date.now() - currentTurnStartTime) / 1000)
						);
						currentTurnStartTime = null;
					}

					messages[idx] = { ...current, ...update };
					break;
				}

				case 'turn.error':
					messages[idx] = {
						...current,
						isStreaming: false,
						error: event.message
					};
					currentTurnStartTime = null;
					break;
			}
		},

		setSelectedModel(model: string) {
			selectedModel = model;
		},

		initializeSelectedModel(defaultModel: string | null) {
			if (!selectedModel && defaultModel) {
				selectedModel = defaultModel;
			}
		},

		retry(messageId: string): { question: string; userMessageOrdinal: number } | null {
			const idx = messages.findIndex((m) => m.id === messageId);
			if (idx < 0) return null;

			for (let i = idx - 1; i >= 0; i--) {
				if (messages[i].role === 'user') {
					// 1-based count of user messages up to and including this one;
					// the backend uses it to rewind session memory to this point.
					const userMessageOrdinal = messages
						.slice(0, i + 1)
						.filter((m) => m.role === 'user').length;
					const question = messages[i].content;
					messages = messages.slice(0, idx);
					return { question, userMessageOrdinal };
				}
			}

			return null;
		},

		clear() {
			messages = [];
			activeMessageId = null;
			selectedModel = null;
			currentTurnStartTime = null;
			conversationId = null;
		}
	};
}

export const chatStore = createChatStore();
