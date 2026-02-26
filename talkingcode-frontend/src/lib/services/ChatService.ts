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

const iterationStartedSchema = baseSchema
	.extend({
		iteration: z.number().int().positive(),
		message: z.string().optional(),
		visible_args: z.record(z.string(), z.unknown()).optional()
	})
	.strict();

const planChunkSchema = baseSchema
	.extend({
		iteration: z.number().int().positive(),
		message: z.string(),
		visible_args: z.object({ chunk: z.string() })
	})
	.strict();

const planDoneSchema = baseSchema
	.extend({
		iteration: z.number().int().positive(),
		message: z.string(),
		visible_args: z.object({ plan_text: z.string() })
	})
	.strict();

const answerPhaseStartedSchema = baseSchema
	.extend({
		iteration: z.number().int().positive().optional(),
		message: z.string().optional()
	})
	.strict();

const toolCallStartedSchema = baseSchema
	.extend({
		message: z.string().optional(),
		iteration: z.number().int().positive().optional(),
		call_id: z.string().min(1).optional(),
		tool_name: z.string().min(1),
		visible_args: z.record(z.string(), z.unknown()).optional()
	})
	.strict();

const toolCallFinishedSchema = baseSchema
	.extend({
		message: z.string().optional(),
		iteration: z.number().int().positive().optional(),
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

const assistantTokenSchema = baseSchema.extend({ message: z.string() }).strict();
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
		case 'iteration_started': {
			const result = iterationStartedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'iteration_started',
				turnId: result.data.turn_id,
				iteration: result.data.iteration,
				timestamp: result.data.timestamp
			};
		}
		case 'plan_chunk': {
			const result = planChunkSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'plan_chunk',
				turnId: result.data.turn_id,
				iteration: result.data.iteration,
				chunk: result.data.visible_args.chunk,
				timestamp: result.data.timestamp
			};
		}
		case 'plan_done': {
			const result = planDoneSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'plan_done',
				turnId: result.data.turn_id,
				iteration: result.data.iteration,
				planText: result.data.visible_args.plan_text,
				timestamp: result.data.timestamp
			};
		}
		case 'tool_call_started': {
			const result = toolCallStartedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'tool_call_started',
				turnId: result.data.turn_id,
				toolName: result.data.tool_name,
				callId: result.data.call_id,
				iteration: result.data.iteration,
				visibleArgs: result.data.visible_args ?? {},
				timestamp: result.data.timestamp
			};
		}
		case 'tool_call_finished': {
			const result = toolCallFinishedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'tool_call_finished',
				turnId: result.data.turn_id,
				toolName: result.data.tool_name,
				callId: result.data.call_id,
				iteration: result.data.iteration,
				success: result.data.visible_args.success,
				durationMs: result.data.visible_args.duration_ms,
				errorCode: result.data.visible_args.error_code ?? result.data.code ?? undefined,
				timestamp: result.data.timestamp
			};
		}
		case 'assistant_token': {
			const result = assistantTokenSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'assistant_token',
				turnId: result.data.turn_id,
				token: result.data.message,
				timestamp: result.data.timestamp
			};
		}
		case 'answer_phase_started': {
			const result = answerPhaseStartedSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'answer_phase_started',
				turnId: result.data.turn_id,
				iteration: result.data.iteration,
				timestamp: result.data.timestamp
			};
		}

		case 'assistant_done': {
			const result = assistantDoneSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'assistant_done',
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
		case 'agent_error': {
			const result = agentErrorSchema.safeParse(parsed);
			if (!result.success) return null;
			return {
				kind: 'agent_error',
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
