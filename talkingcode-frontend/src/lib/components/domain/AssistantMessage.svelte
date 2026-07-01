<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import MessageResponse from '$lib/components/ai-elements/new-message/MessageResponse.svelte';
	import MessageToolbar from '$lib/components/ai-elements/new-message/MessageToolbar.svelte';
	import MessageActions from '$lib/components/ai-elements/new-message/MessageActions.svelte';
	import MessageAction from '$lib/components/ai-elements/new-message/MessageAction.svelte';
	import Reasoning from '$lib/components/ai-elements/reasoning/Reasoning.svelte';
	import ReasoningTrigger from '$lib/components/ai-elements/reasoning/ReasoningTrigger.svelte';
	import ReasoningContent from '$lib/components/ai-elements/reasoning/ReasoningContent.svelte';
	import { ThinkingBar } from '$lib/components/ai-elements/thinking-bar';
	import InlineTool from './InlineTool.svelte';
	import { Copy, RotateCcw } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';
	import {
		parseAssistantTags,
		type ReasoningSegment,
		type TextSegment,
		type ToolSegment
	} from '$lib/utils/assistantTags';
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

	let segments = $derived(parseAssistantTags(message.content));
	let answerText = $derived(
		segments
			.filter((segment) => segment.kind === 'text')
			.map((segment) => segment.text)
			.join('')
	);
	let showInitialThinking = $derived(!!message.isStreaming && !message.content);

	interface StepBlock {
		kind: 'step';
		id: string;
		reasoning: ReasoningSegment | null;
		tools: ToolSegment[];
	}
	interface TextBlock {
		kind: 'text';
		segment: TextSegment;
	}
	type Block = StepBlock | TextBlock;

	// Group each thought with the tool calls of the same step so that a
	// collapsed step renders as a single muted line, like Claude's UI.
	// Tool segments join the most recent step even when answer text streamed
	// in between (the model narrates before calling tools).
	let blocks = $derived.by(() => {
		const result: Block[] = [];
		let currentStep: StepBlock | null = null;
		for (const segment of segments) {
			if (segment.kind === 'text') {
				if (segment.text.trim()) result.push({ kind: 'text', segment });
			} else if (segment.kind === 'reasoning') {
				if (!segment.text.trim()) continue;
				currentStep = { kind: 'step', id: segment.id, reasoning: segment, tools: [] };
				result.push(currentStep);
			} else {
				if (!currentStep) {
					currentStep = { kind: 'step', id: `step-${segment.id}`, reasoning: null, tools: [] };
					result.push(currentStep);
				}
				currentStep.tools.push(segment);
			}
		}
		return result;
	});

	let lastStepId = $derived.by(() => {
		for (let i = blocks.length - 1; i >= 0; i--) {
			const block = blocks[i];
			if (block.kind === 'step') return block.id;
		}
		return null;
	});
	let lastSegment = $derived(segments[segments.length - 1]);
</script>

<Message from="assistant" class="max-w-none text-base">
	<div class="flex items-start gap-3 md:gap-5">
		<Avatar.Root class="size-9 shrink-0 border border-border/50 shadow-sm mt-1.5">
			<Avatar.Image src={portrait} alt="Chidi Nweke" class="object-cover" />
			<Avatar.Fallback class="bg-primary/10 text-primary text-[10px] font-bold">CN</Avatar.Fallback>
		</Avatar.Root>

		<div class="flex-1 min-w-0">
			<div class="flex min-w-0 flex-col gap-3">
				{#if showInitialThinking}
					<ThinkingBar text="Thinking" />
				{/if}

				{#each blocks as block (block.kind === 'text' ? block.segment.id : block.id)}
					{#if block.kind === 'text'}
						<MessageContent class="my-1">
							<MessageResponse
								content={block.segment.text}
								isStreaming={!!message.isStreaming && block.segment === lastSegment}
								sources={message.sources}
							/>
						</MessageContent>
					{:else}
						{@const isActiveStep = !!message.isStreaming && block.id === lastStepId}
						<Reasoning isStreaming={isActiveStep} defaultOpen={isActiveStep}>
							<ReasoningTrigger toolCount={block.tools.length} />
							<ReasoningContent>
								<div class="flex min-w-0 flex-col gap-2.5">
									{#if block.reasoning}
										<MessageResponse
											content={block.reasoning.text}
											isStreaming={isActiveStep && block.reasoning === lastSegment}
											class="prose-sm min-w-0 text-sm leading-relaxed text-muted-foreground wrap-anywhere prose-p:text-muted-foreground prose-li:text-muted-foreground prose-strong:text-muted-foreground prose-headings:text-muted-foreground [&_p]:my-2"
										/>
									{/if}
									{#each block.tools as tool (tool.id)}
										<InlineTool {tool} />
									{/each}
								</div>
							</ReasoningContent>
						</Reasoning>
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
