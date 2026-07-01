import { ServerFactory } from '$lib/server/ServerFactory';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const modelsService = ServerFactory.getModelsService(fetch);

	try {
		return modelsService.listModels();
	} catch {
		return { models: [], defaultModel: null };
	}
};
