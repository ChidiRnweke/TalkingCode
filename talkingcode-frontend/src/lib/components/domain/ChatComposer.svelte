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
	import { Message } from '$lib/components/ai-elements/new-message';

	interface Props {
		onSubmit: (question: string) => void;
		disabled?: boolean;
		selectedModel?: string | null;
		onModelChange?: (model: string) => void;
		models: Array<{ id: string; label: string }>;
		defaultModel: string | null;
	}

	let {
		onSubmit,
		disabled = false,
		selectedModel = null,
		onModelChange,
		models,
		defaultModel
	}: Props = $props();

	let inputText = $state('');

	function handleSubmit(message: PromptInputMessage) {
		const text = (message.text ?? '').trim();
		if (text && !disabled) {
			onSubmit(text);
			inputText = '';
		}
	}

	const isSubmitDisabled = $derived(disabled || !inputText.trim());

	const fallbackModel = $derived(defaultModel || models[0]?.id || 'google/gemini-3-flash-preview');
</script>

<div class="fixed bottom-0 left-0 right-0 z-40 p-4 md:p-6 pointer-events-none">
	<div class="mx-auto max-w-3xl w-full pointer-events-auto">
		<Message from="user" class="max-w-none">
			<PromptInput
				onSubmit={handleSubmit}
				class="border-border/60 bg-background/80 backdrop-blur-lg shadow-2xl focus-within:border-primary/40 focus-within:ring-4 focus-within:ring-primary/5"
			>
				<PromptInputBody>
					<PromptInputTextarea
						bind:value={inputText}
						placeholder="Ask about architecture, modules, ownership, or behavior..."
					/>
				</PromptInputBody>
				<PromptInputToolbar>
					<PromptInputModelSelect
						value={selectedModel || fallbackModel}
						onValueChange={(v) => onModelChange?.(v ?? fallbackModel)}
					>
						<PromptInputModelSelectTrigger>
							<PromptInputModelSelectValue placeholder="Select model" />
						</PromptInputModelSelectTrigger>
						<PromptInputModelSelectContent>
							{#each models as model}
								<PromptInputModelSelectItem value={model.id}>
									{model.label}
								</PromptInputModelSelectItem>
							{/each}
						</PromptInputModelSelectContent>
					</PromptInputModelSelect>

					<PromptInputSubmit disabled={isSubmitDisabled} />
				</PromptInputToolbar>
			</PromptInput>
		</Message>
		<p class="mt-3 text-[10px] text-center text-muted-foreground uppercase tracking-widest">
			My AI agent might make some mistakes 😅
		</p>
	</div>
</div>
