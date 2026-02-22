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
	import { Button } from '$lib/components/ui/button';

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

<div class="w-full max-w-2xl mx-auto space-y-6">
	<PromptInput
		onSubmit={handleSubmit}
		class="border-border/60 bg-background focus-within:border-primary/40 focus-within:ring-4 focus-within:ring-primary/5 p-2 shadow-lg"
	>
		<PromptInputBody>
			<PromptInputTextarea 
				placeholder="Ask me about how I built this or any other repo..." 
				class="text-lg py-4 px-4 min-h-[120px]"
			/>
		</PromptInputBody>
		<div class="flex justify-end p-2">
			<PromptInputSubmit class="h-10 px-6" />
		</div>
	</PromptInput>

	<div class="space-y-3">
		<p class="text-sm font-medium text-muted-foreground uppercase tracking-wider text-center">Some things to ask:</p>
		<div class="flex flex-wrap justify-center gap-2">
			{#each curatedPrompts as prompt}
				<button
					onclick={() => handleCuratedClick(prompt)}
					class="px-4 py-2 rounded-full border border-border bg-surface-2 hover:bg-surface-3 hover:border-primary/30 text-sm transition-all duration-200"
				>
					{prompt}
				</button>
			{/each}
		</div>
	</div>
</div>
