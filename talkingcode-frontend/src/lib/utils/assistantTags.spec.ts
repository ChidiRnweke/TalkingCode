import { describe, expect, it } from 'vitest';
import { groupAssistantBlocks, parseAssistantTags } from './assistantTags';

describe('parseAssistantTags', () => {
	it('keeps markdown text around custom tags', () => {
		const segments = parseAssistantTags(
			'Before <tc-tool name="search_github" call-id="c1" status="running" args="{&quot;query&quot;:&quot;auth&quot;}"></tc-tool> after'
		);

		expect(segments.map((segment) => segment.kind)).toEqual(['text', 'tool', 'text']);
	});

	it('parses tool args', () => {
		const segments = parseAssistantTags(
			'<tc-tool name="search_github" call-id="c1" status="done" args="{&quot;query&quot;:&quot;auth&quot;}"></tc-tool>'
		);

		expect(segments[0]).toMatchObject({
			kind: 'tool',
			name: 'search_github',
			status: 'done',
			args: { query: 'auth' }
		});
	});

	it('folds tool status updates with the same call-id into one segment', () => {
		const segments = parseAssistantTags(
			'<tc-tool name="search_github" call-id="c1" status="running" args="{&quot;query&quot;:&quot;auth&quot;}"></tc-tool>' +
				'text between' +
				'<tc-tool call-id="c1" status="done"></tc-tool>'
		);

		const tools = segments.filter((segment) => segment.kind === 'tool');
		expect(tools).toHaveLength(1);
		expect(tools[0]).toMatchObject({
			name: 'search_github',
			callId: 'c1',
			status: 'done',
			args: { query: 'auth' }
		});
	});

	it('merges adjacent reasoning delta tags into one segment', () => {
		const segments = parseAssistantTags(
			'<tc-reasoning>Let</tc-reasoning><tc-reasoning> me</tc-reasoning><tc-reasoning> search.</tc-reasoning>'
		);

		expect(segments).toHaveLength(1);
		expect(segments[0]).toMatchObject({ kind: 'reasoning', text: 'Let me search.' });
	});

	it('drops the completed reasoning re-emit that duplicates streamed deltas', () => {
		const segments = parseAssistantTags(
			'<tc-reasoning>Let me</tc-reasoning><tc-reasoning> search.</tc-reasoning>' +
				'Answer text\n\n' +
				'<tc-reasoning>Let me search.</tc-reasoning>'
		);

		const reasoning = segments.filter((segment) => segment.kind === 'reasoning');
		expect(reasoning).toHaveLength(1);
		expect(reasoning[0].text).toBe('Let me search.');
	});

	it('keeps distinct reasoning blocks separated by other content', () => {
		const segments = parseAssistantTags(
			'<tc-reasoning>First thought.</tc-reasoning>' +
				'<tc-tool name="search" call-id="c1" status="running"></tc-tool>' +
				'<tc-reasoning>Second thought.</tc-reasoning>'
		);

		const reasoning = segments.filter((segment) => segment.kind === 'reasoning');
		expect(reasoning.map((segment) => segment.text)).toEqual(['First thought.', 'Second thought.']);
	});

	it('parses reasoning text', () => {
		const segments = parseAssistantTags('<tc-reasoning>checking &lt;repo&gt;</tc-reasoning>');

		expect(segments[0]).toEqual({
			kind: 'reasoning',
			id: 'reasoning-0',
			text: 'checking <repo>'
		});
	});
});

describe('groupAssistantBlocks', () => {
	const reasoning = '<tc-reasoning>I should inspect the repo.</tc-reasoning>';
	const narration = '\n\nLet me explore the backend layout.\n\n';
	const toolRunning =
		'<tc-tool name="search_github" call-id="c1" status="running" args="{&quot;query&quot;:&quot;auth&quot;}"></tc-tool>';
	const toolDone = '<tc-tool call-id="c1" status="done"></tc-tool>';

	it('groups a thought with its tool calls into one step', () => {
		const blocks = groupAssistantBlocks(parseAssistantTags(reasoning + toolRunning + toolDone));

		expect(blocks).toHaveLength(1);
		expect(blocks[0]).toMatchObject({
			kind: 'step',
			reasoning: { text: 'I should inspect the repo.' },
			tools: [{ callId: 'c1', status: 'done' }]
		});
	});

	it('moves a step below the narration text once its tools arrive', () => {
		const blocks = groupAssistantBlocks(parseAssistantTags(reasoning + narration + toolRunning));

		expect(blocks.map((block) => block.kind)).toEqual(['text', 'step']);
		expect(blocks[1]).toMatchObject({
			kind: 'step',
			reasoning: { text: 'I should inspect the repo.' },
			tools: [{ callId: 'c1', status: 'running' }]
		});
	});

	it('keeps a tool-less final thought above the answer text', () => {
		const blocks = groupAssistantBlocks(
			parseAssistantTags(
				reasoning + narration + toolRunning + toolDone + '<tc-reasoning>Time to answer.</tc-reasoning>\n\nThe final answer.'
			)
		);

		expect(blocks.map((block) => block.kind)).toEqual(['text', 'step', 'step', 'text']);
		expect(blocks[2]).toMatchObject({ kind: 'step', reasoning: { text: 'Time to answer.' }, tools: [] });
		expect(blocks[3]).toMatchObject({ kind: 'text', segment: { text: '\n\nThe final answer.' } });
	});

	it('keeps step ids stable while the stream appends', () => {
		const partial = groupAssistantBlocks(parseAssistantTags(reasoning + narration));
		const complete = groupAssistantBlocks(parseAssistantTags(reasoning + narration + toolRunning));

		const partialStep = partial.find((block) => block.kind === 'step');
		const completeStep = complete.find((block) => block.kind === 'step');
		expect(partialStep?.id).toBeDefined();
		expect(completeStep?.id).toBe(partialStep?.id);
	});

	it('creates a step for tools that arrive without a preceding thought', () => {
		const blocks = groupAssistantBlocks(parseAssistantTags(toolRunning));

		expect(blocks).toHaveLength(1);
		expect(blocks[0]).toMatchObject({ kind: 'step', reasoning: null, tools: [{ callId: 'c1' }] });
	});

	it('keeps a step with a running tool as the bottom-most block at every stream prefix', () => {
		// Tags arrive atomically per SSE delta; only plain text is split further.
		const deltas = [
			'<tc-reasoning>First thought.</tc-reasoning>',
			'\n\nLet me ',
			'search the repo.\n\n',
			'<tc-tool name="search_github" call-id="c1" status="running" args="{&quot;query&quot;:&quot;auth&quot;}"></tc-tool>',
			'<tc-tool call-id="c1" status="done"></tc-tool>',
			'<tc-reasoning>Second thought.</tc-reasoning>',
			'\n\nNarrowing ',
			'down.\n\n',
			'<tc-tool name="search_github" call-id="c2" status="running" args="{&quot;query&quot;:&quot;login&quot;}"></tc-tool>',
			'<tc-tool call-id="c2" status="done"></tc-tool>',
			'<tc-reasoning>Time to answer.</tc-reasoning>',
			'\n\nThe final ',
			'answer.'
		];

		let content = '';
		for (const delta of deltas) {
			content += delta;
			const blocks = groupAssistantBlocks(parseAssistantTags(content));
			const runningStep = blocks.find(
				(block) => block.kind === 'step' && block.tools.some((tool) => tool.status === 'running')
			);
			if (runningStep) {
				expect(blocks[blocks.length - 1]).toBe(runningStep);
			}
		}
	});

	it('drops whitespace-only text between steps', () => {
		const blocks = groupAssistantBlocks(
			parseAssistantTags(reasoning + '\n\n' + toolRunning + toolDone)
		);

		expect(blocks).toHaveLength(1);
		expect(blocks[0].kind).toBe('step');
	});
});
