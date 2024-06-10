import { getContext } from 'svelte';
import type { paths } from './schema';
import createClient from 'openapi-fetch';

const client = createClient<paths>({ baseUrl: 'http://localhost:8000' });
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
		let data = {
			response:
				'"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."',
			session_id: 'error'
		};
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
