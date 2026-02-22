<script lang="ts">
	import { MessageSquarePlus, type Icon as IconType } from 'lucide-svelte';

	interface Props {
		title?: string;
		description?: string;
		suggestion?: string;
		icon?: typeof IconType;
	}

	let {
		title = 'Ask your first question',
		description = 'Research your codebase — ask about architecture, ownership, or behaviour.',
		suggestion = 'Try: "Summarize auth flow" or "Find flaky tests"',
		icon: Icon = MessageSquarePlus
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
	<p class="mt-5 text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">
		{suggestion}
	</p>
</div>
