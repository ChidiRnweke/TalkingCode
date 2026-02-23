import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8000';

export const GET: RequestHandler = async ({ fetch }) => {
	const response = await fetch(`${BACKEND_URL}/repos`);
	const data = await response.json();
	return new Response(JSON.stringify(data), {
		status: response.status,
		headers: { 'Content-Type': 'application/json' }
	});
};

export const POST: RequestHandler = async ({ request, fetch }) => {
	const body = await request.json();
	const response = await fetch(`${BACKEND_URL}/repos`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	const data = await response.json();
	return new Response(JSON.stringify(data), {
		status: response.status,
		headers: { 'Content-Type': 'application/json' }
	});
};
