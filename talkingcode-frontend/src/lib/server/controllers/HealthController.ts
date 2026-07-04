import type { HealthReport } from '$lib/models';

export interface IHealthService {
	checkBackend(): Promise<HealthReport['dependencies'][string]>;
}

export class HealthController {
	constructor(private readonly healthService: IHealthService) {}

	async checkHealth(): Promise<HealthReport> {
		const backend = await this.healthService.checkBackend();

		return {
			status: backend.status === 'failed' ? 'failed' : 'ok',
			dependencies: {
				backend
			}
		};
	}
}
