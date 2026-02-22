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

<div class="border-t border-border bg-background px-[var(--page-padding)] py-4">
	<PromptInput
		onSubmit={handleSubmit}
		class="border-border/60 bg-[hsl(var(--color-surface-2))] focus-within:border-[hsl(var(--color-primary)/0.4)] focus-within:ring-2 focus-within:ring-[hsl(var(--color-primary)/0.15)]"
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
</div>
