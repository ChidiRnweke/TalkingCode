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
			<div class="mx-auto max-w-4xl w-full px-5 md:px-8 lg:px-10 flex flex-col gap-10 py-20 pb-40">
				{#each messages as message (message.id)}
					{#if message.role === 'user'}
						<UserMessage {message} />
					{:else}
						<AssistantMessage {message} {onOpenDetail} onRetry={onSuggestionClick} />
					{/if}
				{/each}
			</div>
		{/if}
	</ConversationContent>
	<ConversationScrollButton />
</Conversation>
