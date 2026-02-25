import { createModelsService } from '$lib/server/api/models.service';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const modelsService = createModelsService(fetch);

	try {
		return modelsService.listModels();
	} catch {
		return { models: [], defaultModel: null };
	}
};
