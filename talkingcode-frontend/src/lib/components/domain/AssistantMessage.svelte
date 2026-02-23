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
	import type { ChatMessage, ReasoningStep } from '$lib/models';
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

	const sortedReasoningSteps = $derived.by(() => {
		const steps = [...(message.reasoningSteps ?? [])];
		return steps.sort((a, b) => {
			const timeDiff = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
			if (timeDiff !== 0) return timeDiff;
			if (a.kind === 'plan' && b.kind === 'tool') return -1;
			if (a.kind === 'tool' && b.kind === 'plan') return 1;
			return 0;
		});
	});

	function reasoningKey(step: ReasoningStep): string {
		if (step.kind === 'plan') {
			return step.id;
		}
		if (step.kind === 'tool') {
			return step.tool.callId ?? step.id;
		}
		return step.id;
	}

	let isThinking = $derived(message.isStreaming && !message.content);
	let hasContent = $derived(
		(message.reasoningSteps?.length ?? 0) > 0 || !!message.planText || !!message.toolCalls?.length
	);
	let hasThought = $derived(hasContent || !!message.plan || !!message.planText || !!message.toolCalls?.length);

	// Auto-open when content arrives, stay closed until then
	let reasoningOpen = $state(false);
	let hasAutoOpened = $state(false);

	$effect(() => {
		if (hasContent && !hasAutoOpened) {
			reasoningOpen = true;
			hasAutoOpened = true;
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
				{#if sortedReasoningSteps.length > 0}
					<div class="relative pl-6">
						<div class="absolute left-2.5 top-2 bottom-2 w-px bg-border/70"></div>
						<ol class="space-y-3">
							{#each sortedReasoningSteps as step (reasoningKey(step))}
								<li class="relative">
									{#if step.kind === 'plan'}
										<span class="absolute -left-6 top-2.5 size-2.5 rounded-full border border-primary/40 bg-primary/80"></span>
										<div class="space-y-1 rounded-md border border-border/60 bg-background/50 px-3 py-2">
											<p class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
												Plan {step.iteration}
											</p>
											<p class="text-sm whitespace-pre-wrap text-foreground/90">{step.text}</p>
										</div>
									{:else if step.kind === 'tool'}
										<span class="absolute -left-6 top-2.5 size-2.5 rounded-full border border-border bg-muted-foreground/70"></span>
										<div class="rounded-md border border-border/60 bg-background/30 px-3 py-2">
											<InlineTool tool={step.tool} />
										</div>
									{:else if step.phase === 'answer_started'}
										<span class="absolute -left-6 top-2.5 size-2.5 rounded-full border border-accent/40 bg-accent"></span>
										<p class="rounded-md border border-border/60 bg-background/40 px-3 py-2 text-xs font-medium italic text-muted-foreground/80">
											Switching to final answer
										</p>
									{/if}
								</li>
							{/each}
						</ol>
					</div>
				{:else}
					{#if message.planText}
						<div class="space-y-1 rounded-md border border-border/60 bg-background/50 px-3 py-2">
							<p class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Plan</p>
							<p class="text-sm whitespace-pre-wrap text-foreground/90">{message.planText}</p>
						</div>
					{/if}
					{#if message.toolCalls?.length}
						<div class="space-y-2">
							{#each message.toolCalls as tool (tool.callId ?? tool.toolName + tool.timestamp)}
								<InlineTool {tool} />
							{/each}
						</div>
					{/if}
				{/if}
			</ReasoningContent>
		</Reasoning>
	{/if}

	{#if message.content}
		<MessageContent class={hasThought ? 'mt-3' : ''}>
			<MessageResponse
				content={message.content}
				isStreaming={!!message.isStreaming}
				sources={message.sources}
			/>
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
