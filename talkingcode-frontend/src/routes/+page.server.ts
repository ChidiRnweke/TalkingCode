import { chatStore } from '$lib/stores/chatStore';
import { AppFactory } from '$lib/factories/AppFactory';

export async function load() {
	return {
		phase: chatStore.phase,
		currentPlan: chatStore.currentPlan,
		timeline: chatStore.timeline,
		streamingContent: chatStore.streamingContent,
		error: chatStore.error
	};
}

export const actions = {
	default: async ({ request }) => {
		const formData = await request.formData();
		const question = formData.get('question')?.toString() || '';
		const conversationId = formData.get('conversationId')?.toString() || null;
		const model = formData.get('model')?.toString() || null;

		if (!question.trim()) {
			return { error: 'Question is required' };
		}

		const controller = AppFactory.getChatController();
		const stream = controller.startAgenticTurn({
			conversationId,
			question,
			model
		});

		// Start processing the stream
		chatStore.startTurn();

		try {
			for await (const event of stream) {
				chatStore.handleEvent(event);
			}
		} catch (e) {
			chatStore.handleEvent({
				kind: 'agent_error',
				turnId: chatStore.currentTurnId || '',
				message: e instanceof Error ? e.message : 'Unknown error',
				timestamp: new Date().toISOString()
			});
		}

		return { success: true };
	}
};
