import { describe, expect, it } from 'vitest';

import type { DependencyHealthStatus } from '$lib/models';
import { HealthController, type IHealthService } from '$lib/server/controllers/HealthController';

class FakeHealthService implements IHealthService {
	constructor(private readonly backend: DependencyHealthStatus) {}

	checkBackend(): Promise<DependencyHealthStatus> {
		return Promise.resolve(this.backend);
	}
}

describe('HealthController', () => {
	it('returns failed when backend dependency fails', async () => {
		const controller = new HealthController(
			new FakeHealthService({
				status: 'failed',
				message: 'Backend failed',
				details: {}
			})
		);

		const result = await controller.checkHealth();

		expect(result.status).toBe('failed');
	});

	it('returns ok when backend dependency succeeds', async () => {
		const controller = new HealthController(
			new FakeHealthService({
				status: 'ok',
				details: {}
			})
		);

		const result = await controller.checkHealth();

		expect(result.status).toBe('ok');
	});
});
