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

	interface Props {
		messages: ChatMessage[];
		onOpenDetail?: (id: string) => void;
	}

	let { messages, onOpenDetail }: Props = $props();
</script>

<Conversation>
	<ConversationContent>
		{#if messages.length === 0}
			<ConversationEmptyState
				title="Ask your first question"
				description="Research your codebase — ask about architecture, ownership, or behaviour."
			/>
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