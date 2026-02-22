/** Chat store with agentic turn lifecycle */
import type { AgentStreamEvent, ToolCallTimelineItem, AgentPlanView } from '$lib/models';

type TurnPhase = 'idle' | 'planning' | 'tools' | 'streaming' | 'done' | 'error';

function createChatStore() {
	let phase = $state<TurnPhase>('idle');
	let currentPlan = $state<AgentPlanView | null>(null);
	let timeline = $state<ToolCallTimelineItem[]>([]);
	let streamingContent = $state('');
	let error = $state<string | null>(null);
	let currentTurnId = $state<string | null>(null);

	return {
		get phase() {
			return phase;
		},
		get currentPlan() {
			return currentPlan;
		},
		get timeline() {
			return timeline;
		},
		get streamingContent() {
			return streamingContent;
		},
		get error() {
			return error;
		},
		get currentTurnId() {
			return currentTurnId;
		},

		startTurn() {
			phase = 'planning';
			currentPlan = null;
			timeline = [];
			streamingContent = '';
			error = null;
		},

		handleEvent(event: AgentStreamEvent) {
			switch (event.kind) {
				case 'planner_started':
					phase = 'planning';
					currentTurnId = event.turnId;
					break;

				case 'planner_ready':
					currentPlan = {
						intent: event.intent,
						filters: event.filters,
						toolGroups: []
					};
					phase = 'tools';
					break;

				case 'tool_call_started':
					phase = 'tools';
					timeline = [
						{
							turnId: event.turnId,
							toolName: event.toolName,
							visibleArgs: event.visibleArgs,
							status: 'started',
							timestamp: event.timestamp
						},
						...timeline
					];
					break;

				case 'tool_call_finished': {
					const idx = timeline.findIndex(
						(t) =>
							t.turnId === event.turnId && t.toolName === event.toolName && t.status === 'started'
					);
					if (idx >= 0) {
						timeline[idx] = {
							...timeline[idx],
							status: event.success ? 'finished' : 'failed',
							durationMs: event.durationMs
						};
					}
					break;
				}

				case 'assistant_token':
					phase = 'streaming';
					streamingContent += event.token;
					break;

				case 'assistant_done':
					phase = 'done';
					break;

				case 'agent_error':
					phase = 'error';
					error = event.message;
					break;
			}
		},

		reset() {
			phase = 'idle';
			currentPlan = null;
			timeline = [];
			streamingContent = '';
			error = null;
			currentTurnId = null;
		}
	};
}

export const chatStore = createChatStore();
