<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import MessageResponse from '$lib/components/ai-elements/new-message/MessageResponse.svelte';
	import MessageToolbar from '$lib/components/ai-elements/new-message/MessageToolbar.svelte';
	import MessageActions from '$lib/components/ai-elements/new-message/MessageActions.svelte';
	import MessageAction from '$lib/components/ai-elements/new-message/MessageAction.svelte';
	import { ChainOfThought, ChainOfThoughtStep } from '$lib/components/ai-elements/chain-of-thought';
	import { ThinkingBar } from '$lib/components/ai-elements/thinking-bar';
	import InlineTool from './InlineTool.svelte';
	import { Copy, RotateCcw } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';
	import { buildAssistantBlocks } from '$lib/utils/assistantBlocks';
	import { chatStore } from '$lib/stores';
	import * as Avatar from '$lib/components/ui/avatar';
	import portrait from '$lib/assets/portrait.png';

	interface Props {
		message: ChatMessage;
		onRetry?: (question: string) => void;
	}

	let { message, onRetry }: Props = $props();

	function handleCopy() {
		navigator.clipboard.writeText(answerText);
	}

	function handleRetry() {
		const question = chatStore.retry(message.id);
		if (question && onRetry) {
			onRetry(question);
		}
	}

	let blocks = $derived(buildAssistantBlocks(message));
	// The answer prose only (excludes per-step narration headers).
	let answerText = $derived(
		blocks
			.filter((block) => block.kind === 'text')
			.map((block) => block.text)
			.join('\n\n')
	);
	let lastTextBlockId = $derived.by(() => {
		for (let i = blocks.length - 1; i >= 0; i--) {
			if (blocks[i].kind === 'text') return blocks[i].id;
		}
		return null;
	});
	// Before the first token/tool arrives, show a lightweight "thinking" status.
	let showInitialThinking = $derived(!!message.isStreaming && blocks.length === 0);
</script>

<Message from="assistant" class="max-w-none text-base">
	<div class="flex items-start gap-3 md:gap-5">
		<Avatar.Root class="size-9 shrink-0 border border-border/50 shadow-sm mt-1.5">
			<Avatar.Image src={portrait} alt="Chidi Nweke" class="object-cover" />
			<Avatar.Fallback class="bg-primary/10 text-primary text-[10px] font-bold">CN</Avatar.Fallback>
		</Avatar.Root>

		<div class="flex-1 min-w-0">
			<div class="flex min-w-0 flex-col gap-4">
				{#if showInitialThinking}
					<ThinkingBar text="Thinking" />
				{/if}

				{#each blocks as block (block.id)}
					{#if block.kind === 'step'}
						<ChainOfThought>
							<ChainOfThoughtStep
								summary={block.summary}
								status={block.status}
								durationLabel={block.durationLabel}
							>
								{#if block.reasoning || block.tools.length}
									<div class="flex min-w-0 flex-col gap-2">
										{#if block.reasoning}
											<div
												class="min-w-0 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground [overflow-wrap:anywhere]"
											>
												{block.reasoning}
											</div>
										{/if}
										{#each block.tools as tool (tool.callId ?? tool.toolName + tool.timestamp)}
											<InlineTool {tool} />
										{/each}
									</div>
								{/if}
							</ChainOfThoughtStep>
						</ChainOfThought>
					{:else}
						<MessageContent>
							<MessageResponse
								content={block.text}
								isStreaming={!!message.isStreaming && block.id === lastTextBlockId}
								sources={block.id === lastTextBlockId ? message.sources : undefined}
							/>
						</MessageContent>
					{/if}
				{/each}
			</div>

			{#if message.error}
				<div class="rounded-md bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
					<p class="font-bold mb-1">Error</p>
					{message.error}
				</div>
			{/if}

			{#if !message.isStreaming}
				<MessageToolbar class="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
					<MessageActions>
						{#if answerText}
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
