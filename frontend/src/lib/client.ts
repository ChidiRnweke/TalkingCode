import type { paths } from './schema';
import createClient from 'openapi-fetch';

const baseUrl = import.meta.env.VITE_API_URL;
const client = createClient<paths>({ baseUrl: '/api/v1' });
export type inputQuery = paths['/']['post']['requestBody']['content']['application/json'];
export type RAGResponse = paths['/']['post']['responses']['200']['content']['application/json'];
export interface PreviousContext {
	question: string;
	answer: string;
}

class APIError extends Error {
	constructor(public response: string) {
		super(response);
	}
}

class RAGClient {
	private client = client;

	getAnswer = async (inputQuery: inputQuery): Promise<RAGResponse> => {
		const { data } = await this.client.POST('/', { body: inputQuery });
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

export const OQuestionState = {
	Fetching: 1,
	Fetched: 2
} as const;

export type QuestionState = (typeof OQuestionState)[keyof typeof OQuestionState];
