<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import MessageResponse from '$lib/components/ai-elements/new-message/MessageResponse.svelte';
	import MessageToolbar from '$lib/components/ai-elements/new-message/MessageToolbar.svelte';
	import MessageActions from '$lib/components/ai-elements/new-message/MessageActions.svelte';
	import MessageAction from '$lib/components/ai-elements/new-message/MessageAction.svelte';
	import InlineTool from './InlineTool.svelte';
	import { Copy, RotateCcw } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';
	import { chatStore } from '$lib/stores';
	import * as Avatar from '$lib/components/ui/avatar';
	import portrait from '$lib/assets/portrait.png';

	interface Props {
		message: ChatMessage;
		onRetry?: (question: string) => void;
	}

	let { message, onRetry }: Props = $props();

	function handleCopy() {
		navigator.clipboard.writeText(message.content);
	}

	function handleRetry() {
		const question = chatStore.retry(message.id);
		if (question && onRetry) {
			onRetry(question);
		}
	}

	let visibleParts = $derived(message.parts ?? []);
	let fallbackToolCalls = $derived(message.toolCalls ?? []);
	let hasInlineParts = $derived(visibleParts.length > 0);
</script>

<Message from="assistant" class="max-w-none text-base">
	<div class="flex items-start gap-3 md:gap-5">
		<Avatar.Root class="size-9 shrink-0 border border-border/50 shadow-sm mt-1.5">
			<Avatar.Image src={portrait} alt="Chidi Nweke" class="object-cover" />
			<Avatar.Fallback class="bg-primary/10 text-primary text-[10px] font-bold">CN</Avatar.Fallback>
		</Avatar.Root>

		<div class="flex-1 min-w-0">
			{#if hasInlineParts}
				<div class="flex min-w-0 flex-col gap-4">
					{#each visibleParts as part, index (part.id)}
						{#if part.kind === 'text' && part.text.trim()}
							<MessageContent class={index > 0 ? 'mt-1' : ''}>
								<MessageResponse
									content={part.text}
									isStreaming={!!message.isStreaming && index === visibleParts.length - 1}
									sources={index === visibleParts.length - 1 ? message.sources : undefined}
								/>
							</MessageContent>
						{:else if part.kind === 'tool'}
							<div class="max-w-2xl">
								<InlineTool tool={part.tool} />
							</div>
						{/if}
					{/each}
				</div>
			{:else if message.content}
				<MessageContent>
					<MessageResponse content={message.content} isStreaming={!!message.isStreaming} sources={message.sources} />
				</MessageContent>
			{:else if fallbackToolCalls.length}
				<div class="min-w-0 max-w-2xl space-y-2">
					{#each fallbackToolCalls as tool (tool.callId ?? tool.toolName + tool.timestamp)}
						<InlineTool {tool} />
					{/each}
				</div>
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
		</div>
	</div>
</Message>
