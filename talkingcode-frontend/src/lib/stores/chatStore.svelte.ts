/** Chat store with multi-turn conversation support */
import type {
	AgentStreamEvent,
	ToolCallTimelineItem,
	ChatMessage,
	ReasoningStep,
	AssistantPart
} from '$lib/models';

type TurnPhase = 'idle' | 'planning' | 'tools' | 'streaming' | 'done' | 'error';

function createChatStore() {
	let messages = $state<ChatMessage[]>([]);
	let activeMessageId = $state<string | null>(null);
	let selectedModel = $state<string | null>(null);
	let currentTurnStartTime = $state<number | null>(null);

	function generateId(): string {
		return crypto.randomUUID();
	}

	function toolStepId(callId: string | undefined, toolName: string, timestamp: string): string {
		return callId ? `tool-${callId}` : `tool-${toolName}-${timestamp}`;
	}

	function textPartId(timestamp: string, count: number): string {
		return `text-${timestamp}-${count}`;
	}

	function appendTextPart(parts: AssistantPart[] | undefined, token: string, timestamp: string): AssistantPart[] {
		const next = [...(parts ?? [])];
		const last = next.at(-1);

		if (last?.kind === 'text') {
			next[next.length - 1] = {
				...last,
				text: last.text + token,
				timestamp
			};
			return next;
		}

		next.push({
			id: textPartId(timestamp, next.length),
			kind: 'text',
			text: token,
			timestamp
		});
		return next;
	}

	function updateToolPart(
		parts: AssistantPart[] | undefined,
		callId: string | undefined,
		toolName: string,
		update: Partial<ToolCallTimelineItem>,
		timestamp: string
	): AssistantPart[] {
		const next = [...(parts ?? [])];
		const index = next.findLastIndex((part) => {
			if (part.kind !== 'tool') return false;
			if (callId && part.tool.callId) return part.tool.callId === callId;
			return part.tool.toolName === toolName && part.tool.status === 'started';
		});

		if (index >= 0 && next[index].kind === 'tool') {
			const part = next[index];
			next[index] = {
				...part,
				tool: { ...part.tool, ...update },
				timestamp
			};
		}

		return next;
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
			const hasReasoning = !!active.reasoningSteps?.length;
			if (active.isStreaming) {
				if (active.content) return 'streaming';
				if (hasReasoning || active.plan || active.planText || active.toolCalls?.length) return 'tools';
				return 'planning';
			}
			if (hasReasoning || active.plan || active.planText || active.toolCalls?.length) return 'done';
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
				reasoningSteps: [],
				isStreaming: true,
				error: null
			};
			messages = [...messages, assistantMessage];
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
				case 'turn.started':
					messages[idx] = {
						...current,
						reasoningSteps: current.reasoningSteps ?? []
					};
					break;

				case 'tool_call.delta':
					messages[idx] = {
						...current,
						reasoningSteps: current.reasoningSteps ?? []
					};
					break;

				case 'tool_call.started': {
					const newToolCall: ToolCallTimelineItem = {
						turnId: event.turnId,
						toolName: event.toolName,
						callId: event.callId,
						iteration: event.iteration,
						visibleArgs: event.visibleArgs,
						status: 'started',
						timestamp: event.timestamp
					};

					const reasoningSteps: ReasoningStep[] = [
						...(current.reasoningSteps ?? []),
						{
							id: toolStepId(event.callId, event.toolName, event.timestamp),
							kind: 'tool',
							tool: newToolCall,
							timestamp: event.timestamp
						}
					];
					const parts: AssistantPart[] = [
						...(current.parts ?? []),
						{
							id: toolStepId(event.callId, event.toolName, event.timestamp),
							kind: 'tool',
							tool: newToolCall,
							timestamp: event.timestamp
						}
					];

					messages[idx] = {
						...current,
						toolCalls: [...(current.toolCalls ?? []), newToolCall],
						reasoningSteps,
						parts
					};
					break;
				}

				case 'tool_call.completed': {
					const toolCalls = current.toolCalls ?? [];
					const idxToUpdate = toolCalls.findLastIndex((t) => {
						if (event.callId && t.callId) {
							return t.callId === event.callId;
						}
						return (
							t.turnId === event.turnId &&
							t.toolName === event.toolName &&
							t.status === 'started'
						);
					});

					if (idxToUpdate !== -1) {
						const newToolCalls = [...toolCalls];
						newToolCalls[idxToUpdate] = {
							...newToolCalls[idxToUpdate],
							status: event.success ? 'finished' : 'failed',
							durationMs: event.durationMs
						};

						const reasoningSteps = [...(current.reasoningSteps ?? [])];
						const stepId = toolStepId(event.callId, event.toolName, event.timestamp);
						const stepIndex = reasoningSteps.findLastIndex(
							(step) =>
								step.kind === 'tool' &&
								(step.id === stepId ||
									(step.tool.toolName === event.toolName &&
										step.tool.status === 'started' &&
										(!event.callId || step.tool.callId === event.callId)))
						);

						if (stepIndex >= 0 && reasoningSteps[stepIndex].kind === 'tool') {
							reasoningSteps[stepIndex] = {
								...reasoningSteps[stepIndex],
								tool: {
									...reasoningSteps[stepIndex].tool,
									status: event.success ? 'finished' : 'failed',
									durationMs: event.durationMs,
									errorCode: event.errorCode
								},
								timestamp: event.timestamp
							};
						}

						const parts = updateToolPart(
							current.parts,
							event.callId,
							event.toolName,
							{
								status: event.success ? 'finished' : 'failed',
								durationMs: event.durationMs,
								errorCode: event.errorCode
							},
							event.timestamp
						);

						messages[idx] = { ...current, toolCalls: newToolCalls, reasoningSteps, parts };
					}
					break;
				}

				case 'tool_result.available':
					break;

				case 'message.delta': {
					const update: Partial<ChatMessage> = {
						content: current.content + event.token,
						isStreaming: true,
						parts: appendTextPart(current.parts, event.token, event.timestamp)
					};

					if (!current.content && currentTurnStartTime) {
						update.thoughtDurationS = Math.max(1, Math.round((Date.now() - currentTurnStartTime) / 1000));
						currentTurnStartTime = null;
					}

					messages[idx] = { ...current, ...update };
					break;
				}

				case 'turn.done': {
					const update: Partial<ChatMessage> = {
						isStreaming: false,
						sources: event.sources
					};

					if (!current.thoughtDurationS && currentTurnStartTime) {
						update.thoughtDurationS = Math.max(1, Math.round((Date.now() - currentTurnStartTime) / 1000));
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
				selectedModel = null;
				currentTurnStartTime = null;
			}
	};
}

export const chatStore = createChatStore();
