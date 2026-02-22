<script lang="ts">
	import {
		Conversation,
		ConversationContent,
		ConversationEmptyState,
		ConversationScrollButton
	} from '$lib/components/ai-elements/conversation';
	import UserMessage from './UserMessage.svelte';
	import AssistantMessage from './AssistantMessage.svelte';
	import type { ChatMessage } from '$lib/models';
	import { EmptyState } from '$lib/components/layout';

	interface Props {
		messages: ChatMessage[];
		onOpenDetail?: (id: string) => void;
		onSuggestionClick?: (suggestion: string) => void;
	}

	let { messages, onOpenDetail, onSuggestionClick }: Props = $props();
</script>

<Conversation>
	<ConversationContent>
		{#if messages.length === 0}
			<ConversationEmptyState>
				<EmptyState
					title="Chat with Chidi's code"
					description="Ask questions about architecture, modules, ownership, or behavior across all indexed repositories."
					suggestions={[
						'What projects has Chidi built in Python?',
						'Walk me through the architecture of this repo',
						'What testing patterns are used across the codebase?',
						'Show me the most complex modules and explain them'
					]}
					onSuggestionClick={onSuggestionClick}
				/>
			</ConversationEmptyState>
		{:else}
			<div class="flex flex-col gap-4 px-4 py-6">
				{#each messages as message (message.id)}
					{#if message.role === 'user'}
						<UserMessage {message} />
					{:else}
						<AssistantMessage {message} {onOpenDetail} />
					{/if}
				{/each}
			</div>
		{/if}
	</ConversationContent>
	<ConversationScrollButton />
</Conversation>
