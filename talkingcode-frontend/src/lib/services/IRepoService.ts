/** Repo service interface */
import type { RepositoryInfo, IngestionRunInfo, RegisterRepoInput } from '$lib/models';

export interface IRepoService {
	listRepos(): Promise<RepositoryInfo[]>;
	getRepo(owner: string, name: string): Promise<RepositoryInfo>;
	registerRepo(input: RegisterRepoInput): Promise<RepositoryInfo>;
	startIngestion(owner: string, name: string, gitRef?: string): Promise<IngestionRunInfo>;
	startOwnedIngestion(gitRef?: string): Promise<IngestionRunInfo[]>;
	listIngestionRuns(owner: string, name: string): Promise<IngestionRunInfo[]>;
}
