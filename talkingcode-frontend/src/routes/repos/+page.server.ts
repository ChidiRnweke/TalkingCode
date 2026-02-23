import { fail } from '@sveltejs/kit';
import { RepoServiceServer } from '$lib/services/RepoServiceServer';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const repoService = new RepoServiceServer(fetch);

	try {
		const repos = await repoService.listRepos();
		return { repos };
	} catch {
		return { repos: [] };
	}
};

export const actions: Actions = {
	register: async ({ request, fetch }) => {
		const data = await request.formData();
		const owner = String(data.get('owner') ?? '').trim();
		const name = String(data.get('name') ?? '').trim();
		const defaultBranch = String(data.get('defaultBranch') ?? 'main').trim() || 'main';

		if (!owner || !name) {
			return fail(400, { error: 'Owner and repository name are required.' });
		}

		try {
			const repoService = new RepoServiceServer(fetch);
			await repoService.registerRepo({ owner, name, defaultBranch });
			return { success: true };
		} catch (error) {
			return fail(500, { error: error instanceof Error ? error.message : 'Failed to register repo.' });
		}
	},

	ingest: async ({ request, fetch }) => {
		const data = await request.formData();
		const owner = String(data.get('owner') ?? '').trim();
		const name = String(data.get('name') ?? '').trim();

		if (!owner || !name) {
			return fail(400, { error: 'Owner and repository name are required.' });
		}

		try {
			const repoService = new RepoServiceServer(fetch);
			await repoService.startIngestion(owner, name);
			return { success: true };
		} catch (error) {
			return fail(500, { error: error instanceof Error ? error.message : 'Failed to start ingestion.' });
		}
	},

	ingestOwned: async ({ fetch }) => {
		try {
			const repoService = new RepoServiceServer(fetch);
			await repoService.startOwnedIngestion();
			return { success: true };
		} catch (error) {
			return fail(500, {
				error:
					error instanceof Error ? error.message : 'Failed to ingest owned repositories.'
			});
		}
	}
};
