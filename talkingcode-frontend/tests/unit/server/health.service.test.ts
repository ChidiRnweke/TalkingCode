import { describe, expect, it } from 'vitest';

import type { ApiClient } from '$lib/server/api/client';
import { HealthService } from '$lib/server/api/health.service';

type FakeHealthResponse = {
	data?: unknown;
	error?: unknown;
	response: Response;
};

class FakeApiClient {
	constructor(private readonly result: FakeHealthResponse) {}

	GET() {
		return Promise.resolve(this.result);
	}
}

function makeService(result: FakeHealthResponse): HealthService {
	return new HealthService(new FakeApiClient(result) as unknown as ApiClient);
}

describe('HealthService', () => {
	it('returns ok when backend health succeeds', async () => {
		const service = makeService({
			data: {
				status: 'ok',
				dependencies: {
					database: { status: 'ok', details: {} }
				}
			},
			response: new Response(null, { status: 200 })
		});

		const result = await service.checkBackend();

		expect(result.status).toBe('ok');
	});

	it('returns failed when backend health fails', async () => {
		const service = makeService({
			error: {
				status: 'failed',
				dependencies: {
					database: { status: 'failed', details: {} }
				}
			},
			response: new Response(null, { status: 500 })
		});

		const result = await service.checkBackend();

		expect(result.status).toBe('failed');
	});
});
