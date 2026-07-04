import { env } from '$env/dynamic/private';
import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from '$lib/api/schema';
import type { ApiClient } from '$lib/server/api/client';
import { HealthService } from '$lib/server/api/health.service';
import { HealthController } from '$lib/server/controllers/HealthController';
import { ModelsService } from '$lib/server/api/models.service';
import { ReposService } from '$lib/server/api/repos.service';

export class ServerFactory {
	private static readonly DEFAULT_BACKEND_URL = 'http://localhost:8000';

	private static readonly INGESTION_AUTH_ENDPOINTS = new Set([
		'/repos',
		'/repos/ingest-owned',
		'/repos/{owner}/{name}/ingest'
	]);

	private static requiresIngestionAuth(schemaPath: string, method: string): boolean {
		return method === 'POST' && ServerFactory.INGESTION_AUTH_ENDPOINTS.has(schemaPath);
	}

	private static readonly ingestionAuthMiddleware: Middleware = {
		onRequest({ request, schemaPath }) {
			if (!ServerFactory.requiresIngestionAuth(schemaPath, request.method)) {
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

	private static createApiClient(fetchFn?: typeof fetch): ApiClient {
		const client = createClient<paths>({
			baseUrl: env.BACKEND_URL || ServerFactory.DEFAULT_BACKEND_URL,
			fetch: fetchFn
		});

		client.use(ServerFactory.ingestionAuthMiddleware);

		return client;
	}

	static getModelsService(fetchFn?: typeof fetch): ModelsService {
		return new ModelsService(ServerFactory.createApiClient(fetchFn));
	}

	static getReposService(fetchFn?: typeof fetch): ReposService {
		return new ReposService(ServerFactory.createApiClient(fetchFn));
	}

	static getHealthController(fetchFn?: typeof fetch): HealthController {
		return new HealthController(new HealthService(ServerFactory.createApiClient(fetchFn)));
	}
}
