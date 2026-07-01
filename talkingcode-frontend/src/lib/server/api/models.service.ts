import type { ApiClient } from './client';
import { mapModel, type ModelOption } from './mappers/models';

function errorMessage(error: unknown): string {
	if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
		return error.detail;
	}

	return 'Request failed';
}

export interface ModelListView {
	models: ModelOption[];
	defaultModel: string | null;
}

export class ModelsService {
	constructor(private readonly client: ApiClient) {}

	async listModels(): Promise<ModelListView> {
		const { data, error } = await this.client.GET('/models');
		if (error) throw new Error(`Failed to list models: ${errorMessage(error)}`);
		if (!data) {
			return {
				models: [],
				defaultModel: null
			};
		}

		return {
			models: data.models.map(mapModel),
			defaultModel: data.default ?? null
		};
	}
}

