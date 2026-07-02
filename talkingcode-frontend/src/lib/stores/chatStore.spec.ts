import { beforeEach, describe, expect, it } from 'vitest';
import { chatStore } from './chatStore.svelte';

function seedConversation() {
	chatStore.addUserMessage('q1');
	const a1 = chatStore.startAssistantTurn();
	chatStore.handleEvent(
		{
			kind: 'turn.done',
			turnId: a1,
			conversationId: 'conv-1',
			timestamp: new Date().toISOString()
		},
		a1
	);
	chatStore.addUserMessage('q2');
	const a2 = chatStore.startAssistantTurn();
	chatStore.handleEvent(
		{
			kind: 'turn.done',
			turnId: a2,
			conversationId: 'conv-1',
			timestamp: new Date().toISOString()
		},
		a2
	);
	return { a1, a2 };
}

describe('chatStore.retry', () => {
	beforeEach(() => {
		chatStore.clear();
	});

	it('returns the question and ordinal of the last turn and truncates it', () => {
		const { a2 } = seedConversation();

		const result = chatStore.retry(a2);

		expect(result).toEqual({ question: 'q2', userMessageOrdinal: 2 });
		expect(chatStore.messages.map((m) => m.content)).toEqual(['q1', '', 'q2']);
	});

	it('retrying a middle assistant message truncates everything after it', () => {
		const { a1 } = seedConversation();

		const result = chatStore.retry(a1);

		expect(result).toEqual({ question: 'q1', userMessageOrdinal: 1 });
		expect(chatStore.messages.map((m) => m.content)).toEqual(['q1']);
	});

	it('returns null and keeps messages when there is no preceding user message', () => {
		const orphan = chatStore.startAssistantTurn();

		const result = chatStore.retry(orphan);

		expect(result).toBeNull();
		expect(chatStore.messages).toHaveLength(1);
	});

	it('returns null for an unknown message id', () => {
		seedConversation();

		expect(chatStore.retry('missing')).toBeNull();
		expect(chatStore.messages).toHaveLength(4);
	});
});
