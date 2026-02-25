import type { IngestionRunView, RepositoryView } from '$lib/models';
import type { components } from '$lib/api/schema';

type RawRepositoryInfo = components['schemas']['RepositoryInfo'];
type RawIngestionRunInfo = components['schemas']['IngestionRunInfo'];

export function mapRepository(raw: RawRepositoryInfo): RepositoryView {
	return {
		id: raw.id,
		provider: raw.provider,
		owner: raw.owner,
		name: raw.name,
		defaultBranch: raw.default_branch,
		lastIngestedAt: raw.last_ingested_at,
		createdAt: raw.created_at
	};
}

export function mapIngestionRun(raw: RawIngestionRunInfo): IngestionRunView {
	return {
		id: raw.id,
		repositoryId: raw.repository_id,
		status: raw.status,
		startedAt: raw.started_at,
		completedAt: raw.completed_at,
		errorMessage: raw.error_message
	};
}
