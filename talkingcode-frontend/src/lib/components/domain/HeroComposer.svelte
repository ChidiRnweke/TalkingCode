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
	}

	let { onAction }: Props = $props();

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
			goto('/chat');
		}
	}

	function handleCuratedClick(prompt: string) {
		chatStore.addUserMessage(prompt);
		onAction?.();
		goto('/chat');
	}
</script>

<div class="w-full max-w-2xl mx-auto space-y-4">
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

	<div class="relative group">
		<div class="absolute -inset-1 bg-gradient-to-r from-primary/20 to-accent/20 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
		<PromptInput
			onSubmit={handleSubmit}
			class="relative border-border/80 bg-background/90 backdrop-blur-sm focus-within:border-primary/50 focus-within:ring-8 focus-within:ring-primary/5 p-2 shadow-2xl rounded-2xl"
		>
			<PromptInputBody>
				<PromptInputTextarea 
					placeholder="Ask me about how I built this or any other repo..." 
					class="text-lg py-5 px-4 min-h-[140px] resize-none border-none focus-visible:ring-0"
				/>
			</PromptInputBody>
			<div class="flex justify-end p-2">
				<PromptInputSubmit class="h-12 px-8 rounded-xl uppercase tracking-widest text-[10px] font-bold" />
			</div>
		</PromptInput>
	</div>
</div>
