import { describe, it, expect } from 'vitest';
import { buildAssistantBlocks, type StepBlock, type TextBlock } from './assistantBlocks';
import type {
	AssistantPart,
	ChatMessage,
	ToolCallStatus,
	ToolCallTimelineItem
} from '$lib/models';

function tool(
	toolName: string,
	status: ToolCallStatus,
	extra: Partial<ToolCallTimelineItem> = {}
): ToolCallTimelineItem {
	return {
		turnId: 't',
		toolName,
		visibleArgs: {},
		status,
		timestamp: '2026-01-01T00:00:00Z',
		...extra
	};
}

function toolPart(iteration: number, item: ToolCallTimelineItem): AssistantPart {
	return { id: `tool-${iteration}`, kind: 'tool', tool: item, iteration, timestamp: 't' };
}

function textPart(iteration: number, text: string): AssistantPart {
	return { id: `t-${iteration}`, kind: 'text', text, iteration, timestamp: 't' };
}

function reasoningPart(iteration: number, text: string): AssistantPart {
	return { id: `r-${iteration}`, kind: 'reasoning', text, iteration, timestamp: 't' };
}

function message(parts: AssistantPart[], extra: Partial<ChatMessage> = {}): ChatMessage {
	return {
		id: 'm',
		role: 'assistant',
		content: '',
		timestamp: 't',
		parts,
		...extra
	};
}

describe('buildAssistantBlocks', () => {
	it('renders tool iterations as steps followed by the final answer prose', () => {
		const blocks = buildAssistantBlocks(
			message(
				[
					toolPart(1, tool('search_github', 'finished', { durationMs: 1200 })),
					toolPart(2, tool('read_file', 'finished', { durationMs: 100 })),
					textPart(3, 'The final answer.')
				],
				{ stepSummaries: { 1: 'Searching for X', 2: 'Reading the file' }, isStreaming: false }
			)
		);

		expect(blocks.map((b) => b.kind)).toEqual(['step', 'step', 'text']);
		expect((blocks[0] as StepBlock).summary).toBe('Searching for X');
		expect((blocks[0] as StepBlock).status).toBe('done');
		expect((blocks[0] as StepBlock).durationLabel).toBe('1.2s');
		expect((blocks[2] as TextBlock).text).toBe('The final answer.');
	});

	it('folds a tool iteration narration line into the step header, not into prose', () => {
		const blocks = buildAssistantBlocks(
			message([textPart(1, 'Let me look.'), toolPart(1, tool('search_github', 'finished'))], {
				stepSummaries: { 1: 'Searching the repo' },
				isStreaming: false
			})
		);

		expect(blocks).toHaveLength(1);
		expect(blocks[0].kind).toBe('step');
		expect((blocks[0] as StepBlock).summary).toBe('Searching the repo');
	});

	it('splits final-iteration reasoning into a thinking step before the answer', () => {
		const blocks = buildAssistantBlocks(
			message(
				[
					toolPart(1, tool('search_github', 'finished')),
					reasoningPart(2, 'Weighing the evidence...'),
					textPart(2, 'Grounded answer.')
				],
				{ stepSummaries: { 1: 'Search' }, isStreaming: false }
			)
		);

		expect(blocks.map((b) => b.kind)).toEqual(['step', 'step', 'text']);
		expect((blocks[1] as StepBlock).reasoning).toContain('Weighing the evidence');
		expect((blocks[1] as StepBlock).summary).toBe('Thinking');
		expect((blocks[2] as TextBlock).text).toBe('Grounded answer.');
	});

	it('marks the active tool step as running while streaming', () => {
		const blocks = buildAssistantBlocks(
			message([toolPart(1, tool('search_github', 'started'))], { isStreaming: true })
		);

		expect((blocks[0] as StepBlock).status).toBe('running');
		expect((blocks[0] as StepBlock).durationLabel).toBeUndefined();
	});

	it('derives a summary from tools when none was provided', () => {
		const blocks = buildAssistantBlocks(
			message([toolPart(1, tool('search_github', 'finished', { visibleArgs: { query: 'pgvector' } }))], {
				isStreaming: false
			})
		);

		expect((blocks[0] as StepBlock).summary).toContain('pgvector');
	});
});
