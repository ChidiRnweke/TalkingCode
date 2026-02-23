import { env } from '$env/dynamic/private';
import type { IngestionRunInfo, RegisterRepoInput, RepositoryInfo } from '$lib/models';
import type { IRepoService } from './IRepoService';

type ServerFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export class RepoServiceServer implements IRepoService {
	constructor(
		private readonly fetchFn: ServerFetch,
		private readonly backendUrl: string = env.BACKEND_URL || 'http://localhost:8000'
	) {}

	async listRepos(): Promise<RepositoryInfo[]> {
		const response = await this.fetchFn(`${this.backendUrl}/repos`);
		if (!response.ok) throw new Error(`Failed to list repos: ${response.status}`);
		return response.json();
	}

	async getRepo(owner: string, name: string): Promise<RepositoryInfo> {
		const response = await this.fetchFn(`${this.backendUrl}/repos/${owner}/${name}`);
		if (!response.ok) throw new Error(`Failed to get repo: ${response.status}`);
		return response.json();
	}

	async registerRepo(input: RegisterRepoInput): Promise<RepositoryInfo> {
		const response = await this.fetchFn(`${this.backendUrl}/repos`, {
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
		const response = await this.fetchFn(`${this.backendUrl}/repos/${owner}/${name}/ingest`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ git_ref: gitRef || null })
		});
		if (!response.ok) throw new Error(`Failed to start ingestion: ${response.status}`);
		return response.json();
	}

	async listIngestionRuns(owner: string, name: string): Promise<IngestionRunInfo[]> {
		const response = await this.fetchFn(`${this.backendUrl}/repos/${owner}/${name}/runs`);
		if (!response.ok) throw new Error(`Failed to list runs: ${response.status}`);
		return response.json();
	}

	async startOwnedIngestion(gitRef?: string): Promise<IngestionRunInfo[]> {
		const headers: Record<string, string> = { 'Content-Type': 'application/json' };
		if (env.INGESTION_API_KEY) {
			headers['X-API-Key'] = env.INGESTION_API_KEY;
		}

		const response = await this.fetchFn(`${this.backendUrl}/repos/ingest-owned`, {
			method: 'POST',
			headers,
			body: JSON.stringify({ git_ref: gitRef || null })
		});
		if (!response.ok) throw new Error(`Failed to ingest owned repositories: ${response.status}`);
		return response.json();
	}
}
