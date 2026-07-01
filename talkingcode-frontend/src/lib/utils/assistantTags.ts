export interface TextSegment {
	kind: 'text';
	id: string;
	text: string;
}

export interface ToolSegment {
	kind: 'tool';
	id: string;
	name: string;
	callId: string;
	status: 'pending' | 'running' | 'done' | 'error';
	args: Record<string, unknown>;
}

export interface ReasoningSegment {
	kind: 'reasoning';
	id: string;
	text: string;
}

export type AssistantSegment = TextSegment | ToolSegment | ReasoningSegment;

const tagPattern = /<tc-tool\s+([^>]*)><\/tc-tool>|<tc-reasoning>([\s\S]*?)<\/tc-reasoning>/g;

function parseAttrs(raw: string): Record<string, string> {
	const attrs: Record<string, string> = {};
	const attrPattern = /([a-zA-Z-]+)="([^"]*)"/g;
	let match: RegExpExecArray | null;
	while ((match = attrPattern.exec(raw)) !== null) {
		attrs[match[1]] = decodeHtml(match[2]);
	}
	return attrs;
}

function decodeHtml(value: string): string {
	return value
		.replaceAll('&quot;', '"')
		.replaceAll('&#39;', "'")
		.replaceAll('&#x27;', "'")
		.replaceAll('&lt;', '<')
		.replaceAll('&gt;', '>')
		.replaceAll('&amp;', '&');
}

function parseArgs(value: string | undefined): Record<string, unknown> {
	if (!value) return {};
	try {
		const parsed: unknown = JSON.parse(value);
		return typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)
			? (parsed as Record<string, unknown>)
			: {};
	} catch {
		return {};
	}
}

function normalizeStatus(value: string | undefined): ToolSegment['status'] {
	if (value === 'running' || value === 'done' || value === 'error') return value;
	return 'pending';
}

export function parseAssistantTags(content: string): AssistantSegment[] {
	const segments: AssistantSegment[] = [];
	const toolsByCallId = new Map<string, ToolSegment>();
	let lastReasoning: ReasoningSegment | null = null;
	let lastIndex = 0;
	let index = 0;
	let match: RegExpExecArray | null;

	while ((match = tagPattern.exec(content)) !== null) {
		if (match.index > lastIndex) {
			segments.push({
				kind: 'text',
				id: `text-${index++}`,
				text: content.slice(lastIndex, match.index)
			});
		}

		if (match[1] !== undefined) {
			const attrs = parseAttrs(match[1]);
			const callId = attrs['call-id'] || '';
			const existing = callId ? toolsByCallId.get(callId) : undefined;
			// Tool status updates re-send the same call-id; fold them into one segment
			// so the keyed each block never sees duplicate keys.
			if (existing) {
				existing.status = normalizeStatus(attrs.status);
				if (attrs.name) existing.name = attrs.name;
				const args = parseArgs(attrs.args);
				if (Object.keys(args).length > 0) existing.args = args;
			} else {
				const tool: ToolSegment = {
					kind: 'tool',
					id: callId || `tool-${index}`,
					name: attrs.name || 'tool',
					callId,
					status: normalizeStatus(attrs.status),
					args: parseArgs(attrs.args)
				};
				segments.push(tool);
				if (callId) toolsByCallId.set(callId, tool);
				index += 1;
			}
		} else {
			const text = decodeHtml(match[2] ?? '');
			const previous = segments[segments.length - 1];
			if (previous?.kind === 'reasoning' && match.index === lastIndex) {
				// Streaming sends each reasoning delta as its own tag; adjacent tags
				// belong to the same reasoning block. A tag matching the accumulated
				// text is the completed item being re-sent, not a delta.
				if (text !== previous.text) {
					previous.text += text;
				}
			} else if (lastReasoning && lastReasoning.text === text) {
				// The full reasoning text can be re-sent once the item completes;
				// drop the duplicate.
			} else {
				const reasoning: ReasoningSegment = {
					kind: 'reasoning',
					id: `reasoning-${index++}`,
					text
				};
				segments.push(reasoning);
				lastReasoning = reasoning;
			}
		}

		lastIndex = tagPattern.lastIndex;
	}

	if (lastIndex < content.length) {
		segments.push({
			kind: 'text',
			id: `text-${index}`,
			text: content.slice(lastIndex)
		});
	}

	return segments;
}
