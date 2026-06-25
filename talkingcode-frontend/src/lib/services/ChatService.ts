/** Chat service implementation with strict SSE parsing */
import { env } from '$env/dynamic/public';
import { z } from 'zod';
import type { AgenticAskInput, AgentStreamEvent, ToolCallTimelineItem } from '$lib/models';
import type { IChatService } from './IChatService';

const baseSchema = z
	.object({
		turn_id: z.string().min(1),
		timestamp: z.string().min(1)
	})
	.strict();

const turnStartedSchema = baseSchema
	.extend({
		message: z.string().optional(),
		visible_args: z.object({ model: z.string().optional() }).optional()
	})
	.strict();

const messageDeltaSchema = baseSchema
	.extend({
		message: z.string(),
		iteration: z.number().int().positive().optional()
	})
	.strict();

const toolCallStartedSchema = baseSchema
	.extend({
		message: z.string().optional(),
		iteration: z.number().int().positive().optional(),
		index: z.number().int().nonnegative().optional(),
		call_id: z.string().min(1).optional(),
		tool_name: z.string().min(1),
		visible_args: z.record(z.string(), z.unknown()).optional()
	})
	.strict();

const toolCallDeltaSchema = baseSchema
	.extend({
		message: z.string().optional(),
		iteration: z.number().int().positive().optional(),
		index: z.number().int().nonnegative().optional(),
		call_id: z.string().min(1).optional(),
		tool_name: z.string().min(1).optional(),
		visible_args: z.object({ phase: z.string().optional() }).optional()
	})
	.strict();

const toolCallFinishedSchema = baseSchema
	.extend({
		message: z.string().optional(),
		iteration: z.number().int().positive().optional(),
		index: z.number().int().nonnegative().optional(),
		call_id: z.string().min(1).optional(),
		tool_name: z.string().min(1),
		visible_args: z.object({
			success: z.boolean(),
			duration_ms: z.number().int().nonnegative(),
			error_code: z.string().nullish()
		}),
		code: z.string().optional()
	})
	.strict();

const toolResultAvailableSchema = baseSchema
	.extend({
		message: z.string().optional(),
		iteration: z.number().int().positive().optional(),
		index: z.number().int().nonnegative().optional(),
		call_id: z.string().min(1).optional(),
		tool_name: z.string().min(1),
		visible_args: z.object({
			success: z.boolean(),
			error_code: z.string().nullish()
		})
	})
	.strict();

const assistantDoneSchema = baseSchema
	.extend({
		message: z.string().optional(),
		visible_args: z
			.object({
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
			.optional()
	})
	.strict();
const agentErrorSchema = baseSchema
	.extend({
		message: z.string(),
		code: z.string().optional(),
		visible_args: z.object({ code: z.string().optional() }).strict().optional()
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
		case 'turn.started': {
			const result = turnStartedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'turn.started',
				turnId: result.data.turn_id,
				model: result.data.visible_args?.model,
				timestamp: result.data.timestamp
			};
		}
		case 'message.delta': {
			const result = messageDeltaSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'message.delta',
				turnId: result.data.turn_id,
				iteration: result.data.iteration,
				token: result.data.message,
				timestamp: result.data.timestamp
			};
		}
		case 'tool_call.started': {
			const result = toolCallStartedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'tool_call.started',
				turnId: result.data.turn_id,
				toolName: result.data.tool_name,
				callId: result.data.call_id,
				iteration: result.data.iteration,
				index: result.data.index,
				visibleArgs: result.data.visible_args ?? {},
				timestamp: result.data.timestamp
			};
		}
		case 'tool_call.delta': {
			const result = toolCallDeltaSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'tool_call.delta',
				turnId: result.data.turn_id,
				toolName: result.data.tool_name,
				callId: result.data.call_id,
				iteration: result.data.iteration,
				index: result.data.index,
				phase: result.data.visible_args?.phase,
				timestamp: result.data.timestamp
			};
		}
		case 'tool_call.completed': {
			const result = toolCallFinishedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'tool_call.completed',
				turnId: result.data.turn_id,
				toolName: result.data.tool_name,
				callId: result.data.call_id,
				iteration: result.data.iteration,
				index: result.data.index,
				success: result.data.visible_args.success,
				durationMs: result.data.visible_args.duration_ms,
				errorCode: result.data.visible_args.error_code ?? result.data.code ?? undefined,
				timestamp: result.data.timestamp
			};
		}
		case 'tool_result.available': {
			const result = toolResultAvailableSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'tool_result.available',
				turnId: result.data.turn_id,
				toolName: result.data.tool_name,
				callId: result.data.call_id,
				iteration: result.data.iteration,
				index: result.data.index,
				success: result.data.visible_args.success,
				errorCode: result.data.visible_args.error_code ?? undefined,
				timestamp: result.data.timestamp
			};
		}
		case 'turn.done': {
			const result = assistantDoneSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'turn.done',
				turnId: result.data.turn_id,
				sources: (result.data.visible_args?.sources ?? []).map((source) => ({
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
				code: result.data.code || result.data.visible_args?.code || null,
				timestamp: result.data.timestamp
			};
		}
		default:
			return null;
	}
}

export class ChatService implements IChatService {
	private backendUrl: string;
	private currentEventType = '';

	constructor() {
		this.backendUrl = env.PUBLIC_BACKEND_URL || 'http://localhost:8000';
	}

	async *askAgentic(input: AgenticAskInput, signal?: AbortSignal): AsyncGenerator<AgentStreamEvent> {
		const response = await fetch(`api/chat/agentic`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			signal,
			body: JSON.stringify({
				conversation_id: input.conversationId,
				question: input.question,
				selected_model: input.model
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

	async getToolTimeline(conversationId: string): Promise<ToolCallTimelineItem[]> {
		const response = await fetch(
			`${this.backendUrl}/chat/timeline?conversation_id=${conversationId}`
		);

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();
		return data.timeline || [];
	}
}

export const chatService = new ChatService();
