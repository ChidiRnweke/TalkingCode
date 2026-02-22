import { AppFactory } from '$lib/factories/AppFactory';

export async function load() {
	// Server-side load - return empty initial state
	// Client-side store will be populated from events
	return {
		phase: 'idle',
		currentPlan: null,
		timeline: [],
		streamingContent: '',
		error: null
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

		// Return the question data for the client to process
		return { 
			success: true,
			question,
			conversationId,
			model
		};
	}
};
