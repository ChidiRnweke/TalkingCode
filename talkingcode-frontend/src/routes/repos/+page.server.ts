import { createReposService } from '$lib/server/api/repos.service';
import type { IngestionRunView } from '$lib/models';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const repoService = createReposService(fetch);

	try {
		const repos = await repoService.listRepos();
		const runsByRepo: Record<string, Promise<IngestionRunView[]>> = Object.fromEntries(
			repos.map((repo) => [
				repo.id,
				repoService.listIngestionRuns(repo.owner, repo.name).catch(() => [])
			])
		);

		return { repos, runsByRepo };
	} catch {
		return { repos: [], runsByRepo: {} };
	}
};
