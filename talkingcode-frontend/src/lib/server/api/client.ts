import { env } from '$env/dynamic/private';
import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from '$lib/api/schema';

const DEFAULT_BACKEND_URL = 'http://localhost:8000';

const INGESTION_AUTH_ENDPOINTS = new Set([
	'/repos',
	'/repos/ingest-owned',
	'/repos/{owner}/{name}/ingest'
]);

type OpenApiClient = ReturnType<typeof createClient<paths>>;

export type ApiClient = OpenApiClient;

function requiresIngestionAuth(schemaPath: string, method: string): boolean {
	return method === 'POST' && INGESTION_AUTH_ENDPOINTS.has(schemaPath);
}

const ingestionAuthMiddleware: Middleware = {
	onRequest({ request, schemaPath }) {
		if (!requiresIngestionAuth(schemaPath, request.method)) {
			return request;
		}

		if (!env.INGESTION_API_KEY) {
			return request;
		}

		const headers = new Headers(request.headers);
		headers.set('X-API-Key', env.INGESTION_API_KEY);
		return new Request(request, { headers });
	}
};

export function createApiClient(fetchFn?: typeof fetch): ApiClient {
	const client = createClient<paths>({
		baseUrl: env.BACKEND_URL || DEFAULT_BACKEND_URL,
		fetch: fetchFn
	});

	client.use(ingestionAuthMiddleware);

	return client;
}
