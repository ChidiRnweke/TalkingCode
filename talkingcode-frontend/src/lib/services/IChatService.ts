/** Chat service interface */
import type { AgenticAskInput, AgentStreamEvent } from '$lib/models';

export interface IChatService {
	askAgentic(input: AgenticAskInput, signal?: AbortSignal): AsyncIterable<AgentStreamEvent>;
}
