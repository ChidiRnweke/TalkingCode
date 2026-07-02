import { describe, expect, it } from 'vitest';

import { parseAgentEvent } from '$lib/services/ChatService';

describe('parseAgentEvent', () => {
	it('parses markdown deltas', () => {
		const event = parseAgentEvent(
			'markdown.delta',
			JSON.stringify({
				text: 'Hello',
				timestamp: '2026-01-01T00:00:00Z'
			})
		);

		expect(event).toEqual({
			kind: 'markdown.delta',
			text: 'Hello',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('parses turn.done with citation sources', () => {
		const event = parseAgentEvent(
			'turn.done',
			JSON.stringify({
				turn_id: 'turn-1',
				conversation_id: 'conv-1',
				timestamp: '2026-01-01T00:00:00Z',
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
			})
		);

		expect(event).toEqual({
			kind: 'turn.done',
			turnId: 'turn-1',
			conversationId: 'conv-1',
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
				message: 'boom',
				code: 'agent_error'
			})
		);

		expect(event).toEqual({
			kind: 'turn.error',
			turnId: 'turn-1',
			message: 'boom',
			code: 'agent_error',
			timestamp: '2026-01-01T00:00:00Z'
		});
	});

	it('ignores unknown events', () => {
		const event = parseAgentEvent('tool_call.started', JSON.stringify({}));

		expect(event).toBeNull();
	});
});
