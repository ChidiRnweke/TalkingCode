/** Chat service interface */
import type { AgenticAskInput, AgentStreamEvent, ToolCallTimelineItem } from '$lib/models';

export interface IChatService {
	askAgentic(input: AgenticAskInput, signal?: AbortSignal): AsyncIterable<AgentStreamEvent>;
	getToolTimeline(conversationId: string): Promise<ToolCallTimelineItem[]>;
}
