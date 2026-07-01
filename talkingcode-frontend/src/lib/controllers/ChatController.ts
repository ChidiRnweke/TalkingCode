/** Chat controller */
import type { AgenticAskInput, AgentStreamEvent } from '$lib/models';
import type { IChatService } from '$lib/services/IChatService';

export class ChatController {
	constructor(private readonly chatService: IChatService) {}

	async *startAgenticTurn(
		input: AgenticAskInput,
		signal?: AbortSignal
	): AsyncGenerator<AgentStreamEvent> {
		yield* this.chatService.askAgentic(input, signal);
	}
}
