import { env } from '$env/dynamic/private';
import type { PageServerLoad } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8000';

export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const response = await fetch(`${BACKEND_URL}/models`);
		if (!response.ok) {
			return { models: [], defaultModel: null };
		}

		const data = await response.json();
		return {
			models: Array.isArray(data.models) ? data.models : [],
			defaultModel: typeof data.default === 'string' ? data.default : null
		};
	} catch {
		return { models: [], defaultModel: null };
	}
};
