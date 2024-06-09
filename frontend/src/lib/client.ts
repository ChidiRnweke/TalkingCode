import type { paths } from './schema';
import createClient from 'openapi-fetch';

const client = createClient<paths>({ baseUrl: 'http://localhost:8000' });
export type inputQuery = paths['/']['post']['requestBody']['content']['application/json'];
export type RAGResponse = paths['/']['post']['responses']['200']['content']['application/json'];

class APIError extends Error {
	constructor(public response: string) {
		super(response);
	}
}

class RAGClient {
	private client = client;

	getAnswer = async (inputQuery: inputQuery): Promise<RAGResponse> => {
		let { data } = await this.client.POST('/', { body: inputQuery });
		if (data) {
			return data;
		} else {
			throw new APIError(
				'An error ocurred. Please try again later. If this persists it may be that a critical service (e.g. the chatGPT server) is down.'
			);
		}
	};
}

export let ragClient = new RAGClient();
