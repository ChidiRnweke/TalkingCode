<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import Response from '$lib/components/ai-elements/response/Response.svelte';
	import { Reasoning, ReasoningTrigger } from '$lib/components/ai-elements/reasoning';
	import { Actions, Action } from '$lib/components/ai-elements/action';
	import { Copy, PanelRight, RotateCcw } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';
	import { chatStore } from '$lib/stores';

	interface Props {
		message: ChatMessage;
		onOpenDetail?: (id: string) => void;
		onRetry?: (question: string) => void;
	}

	let { message, onOpenDetail, onRetry }: Props = $props();

	function handleCopy() {
		navigator.clipboard.writeText(message.content);
	}

	function handleRetry() {
		const question = chatStore.retry(message.id);
		if (question && onRetry) {
			onRetry(question);
		}
	}

	let isThinking = $derived(message.isStreaming && !message.content);
	let hasThought = $derived(!!(message.plan || (message.toolCalls && message.toolCalls.length > 0)));
</script>

<Message from="assistant" class="max-w-none text-base">
	{#if isThinking || hasThought}
		<Reasoning 
			isStreaming={isThinking} 
			duration={message.thoughtDurationS}
			class="mb-2"
		>
			<ReasoningTrigger onclick={() => onOpenDetail?.(message.id)} />
		</Reasoning>
	{/if}

	{#if message.content}
		<MessageContent>
			<Response content={message.content} />
		</MessageContent>
	{/if}

	{#if message.error}
		<div class="rounded-md bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
			<p class="font-bold mb-1">Error</p>
			{message.error}
		</div>
	{/if}

	{#if !message.isStreaming}
		<Actions class="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
			{#if message.content}
				<Action tooltip="Copy message" onclick={handleCopy}>
					<Copy class="size-4" />
				</Action>
			{/if}
			
			<Action tooltip="Retry" onclick={handleRetry}>
				<RotateCcw class="size-4" />
			</Action>

			<Action tooltip="View detailed timeline" onclick={() => onOpenDetail?.(message.id)}>
				<PanelRight class="size-4" />
			</Action>
		</Actions>
	{/if}
</Message>
