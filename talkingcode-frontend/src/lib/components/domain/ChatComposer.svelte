<script lang="ts">
	import {
		PromptInput,
		PromptInputBody,
		PromptInputTextarea,
		PromptInputToolbar,
		PromptInputSubmit,
		PromptInputModelSelect,
		PromptInputModelSelectTrigger,
		PromptInputModelSelectContent,
		PromptInputModelSelectItem,
		PromptInputModelSelectValue,
		type PromptInputMessage
	} from '$lib/components/ai-elements/prompt-input';

	interface Props {
		onSubmit: (question: string) => void;
		disabled?: boolean;
		selectedModel?: string | null;
		onModelChange?: (model: string) => void;
	}

	let { onSubmit, disabled = false, selectedModel = null, onModelChange }: Props = $props();

	function handleSubmit(message: PromptInputMessage) {
		const text = (message.text ?? '').trim();
		if (text && !disabled) {
			onSubmit(text);
		}
	}

	const models = [
		{ value: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
		{ value: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
		{ value: 'openai/gpt-4o', label: 'GPT-4o' }
	];
</script>

<div class="fixed bottom-0 left-0 right-0 z-40 p-4 md:p-6 pointer-events-none">
	<div class="mx-auto max-w-3xl w-full pointer-events-auto">
		<PromptInput
			onSubmit={handleSubmit}
			class="border-border/60 bg-background/80 backdrop-blur-lg shadow-2xl focus-within:border-primary/40 focus-within:ring-4 focus-within:ring-primary/5"
		>
			<PromptInputBody>
				<PromptInputTextarea placeholder="Ask about architecture, modules, ownership, or behavior..." />
			</PromptInputBody>
			<PromptInputToolbar>
				<PromptInputModelSelect
					value={selectedModel || models[0].value}
					onValueChange={(v) => onModelChange?.(v ?? models[0].value)}
				>
					<PromptInputModelSelectTrigger>
						<PromptInputModelSelectValue placeholder="Select model" />
					</PromptInputModelSelectTrigger>
					<PromptInputModelSelectContent>
						{#each models as model}
							<PromptInputModelSelectItem value={model.value}>
								{model.label}
							</PromptInputModelSelectItem>
						{/each}
					</PromptInputModelSelectContent>
				</PromptInputModelSelect>

				<PromptInputSubmit disabled={disabled} />
			</PromptInputToolbar>
		</PromptInput>
		<p class="mt-3 text-[10px] text-center text-muted-foreground uppercase tracking-widest">
			Chidi might make mistakes. Verify important info.
		</p>
	</div>
</div>
