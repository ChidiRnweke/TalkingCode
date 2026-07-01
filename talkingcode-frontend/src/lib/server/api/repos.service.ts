import type { IngestionRunView, RegisterRepoInput, RepositoryView } from '$lib/models';
import type { ApiClient } from './client';
import { mapIngestionRun, mapRepository } from './mappers/repos';

function errorMessage(error: unknown): string {
	if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
		return error.detail;
	}

	return 'Request failed';
}

export class ReposService {
	constructor(private readonly client: ApiClient) {}

	async listRepos(): Promise<RepositoryView[]> {
		const { data, error } = await this.client.GET('/repos');
		if (error) throw new Error(`Failed to list repositories: ${errorMessage(error)}`);
		if (!data) return [];
		return data.map(mapRepository);
	}

	async listIngestionRuns(owner: string, name: string): Promise<IngestionRunView[]> {
		const { data, error } = await this.client.GET('/repos/{owner}/{name}/runs', {
			params: {
				path: { owner, name }
			}
		});
		if (error) throw new Error(`Failed to list ingestion runs: ${errorMessage(error)}`);
		if (!data) return [];
		return data.map(mapIngestionRun);
	}

	async startIngestion(owner: string, name: string, gitRef?: string): Promise<IngestionRunView> {
		const { data, error } = await this.client.POST('/repos/{owner}/{name}/ingest', {
			params: {
				path: { owner, name }
			},
			body: {
				git_ref: gitRef ?? null
			}
		});
		if (error) throw new Error(`Failed to start ingestion: ${errorMessage(error)}`);
		if (!data) throw new Error('Failed to start ingestion: empty response body');
		return mapIngestionRun(data);
	}

	async startOwnedIngestion(gitRef?: string): Promise<IngestionRunView[]> {
		const { data, error } = await this.client.POST('/repos/ingest-owned', {
			body: {
				git_ref: gitRef ?? null
			}
		});
		if (error) throw new Error(`Failed to ingest owned repositories: ${errorMessage(error)}`);
		if (!data) return [];
		return data.map(mapIngestionRun);
	}

	async registerRepo(input: RegisterRepoInput): Promise<RepositoryView> {
		const { data, error } = await this.client.POST('/repos', {
			body: {
				owner: input.owner,
				name: input.name,
				default_branch: input.defaultBranch ?? 'main'
			}
		});
		if (error) throw new Error(`Failed to register repository: ${errorMessage(error)}`);
		if (!data) throw new Error('Failed to register repository: empty response body');
		return mapRepository(data);
	}
}

