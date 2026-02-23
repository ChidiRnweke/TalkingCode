import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8000';

export const POST: RequestHandler = async ({ request, fetch }) => {
	const body = await request.json().catch(() => ({}));
	const headers: Record<string, string> = { 'Content-Type': 'application/json' };

	if (env.INGESTION_API_KEY) {
		headers['X-API-Key'] = env.INGESTION_API_KEY;
	}

	const response = await fetch(`${BACKEND_URL}/repos/ingest-owned`, {
		method: 'POST',
		headers,
		body: JSON.stringify(body)
	});

	const data = await response.json();
	return new Response(JSON.stringify(data), {
		status: response.status,
		headers: { 'Content-Type': 'application/json' }
	});
};
