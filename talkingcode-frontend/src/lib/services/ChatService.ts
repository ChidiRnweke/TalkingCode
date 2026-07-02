/** Chat service implementation with strict SSE parsing */
import { z } from 'zod';
import type { AgenticAskInput, AgentStreamEvent } from '$lib/models';
import type { IChatService } from './IChatService';

const markdownDeltaSchema = z
	.object({
		text: z.string(),
		timestamp: z.string().min(1)
	})
	.strict();

const assistantDoneSchema = z
	.object({
		turn_id: z.string().min(1),
		conversation_id: z.string().min(1),
		timestamp: z.string().min(1),
		sources: z
			.array(
				z.object({
					index: z.number().int().positive(),
					repository: z.string().min(1),
					path: z.string().min(1),
					start_line: z.number().int().nullable().optional(),
					end_line: z.number().int().nullable().optional(),
					similarity_score: z.number().optional()
				})
			)
			.optional()
	})
	.strict();

const agentErrorSchema = z
	.object({
		turn_id: z.string().min(1),
		message: z.string(),
		code: z.string().optional(),
		timestamp: z.string().min(1)
	})
	.strict();

export function parseAgentEvent(eventType: string, data: string): AgentStreamEvent | null {
	let parsed: unknown;
	try {
		parsed = JSON.parse(data);
	} catch {
		return null;
	}

	switch (eventType) {
		case 'markdown.delta': {
			const result = markdownDeltaSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'markdown.delta',
				text: result.data.text,
				timestamp: result.data.timestamp
			};
		}
		case 'turn.done': {
			const result = assistantDoneSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'turn.done',
				turnId: result.data.turn_id,
				conversationId: result.data.conversation_id,
				sources: (result.data.sources ?? []).map((source) => ({
					index: source.index,
					repository: source.repository,
					path: source.path,
					startLine: source.start_line ?? null,
					endLine: source.end_line ?? null,
					similarityScore: source.similarity_score ?? 0
				})),
				timestamp: result.data.timestamp
			};
		}
		case 'turn.error': {
			const result = agentErrorSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'turn.error',
				turnId: result.data.turn_id,
				message: result.data.message,
				code: result.data.code ?? null,
				timestamp: result.data.timestamp
			};
		}
		default:
			return null;
	}
}

export class ChatService implements IChatService {
	private currentEventType = '';

	async *askAgentic(input: AgenticAskInput, signal?: AbortSignal): AsyncGenerator<AgentStreamEvent> {
		const response = await fetch(`api/chat/agentic`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			signal,
			body: JSON.stringify({
				conversation_id: input.conversationId,
				question: input.question,
				selected_model: input.model,
				retry_user_ordinal: input.retryUserOrdinal ?? null
			})
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const reader = response.body?.getReader();
		if (!reader) {
			throw new Error('No response body');
		}

		const decoder = new TextDecoder();
		let buffer = '';

		try {
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					const event = this.parseSSELine(line);
					if (event) {
						yield event;
					}
				}
			}
		} finally {
			reader.releaseLock();
		}
	}

	private parseSSELine(line: string): AgentStreamEvent | null {
		if (!line.trim()) return null;

		if (line.startsWith('event:')) {
			this.currentEventType = line.slice(6).trim();
			return null;
		}

		if (line.startsWith('data:')) {
			return parseAgentEvent(this.currentEventType, line.slice(5).trim());
		}

		return null;
	}
}

export const chatService = new ChatService();
