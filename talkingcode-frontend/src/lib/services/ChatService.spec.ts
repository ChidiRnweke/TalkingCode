import { describe, expect, it } from 'vitest';

import { parseAgentEvent } from './ChatService';

describe('parseAgentEvent', () => {
	it('parses valid plan_done event', () => {
		const event = parseAgentEvent(
			'plan_done',
			JSON.stringify({
				turn_id: 'turn-1',
				iteration: 1,
				timestamp: '2026-01-01T00:00:00Z',
				message: 'done',
				visible_args: { plan_text: 'Plan text' }
			})
		);

		expect(event).toEqual({
			kind: 'plan_done',
			turnId: 'turn-1',
			iteration: 1,
			planText: 'Plan text',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('rejects unknown fields on strict schemas', () => {
		const event = parseAgentEvent(
			'assistant_done',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				extra: true
			})
		);

		expect(event).toBeNull();
	});

	it('rejects missing required fields', () => {
		const event = parseAgentEvent(
			'tool_call_finished',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				tool_name: 'run_retriever',
				visible_args: { success: true }
			})
		);

		expect(event).toBeNull();
	});

	it('rejects unknown event type', () => {
		const event = parseAgentEvent(
			'planner_ready',
			JSON.stringify({ turn_id: 'turn-1', timestamp: '2026-01-01T00:00:00Z' })
		);

		expect(event).toBeNull();
	});

	it('rejects invalid json payload', () => {
		const event = parseAgentEvent('assistant_done', '{not-json');
		expect(event).toBeNull();
	});

	it('accepts backend-style iteration_started payload', () => {
		const event = parseAgentEvent(
			'iteration_started',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				iteration: 2,
				message: 'Iteration 2',
				visible_args: { iteration: 2 }
			})
		);

		expect(event).toEqual({
			kind: 'iteration_started',
			turnId: 'turn-1',
			iteration: 2,
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('accepts backend-style tool_call_started without visible_args', () => {
		const event = parseAgentEvent(
			'tool_call_started',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				tool_name: 'run_retriever',
				call_id: 'call-1',
				message: 'Starting run_retriever'
			})
		);

		expect(event).toEqual({
			kind: 'tool_call_started',
			turnId: 'turn-1',
			toolName: 'run_retriever',
			callId: 'call-1',
			iteration: undefined,
			visibleArgs: {},
			timestamp: '2026-01-01T00:00:00Z'
		});
	});
});
