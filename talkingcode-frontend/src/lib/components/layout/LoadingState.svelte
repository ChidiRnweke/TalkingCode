<script lang="ts">
	import { Loader2, Sparkles } from 'lucide-svelte';
	import { Skeleton } from '$lib/components/primitives';

	interface Props {
		phase?: 'planning' | 'tools' | 'streaming';
		title?: string;
		showSkeleton?: boolean;
	}

	let { phase = 'planning', title, showSkeleton = true }: Props = $props();

	const phaseConfig = {
		planning: {
			icon: Sparkles,
			defaultTitle: 'Analyzing your request...',
			subtitle: 'The planner is understanding intent and preparing a strategy'
		},
		tools: {
			icon: Loader2,
			defaultTitle: 'Gathering context...',
			subtitle: 'Running retrieval tools across your codebase'
		},
		streaming: {
			icon: Sparkles,
			defaultTitle: 'Composing response...',
			subtitle: 'Generating an answer based on the retrieved context'
		}
	};

	const config = $derived(phaseConfig[phase]);
	const displayTitle = $derived(title ?? config.defaultTitle);
</script>

<div class="flex flex-col items-center justify-center py-12 text-center">
	<div
		class="mb-6 flex h-14 w-14 animate-pulse items-center justify-center rounded-[var(--radius-xl)] border border-accent/30 bg-accent/12 shadow-[var(--shadow-sm)]"
	>
		<config.icon class="h-7 w-7 text-accent" />
	</div>
	<h3 class="font-display text-xl tracking-tight text-foreground">{displayTitle}</h3>
	<p class="mt-2 max-w-sm text-sm text-muted-foreground">{config.subtitle}</p>

	{#if showSkeleton}
		<div class="mt-8 w-full max-w-lg rounded-[var(--radius-lg)] border border-border/60 bg-[hsl(var(--color-surface-2)/0.55)] p-5">
			<Skeleton count={4} columns={1} />
		</div>
	{/if}
</div>
