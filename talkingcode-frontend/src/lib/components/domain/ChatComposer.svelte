<script lang="ts">
	import {Button} from '$lib/components/ui/button';
	import { Send } from 'lucide-svelte';

	interface Props {
		onSubmit: (question: string) => void;
		disabled?: boolean;
	}

	let { onSubmit, disabled = false }: Props = $props();

	let textarea: HTMLTextAreaElement;
	let question = $state('');

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (question.trim() && !disabled) {
			onSubmit(question.trim());
			question = '';
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e);
		}
	}
</script>

<div class="border-t border-border bg-background px-[var(--page-padding)] py-4">
	<form onsubmit={handleSubmit} class="flex flex-col gap-3">
		<textarea
			bind:this={textarea}
			bind:value={question}
			onkeydown={handleKeydown}
			placeholder="Ask about architecture, modules, ownership, or behavior..."
			rows="3"
			disabled={disabled}
			class="w-full resize-none rounded-lg border border-border/60 bg-surface-2 px-4 py-3 text-sm placeholder:text-muted-foreground/70 focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15"
		></textarea>
		<div class="flex justify-end">
			<Button type="submit" disabled={disabled || !question.trim()} variant="default">
				<Send class="mr-2 h-4 w-4" />
				Send
			</Button>
		</div>
	</form>
</div>