import type { paths } from './schema';
import createClient from 'openapi-fetch';
import markdownit from 'markdown-it';

const baseUrl = '/api/v1';
const client = createClient<paths>({ baseUrl });
export type InputQuery = paths['/rag/chat']['post']['requestBody']['content']['application/json'];
export type RAGResponse =
	paths['/rag/chat']['post']['responses']['200']['content']['application/json'];
export type RemainingSpend =
	paths['/rag/remaining_spend']['get']['responses']['200']['content']['application/json'];

const isProd = import.meta.env.PROD;
const md = markdownit({ html: true, breaks: true });

export interface PreviousContext {
	question: string;
	answer: string;
}

const htmlRender = (input: string) => md.renderInline(input);

export interface RAGService {
	getAnswer: (inputQuery: InputQuery) => AsyncGenerator<string, void, unknown>;
	getRemainingSpend: () => Promise<number>;
}

class APIError extends Error {
	constructor(public response: string) {
		super(response);
	}
}

class MockRagClient implements RAGService {
	async *getAnswer(): AsyncGenerator<string, void, unknown> {
		if (!isProd) {
			const mockData = await fetch('/mock-response.json').then((res) => res.json());
			let answer = '';
			for (const chunk of mockData.response) {
				answer += chunk;
				yield htmlRender(answer);
				await new Promise((resolve) => setTimeout(resolve, 1)); // Simulate delay
			}
		} else {
			throw new APIError('Mock data is only available in development mode.');
		}
	}

	getRemainingSpend = async (): Promise<number> => {
		return Promise.resolve(2);
	};
}
class RAGClient implements RAGService {
	private client = client;

	async *getAnswer(inputQuery: InputQuery): AsyncGenerator<string, void, unknown> {
		let renderingBuffer = '';
		const bufferSize = 15;
		let bufferLength = 0;
		let currentAnswer = '';
		const responseStream = await fetch(`${baseUrl}/rag/chat`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(inputQuery)
		});

		const body = responseStream.body;
		if (!body) {
			throw new APIError(
				'An error occurred. Please try again later. If this persists it may be that a critical service (e.g. the chatGPT server) is down.'
			);
		}
		const reader = body.getReader();
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			const text = new TextDecoder().decode(value);

			renderingBuffer += text;
			bufferLength += text.length;
			if (bufferLength >= bufferSize) {
				currentAnswer += renderingBuffer;
				yield htmlRender(currentAnswer);
				renderingBuffer = '';
				bufferLength = 0;
			}
		}
		if (bufferLength > 0) {
			currentAnswer += renderingBuffer;
			yield htmlRender(currentAnswer);
		}
	}

	getRemainingSpend = async (): Promise<number> => {
		const { data } = await this.client.GET('/rag/remaining_spend');
		if (data) {
			return data.remaining_spend;
		} else {
			throw new APIError('An error ocurred. Please try again later.');
		}
	};
}
export const ragClient: RAGService = isProd ? new RAGClient() : new MockRagClient();
