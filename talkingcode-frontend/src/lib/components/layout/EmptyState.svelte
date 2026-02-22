<script lang="ts">
	import { MessageSquarePlus, type Icon as IconType } from 'lucide-svelte';

	interface Props {
		title?: string;
		description?: string;
		icon?: typeof IconType;
	}

	let {
		title = 'Ask your first repository question',
		description = 'The assistant will show planning context, tool activity, and a streamed answer without exposing payload bodies.',
		icon: Icon = MessageSquarePlus
	}: Props = $props();
</script>

<div
	class="flex h-full flex-col items-center justify-center rounded-[var(--radius-xl)] border border-dashed border-border/80 bg-[hsl(var(--color-surface-2)/0.58)] px-6 py-16 text-center shadow-[var(--shadow-sm)]"
>
	<div
		class="mb-6 flex h-16 w-16 items-center justify-center rounded-[var(--radius-xl)] border border-primary/20 bg-primary/10 shadow-[var(--shadow-sm)]"
	>
		<Icon class="h-8 w-8 text-primary/80" />
	</div>
	<h2 class="font-display text-2xl tracking-tight text-foreground">{title}</h2>
	<p class="mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">
		{description}
	</p>
	<p class="mt-5 text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">
		Try: "Summarize auth flow" or "Find flaky tests"
	</p>
</div>
