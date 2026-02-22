<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import MessageActions from '$lib/components/ai-elements/new-message/MessageActions.svelte';
	import MessageAction from '$lib/components/ai-elements/new-message/MessageAction.svelte';
	import Response from '$lib/components/ai-elements/response/Response.svelte';
	import InlineReasoning from './InlineReasoning.svelte';
	import InlineTool from './InlineTool.svelte';
	import Shimmer from '$lib/components/ai-elements/shimmer/Shimmer.svelte';
	import { Copy, PanelRight } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';

	interface Props {
		message: ChatMessage;
		onOpenDetail?: (id: string) => void;
	}

	let { message, onOpenDetail }: Props = $props();

	function handleCopy() {
		navigator.clipboard.writeText(message.content);
	}
</script>

<Message from="assistant">
	{#if message.plan || message.isStreaming}
		<InlineReasoning plan={message.plan} isStreaming={message.isStreaming && !message.content} />
	{/if}

	{#if message.toolCalls && message.toolCalls.length > 0}
		{#each message.toolCalls as tool (tool.toolName + tool.timestamp)}
			<InlineTool {tool} />
		{/each}
	{/if}

	{#if message.content}
		<MessageContent>
			<Response content={message.content} />
		</MessageContent>
	{:else if message.isStreaming}
		<Shimmer>Thinking...</Shimmer>
	{/if}

	{#if message.error}
		<div class="rounded-md bg-destructive/12 p-3 text-sm text-destructive">
			{message.error}
		</div>
	{/if}

	{#if !message.isStreaming && message.content}
		<MessageActions>
			<MessageAction tooltip="Copy" onclick={handleCopy}>
				<Copy class="size-4" />
			</MessageAction>
			<MessageAction tooltip="View details" onclick={() => onOpenDetail?.(message.id)}>
				<PanelRight class="size-4" />
			</MessageAction>
		</MessageActions>
	{/if}
</Message>