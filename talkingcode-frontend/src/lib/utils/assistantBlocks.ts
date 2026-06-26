/**
 * Groups an assistant message's ordered `parts` into render blocks for the
 * ReAct view: collapsible "chain-of-thought" steps interleaved with answer prose.
 *
 * A step = one loop iteration that called tools (or reasoned). The trailing
 * iteration with no tools is the final answer and becomes a text block.
 */
import type {
	AssistantPart,
	AssistantReasoningPart,
	AssistantTextPart,
	AssistantToolPart,
	ChatMessage,
	ToolCallTimelineItem
} from '$lib/models';

export interface StepBlock {
	kind: 'step';
	id: string;
	summary: string;
	status: 'running' | 'done' | 'error';
	durationLabel?: string;
	reasoning?: string;
	tools: ToolCallTimelineItem[];
}

export interface TextBlock {
	kind: 'text';
	id: string;
	text: string;
}

export type AssistantBlock = StepBlock | TextBlock;

function prettyToolName(name: string): string {
	return name
		.split('_')
		.filter(Boolean)
		.map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
		.join(' ');
}

function deriveFromTools(tools: ToolCallTimelineItem[]): string {
	const labels: string[] = [];
	for (const tool of tools) {
		const query = typeof tool.visibleArgs?.query === 'string' ? tool.visibleArgs.query.trim() : '';
		if (tool.toolName === 'search_github') {
			labels.push(query ? `Searching for “${query}”` : 'Searching the repositories');
		} else if (tool.toolName === 'read_file') {
			const path = typeof tool.visibleArgs?.file_path === 'string' ? tool.visibleArgs.file_path : '';
			labels.push(path ? `Reading ${path}` : 'Reading a file');
		} else {
			labels.push(prettyToolName(tool.toolName));
		}
	}
	const unique = [...new Set(labels)];
	return unique.join('; ') || 'Gathering evidence';
}

function totalDurationLabel(tools: ToolCallTimelineItem[]): string | undefined {
	if (!tools.length || tools.some((t) => t.status === 'started')) return undefined;
	const ms = tools.reduce((sum, t) => sum + (t.durationMs ?? 0), 0);
	if (ms <= 0) return undefined;
	const seconds = ms / 1000;
	return `${seconds.toFixed(seconds < 10 ? 1 : 0)}s`;
}

export function buildAssistantBlocks(message: ChatMessage): AssistantBlock[] {
	const parts = message.parts ?? [];
	const order: number[] = [];
	const groups = new Map<number, AssistantPart[]>();

	for (const part of parts) {
		const iteration = part.iteration ?? 0;
		if (!groups.has(iteration)) {
			groups.set(iteration, []);
			order.push(iteration);
		}
		groups.get(iteration)!.push(part);
	}

	const streaming = !!message.isStreaming;
	const blocks: AssistantBlock[] = [];

	order.forEach((iteration, groupIndex) => {
		const group = groups.get(iteration)!;
		const isLastGroup = groupIndex === order.length - 1;

		const tools = group
			.filter((p): p is AssistantToolPart => p.kind === 'tool')
			.map((p) => p.tool);
		const reasoning = group
			.filter((p): p is AssistantReasoningPart => p.kind === 'reasoning')
			.map((p) => p.text)
			.join('');
		const text = group
			.filter((p): p is AssistantTextPart => p.kind === 'text')
			.map((p) => p.text)
			.join('');

		const summary = message.stepSummaries?.[iteration];
		const hasStep = tools.length > 0 || reasoning.trim().length > 0;

		// 1. The "thinking / acting" step: reasoning + tool calls, behind a header.
		if (hasStep) {
			const anyToolRunning = tools.some((t) => t.status === 'started');
			const status: StepBlock['status'] =
				anyToolRunning || (streaming && isLastGroup && !text.trim()) ? 'running' : 'done';
			blocks.push({
				kind: 'step',
				id: tools.length > 0 ? `step-${iteration}` : `think-${iteration}`,
				summary: tools.length > 0 ? (summary ?? deriveFromTools(tools)) : (summary ?? 'Thinking'),
				status,
				durationLabel: totalDurationLabel(tools),
				reasoning: reasoning.trim() || undefined,
				tools
			});
		}

		// 2. The model's prose is the real, progressive answer — always its own
		//    block (never folded into a step header), so it doesn't flash.
		if (text.trim()) {
			blocks.push({ kind: 'text', id: `text-${iteration}`, text });
		}
	});

	return blocks;
}
