import type { paths } from './schema';
import createClient from 'openapi-fetch';

const client = createClient<paths>({ baseUrl: '/api/v1' });
export type inputQuery = paths['/']['post']['requestBody']['content']['application/json'];
export type RAGResponse = paths['/']['post']['responses']['200']['content']['application/json'];
export type RemainingSpend =
	paths['/remaining_spend']['get']['responses']['200']['content']['application/json'];

import { writable } from 'svelte/store';
export const remainingSpace = writable(2);
const isProd = import.meta.env.PROD;

export interface PreviousContext {
	question: string;
	answer: string;
}

export interface RAGService {
	getAnswer: (inputQuery: inputQuery) => Promise<RAGResponse>;
	refreshRemainingSpend: () => Promise<void>;
	getCurrentSpend: () => Promise<number>;
}

class APIError extends Error {
	constructor(public response: string) {
		super(response);
	}
}

class MockRagClient implements RAGService {
	getAnswer = async (): Promise<RAGResponse> => {
		if (!isProd) {
			const mockData = await fetch('/mock-response.json').then((res) => res.json());
			return mockData;
		}
		throw new APIError('Mock data is only available in development mode.');
	};

	refreshRemainingSpend = async () => {
		remainingSpace.set(2);
	};

	getCurrentSpend = async (): Promise<number> => {
		return 2;
	};
}
class RAGClient implements RAGService {
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

	refreshRemainingSpend = async () => {
		const remainingSpend = await this.getCurrentSpend();
		remainingSpace.set(remainingSpend);
	};

	getCurrentSpend = async (): Promise<number> => {
		const { data } = await this.client.GET('/remaining_spend');
		if (data) {
			return data.remaining_spend;
		} else {
			throw new APIError('An error ocurred. Please try again later.');
		}
	};
}
export const ragClient: RAGService = isProd ? new RAGClient() : new MockRagClient();
