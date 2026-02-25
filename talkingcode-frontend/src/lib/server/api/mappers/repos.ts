import type { IngestionRunInfo, RepositoryInfo } from '$lib/models';
import type { components } from '$lib/api/schema';

type RawRepositoryInfo = components['schemas']['RepositoryInfo'];
type RawIngestionRunInfo = components['schemas']['IngestionRunInfo'];

export function mapRepository(raw: RawRepositoryInfo): RepositoryInfo {
	return {
		id: raw.id,
		provider: raw.provider,
		owner: raw.owner,
		name: raw.name,
		default_branch: raw.default_branch,
		last_ingested_at: raw.last_ingested_at,
		created_at: raw.created_at
	};
}

export function mapIngestionRun(raw: RawIngestionRunInfo): IngestionRunInfo {
	return {
		id: raw.id,
		repository_id: raw.repository_id,
		status: raw.status,
		started_at: raw.started_at,
		completed_at: raw.completed_at,
		error_message: raw.error_message
	};
}
