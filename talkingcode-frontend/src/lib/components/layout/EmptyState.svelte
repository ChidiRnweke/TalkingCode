<script lang="ts">
	import { MessageSquarePlus, type Icon as IconType } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';

	interface Props {
		title?: string;
		description?: string;
		icon?: typeof IconType;
		suggestions?: string[];
		onSuggestionClick?: (suggestion: string) => void;
	}

	let {
		title = 'Ask your first question',
		description = 'Research your codebase — ask about architecture, ownership, or behaviour.',
		icon: Icon = MessageSquarePlus,
		suggestions = [],
		onSuggestionClick
	}: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-16 text-center">
	<div
		class="mb-6 flex h-14 w-14 items-center justify-center rounded-[var(--radius-lg)] border border-primary/20 bg-primary/10"
	>
		<Icon class="h-7 w-7 text-primary/80" />
	</div>
	<h2 class="font-display text-2xl tracking-tight text-foreground">{title}</h2>
	<p class="mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">{description}</p>
	{#if suggestions && suggestions.length > 0}
		<div class="mt-6 flex flex-wrap justify-center gap-2">
			{#each suggestions as suggestion}
				<Button
					type="button"
					variant="outline"
					size="sm"
					onclick={() => onSuggestionClick?.(suggestion)}
					class="rounded-[var(--radius-full)] border-border bg-[hsl(var(--color-surface-2))] text-foreground hover:bg-[hsl(var(--color-surface-3))]"
				>
					{suggestion}
				</Button>
			{/each}
		</div>
	{/if}
</div>
