import { RepoServiceServer } from '$lib/services/RepoServiceServer';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const repoService = new RepoServiceServer(fetch);

	try {
		const repos = await repoService.listRepos();
		return { repos };
	} catch {
		return { repos: [] };
	}
};
