<script lang="ts">
	import {
		PromptInput,
		PromptInputBody,
		PromptInputTextarea,
		PromptInputSubmit,
		type PromptInputMessage
	} from '$lib/components/ai-elements/prompt-input';
	import { chatStore } from '$lib/stores';
	import { goto } from '$app/navigation';

	interface Props {
		onAction?: () => void;
		compact?: boolean;
	}

	let { onAction, compact = false }: Props = $props();

	let inputText = $state('');
	const isSubmitDisabled = $derived(!inputText.trim());

	const curatedPrompts = [
		"How do you handle data ingestion?",
		"Show me your favorite Rust or Scala patterns.",
		"What's the architecture of this agent?"
	];

	function handleSubmit(message: PromptInputMessage) {
		const text = (message.text ?? '').trim();
		if (text) {
			chatStore.addUserMessage(text);
			onAction?.();
			inputText = '';
			goto('/chat');
		}
	}

	function handleCuratedClick(prompt: string) {
		chatStore.addUserMessage(prompt);
		onAction?.();
		goto('/chat');
	}
</script>

<div class={`w-full max-w-2xl mx-auto ${compact ? 'space-y-0' : 'space-y-4'}`}>
	{#if !compact}
		<div class="space-y-3">
			<p class="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] text-center md:text-left">
				Suggested starting points
			</p>
			<div class="flex flex-wrap justify-center md:justify-start gap-2">
				{#each curatedPrompts as prompt}
					<button
						onclick={() => handleCuratedClick(prompt)}
						class="px-4 py-2 rounded-full border border-border bg-background hover:bg-surface-2 hover:border-primary/40 text-xs transition-all duration-200 shadow-sm font-medium"
					>
						{prompt}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<div class="relative group">
		{#if !compact}
			<div class="absolute -inset-1 bg-gradient-to-r from-primary/20 to-accent/20 rounded-xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
		{/if}
		<PromptInput
			onSubmit={handleSubmit}
			class={`relative border-border/80 bg-background/90 backdrop-blur-sm focus-within:border-primary/50 focus-within:ring-8 focus-within:ring-primary/5 shadow-2xl ${compact ? 'rounded-lg p-1' : 'rounded-xl p-2'}`}
		>
			<PromptInputBody>
				<PromptInputTextarea 
					bind:value={inputText}
					placeholder="Ask me about how I built this..." 
					class={`${compact ? 'text-sm py-2 px-3 min-h-[44px]' : 'text-base py-3 px-4 min-h-[80px]'} resize-none border-none focus-visible:ring-0`}
				/>
			</PromptInputBody>
			<div class={`flex justify-end ${compact ? 'p-1' : 'p-2'}`}>
				<PromptInputSubmit disabled={isSubmitDisabled} class={`${compact ? 'h-8 px-4 rounded-md' : 'h-10 px-6 rounded-lg'} uppercase tracking-widest text-[9px] font-bold`} />
			</div>
		</PromptInput>
	</div>
</div>
