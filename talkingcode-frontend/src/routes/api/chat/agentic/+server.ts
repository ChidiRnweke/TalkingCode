/** API route for agentic chat */
import { json, type RequestHandler } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const backendUrl = env.BACKEND_URL || 'http://localhost:8000';

	try {
		const response = await fetch(`${backendUrl}/chat/agentic`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body)
		});

		if (!response.ok) {
			return json({ error: 'Backend error' }, { status: response.status });
		}

		// Stream response through
		return new Response(response.body, {
			headers: {
				'Content-Type': 'text/event-stream',
				'Cache-Control': 'no-cache',
				Connection: 'keep-alive'
			}
		});
	} catch (error) {
		console.error('Chat proxy error:', error);
		return json({ error: 'Internal error' }, { status: 500 });
	}
};
