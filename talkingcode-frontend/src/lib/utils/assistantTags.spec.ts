import { describe, expect, it } from 'vitest';
import { parseAssistantTags } from './assistantTags';

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
