import type { DependencyHealthStatus, HealthReport } from '$lib/models';
import type { ApiClient } from './client';

type BackendHealthData = {
	status?: string;
	dependencies?: Record<
		string,
		{
			status?: string;
			message?: string | null;
			details?: Record<string, unknown>;
		}
	>;
};

function asHealthReport(raw: BackendHealthData): HealthReport {
	const dependencies = Object.fromEntries(
		Object.entries(raw.dependencies ?? {}).map(([name, dependency]) => [
			name,
			{
				status: dependency.status === 'failed' ? 'failed' : dependency.status === 'skipped' ? 'skipped' : 'ok',
				message: dependency.message ?? null,
				details: dependency.details ?? {}
			} satisfies DependencyHealthStatus
		])
	);

	return {
		status: raw.status === 'failed' ? 'failed' : 'ok',
		dependencies
	};
}

export class HealthService {
	constructor(private readonly client: ApiClient) {}

	async checkBackend(): Promise<DependencyHealthStatus> {
		try {
			const { data, error, response } = await this.client.GET('/health');
			const payload = (data ?? error) as BackendHealthData | undefined;

			if (!payload) {
				return {
					status: 'failed',
					message: `Backend health check returned HTTP ${response.status}`,
					details: {}
				};
			}

			return {
				status: response.ok && payload.status !== 'failed' ? 'ok' : 'failed',
				message: response.ok ? null : `Backend health check returned HTTP ${response.status}`,
				details: {
					report: asHealthReport(payload)
				}
			};
		} catch (error) {
			console.error('Backend health check failed:', error);
			return {
				status: 'failed',
				message: 'Backend health check failed',
				details: {}
			};
		}
	}
}
