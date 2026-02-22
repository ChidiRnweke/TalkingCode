import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const response = await fetch('/api/repos');
		if (!response.ok) {
			return { repos: [] };
		}
		const repos = await response.json();
		return { repos };
	} catch {
		return { repos: [] };
	}
};
