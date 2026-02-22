<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import MessageResponse from '$lib/components/ai-elements/new-message/MessageResponse.svelte';
	import MessageToolbar from '$lib/components/ai-elements/new-message/MessageToolbar.svelte';
	import MessageActions from '$lib/components/ai-elements/new-message/MessageActions.svelte';
	import MessageAction from '$lib/components/ai-elements/new-message/MessageAction.svelte';
	import { Reasoning, ReasoningTrigger } from '$lib/components/ai-elements/reasoning';
	import ReasoningContent from '$lib/components/ai-elements/reasoning/ReasoningContent.svelte';
	import InlineTool from './InlineTool.svelte';
	import { Copy, RotateCcw } from 'lucide-svelte';
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
	let hasContent = $derived(!!message.planText || (message.toolCalls && message.toolCalls.length > 0));
	let hasThought = $derived(
		!!(message.plan || message.planText || (message.toolCalls && message.toolCalls.length > 0))
	);

	// Auto-open when content arrives, stay closed until then
	let reasoningOpen = $state(false);
	$effect(() => {
		if (hasContent && !reasoningOpen) {
			reasoningOpen = true;
		}
	});
</script>

<Message from="assistant" class="max-w-none text-base">
	{#if isThinking || hasThought}
		<Reasoning
			isStreaming={isThinking}
			bind:open={reasoningOpen}
			defaultOpen={false}
			duration={message.thoughtDurationS}
			class="mb-2"
		>
			<ReasoningTrigger class="cursor-pointer" />
			<ReasoningContent>
				{#if message.planText}
					<p class="text-sm text-muted-foreground whitespace-pre-wrap">{message.planText}</p>
				{/if}
				{#if message.toolCalls && message.toolCalls.length > 0}
					<div class="mt-2 space-y-2">
						{#each message.toolCalls as tool (tool.callId ?? tool.toolName + tool.timestamp)}
							<InlineTool {tool} />
						{/each}
					</div>
				{/if}
			</ReasoningContent>
		</Reasoning>
	{/if}

	{#if message.content}
		<MessageContent>
			<MessageResponse content={message.content} />
		</MessageContent>
	{/if}

	{#if message.error}
		<div class="rounded-md bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
			<p class="font-bold mb-1">Error</p>
			{message.error}
		</div>
	{/if}

	{#if !message.isStreaming}
		<MessageToolbar class="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
			<MessageActions>
				{#if message.content}
					<MessageAction tooltip="Copy message" onclick={handleCopy}>
						<Copy class="size-4" />
					</MessageAction>
				{/if}

				<MessageAction tooltip="Retry" onclick={handleRetry}>
					<RotateCcw class="size-4" />
				</MessageAction>
			</MessageActions>
		</MessageToolbar>
	{/if}
</Message>
