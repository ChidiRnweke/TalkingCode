/** Chat service interface */
import type { AgenticAskInput, AgentStreamEvent, ToolCallTimelineItem } from '$lib/models';

export interface IChatService {
	askAgentic(input: AgenticAskInput): AsyncIterable<AgentStreamEvent>;
	getToolTimeline(conversationId: string): Promise<ToolCallTimelineItem[]>;
}
