/** Repo service implementation */
import type { RepositoryInfo, IngestionRunInfo, RegisterRepoInput } from '$lib/models';
import type { IRepoService } from './IRepoService';

export class RepoService implements IRepoService {
	async listRepos(): Promise<RepositoryInfo[]> {
		const response = await fetch('/api/repos');
		if (!response.ok) throw new Error(`Failed to list repos: ${response.status}`);
		return response.json();
	}

	async getRepo(owner: string, name: string): Promise<RepositoryInfo> {
		const response = await fetch(`/api/repos/${owner}/${name}`);
		if (!response.ok) throw new Error(`Failed to get repo: ${response.status}`);
		return response.json();
	}

	async registerRepo(input: RegisterRepoInput): Promise<RepositoryInfo> {
		const response = await fetch('/api/repos', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				owner: input.owner,
				name: input.name,
				default_branch: input.defaultBranch || 'main'
			})
		});
		if (!response.ok) throw new Error(`Failed to register repo: ${response.status}`);
		return response.json();
	}

	async startIngestion(owner: string, name: string, gitRef?: string): Promise<IngestionRunInfo> {
		const response = await fetch(`/api/repos/${owner}/${name}/ingest`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ git_ref: gitRef || null })
		});
		if (!response.ok) throw new Error(`Failed to start ingestion: ${response.status}`);
		return response.json();
	}

	async listIngestionRuns(owner: string, name: string): Promise<IngestionRunInfo[]> {
		const response = await fetch(`/api/repos/${owner}/${name}/runs`);
		if (!response.ok) throw new Error(`Failed to list runs: ${response.status}`);
		return response.json();
	}
}
