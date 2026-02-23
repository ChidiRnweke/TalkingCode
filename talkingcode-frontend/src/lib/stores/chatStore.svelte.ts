/** Chat store with multi-turn conversation support */
import type {
	AgentStreamEvent,
	ToolCallTimelineItem,
	AgentPlanView,
	ChatMessage,
	ReasoningStep
} from '$lib/models';

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

	function planStepId(iteration: number): string {
		return `plan-${iteration}`;
	}

	function toolStepId(callId: string | undefined, toolName: string, timestamp: string): string {
		return callId ? `tool-${callId}` : `tool-${toolName}-${timestamp}`;
	}

	function appendPlanText(existing: string | undefined, iteration: number, planText: string): string {
		const trimmed = planText.trim();
		if (!trimmed) {
			return existing ?? '';
		}

		const block = `Plan ${iteration}\n${trimmed}`;
		if (!existing || !existing.trim()) {
			return block;
		}

		return `${existing.trimEnd()}\n\n${block}`;
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

		handleEvent(event: AgentStreamEvent) {
			if (!activeMessageId) return;

			const idx = messages.findIndex((m) => m.id === activeMessageId);
			if (idx < 0) return;

			const current = messages[idx];

			switch (event.kind) {
				case 'iteration_started':
					messages[idx] = {
						...current,
						planText: current.planText ?? '',
						reasoningSteps: current.reasoningSteps ?? []
					};
					break;

				case 'plan_chunk': {
					const reasoningSteps = [...(current.reasoningSteps ?? [])];
					const stepId = planStepId(event.iteration);
					const existingIndex = reasoningSteps.findIndex((step) => step.id === stepId && step.kind === 'plan');

					if (existingIndex >= 0 && reasoningSteps[existingIndex].kind === 'plan') {
						const existing = reasoningSteps[existingIndex];
						reasoningSteps[existingIndex] = {
							...existing,
							text: existing.text + event.chunk,
							timestamp: event.timestamp
						};
					} else {
						reasoningSteps.push({
							id: stepId,
							kind: 'plan',
							iteration: event.iteration,
							text: event.chunk,
							timestamp: event.timestamp
						});
					}

					messages[idx] = {
						...current,
						reasoningSteps
					};
					break;
				}

				case 'plan_done': {
					if (event.planText) {
						const reasoningSteps = [...(current.reasoningSteps ?? [])];
						const stepId = planStepId(event.iteration);
						const existingIndex = reasoningSteps.findIndex((step) => step.id === stepId && step.kind === 'plan');

						if (existingIndex >= 0) {
							reasoningSteps[existingIndex] = {
								id: stepId,
								kind: 'plan',
								iteration: event.iteration,
								text: event.planText,
								timestamp: event.timestamp
							};
						} else {
							reasoningSteps.push({
								id: stepId,
								kind: 'plan',
								iteration: event.iteration,
								text: event.planText,
								timestamp: event.timestamp
							});
						}

						messages[idx] = {
							...current,
							planText: appendPlanText(current.planText, event.iteration, event.planText),
							reasoningSteps
						};
					}
					break;
				}

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

					const reasoningSteps: ReasoningStep[] = [
						...(current.reasoningSteps ?? []),
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
						reasoningSteps
					};
					break;
				}

				case 'tool_call_finished': {
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

						messages[idx] = { ...current, toolCalls: newToolCalls, reasoningSteps };
					}
					break;
				}

				case 'answer_phase_started':
					messages[idx] = {
						...current,
						reasoningSteps: [
							...(current.reasoningSteps ?? []),
							{
								id: `phase-answer-${event.timestamp}`,
								kind: 'phase',
								phase: 'answer_started',
								iteration: event.iteration,
								timestamp: event.timestamp
							}
						]
					};
					break;

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
			detailPanelMessageId = null;
		}
	};
}

export const chatStore = createChatStore();
