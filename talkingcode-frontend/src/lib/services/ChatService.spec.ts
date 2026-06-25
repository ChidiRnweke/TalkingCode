import { describe, expect, it } from 'vitest';

import { parseAgentEvent } from './ChatService';

describe('parseAgentEvent', () => {
	it('parses turn.started event', () => {
		const event = parseAgentEvent(
			'turn.started',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				message: 'Turn started',
				visible_args: { model: 'test-model' }
			})
		);

		expect(event).toEqual({
			kind: 'turn.started',
			turnId: 'turn-1',
			model: 'test-model',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses message.delta event', () => {
		const event = parseAgentEvent(
			'message.delta',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				iteration: 2,
				message: 'Hello'
			})
		);

		expect(event).toEqual({
			kind: 'message.delta',
			turnId: 'turn-1',
			iteration: 2,
			token: 'Hello',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses streamed tool call delta without raw arguments', () => {
		const event = parseAgentEvent(
			'tool_call.delta',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				tool_name: 'search_github',
				call_id: 'call-1',
				iteration: 1,
				index: 0,
				message: 'Tool call streamed',
				visible_args: { phase: 'arguments' }
			})
		);

		expect(event).toEqual({
			kind: 'tool_call.delta',
			turnId: 'turn-1',
			toolName: 'search_github',
			callId: 'call-1',
			iteration: 1,
			index: 0,
			phase: 'arguments',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses tool_call.started with sanitized visible args', () => {
		const event = parseAgentEvent(
			'tool_call.started',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				tool_name: 'search_github',
				call_id: 'call-1',
				iteration: 1,
				index: 0,
				message: 'Starting search_github',
				visible_args: { query: 'auth' }
			})
		);

		expect(event).toEqual({
			kind: 'tool_call.started',
			turnId: 'turn-1',
			toolName: 'search_github',
			callId: 'call-1',
			iteration: 1,
			index: 0,
			visibleArgs: { query: 'auth' },
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses tool_call.completed with null error_code', () => {
		const event = parseAgentEvent(
			'tool_call.completed',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				tool_name: 'search_github',
				call_id: 'call-1',
				iteration: 1,
				index: 0,
				message: 'Completed search_github',
				visible_args: { success: true, duration_ms: 1234, error_code: null }
			})
		);

		expect(event).toEqual({
			kind: 'tool_call.completed',
			turnId: 'turn-1',
			toolName: 'search_github',
			callId: 'call-1',
			iteration: 1,
			index: 0,
			success: true,
			durationMs: 1234,
			errorCode: undefined,
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses tool_result.available', () => {
		const event = parseAgentEvent(
			'tool_result.available',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				tool_name: 'search_github',
				call_id: 'call-1',
				iteration: 1,
				index: 0,
				message: 'Tool result available',
				visible_args: { success: true, error_code: null }
			})
		);

		expect(event).toEqual({
			kind: 'tool_result.available',
			turnId: 'turn-1',
			toolName: 'search_github',
			callId: 'call-1',
			iteration: 1,
			index: 0,
			success: true,
			errorCode: undefined,
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses turn.done with citation sources', () => {
		const event = parseAgentEvent(
			'turn.done',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				message: 'Turn complete',
				visible_args: {
					sources: [
						{
							index: 1,
							repository: 'owner/repo',
							path: 'backend/app.py',
							start_line: 10,
							end_line: 20,
							similarity_score: 0.9
						}
					]
				}
			})
		);

		expect(event).toEqual({
			kind: 'turn.done',
			turnId: 'turn-1',
			sources: [
				{
					index: 1,
					repository: 'owner/repo',
					path: 'backend/app.py',
					startLine: 10,
					endLine: 20,
					similarityScore: 0.9
				}
			],
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses turn.error', () => {
		const event = parseAgentEvent(
			'turn.error',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				message: 'failed',
				code: 'agent_error'
			})
		);

		expect(event).toEqual({
			kind: 'turn.error',
			turnId: 'turn-1',
			message: 'failed',
			code: 'agent_error',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('rejects unknown fields on strict schemas', () => {
		const event = parseAgentEvent(
			'turn.done',
			JSON.stringify({
				turn_id: 'turn-1',
				timestamp: '2026-01-01T00:00:00Z',
				extra: true
			})
		);

		expect(event).toBeNull();
	});

	it('rejects invalid json payload', () => {
		const event = parseAgentEvent('turn.done', '{not-json');
		expect(event).toBeNull();
	});
});
