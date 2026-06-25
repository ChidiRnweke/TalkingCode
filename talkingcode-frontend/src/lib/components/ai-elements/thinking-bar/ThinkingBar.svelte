<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLAttributes } from 'svelte/elements';
	import Loader from '../loader/Loader.svelte';
	import TextShimmer from '../text-shimmer/TextShimmer.svelte';

	type Props = Omit<HTMLAttributes<HTMLDivElement>, 'onclick'> & {
		text?: string;
		onStop?: () => void;
		stopLabel?: string;
		onclick?: () => void;
		class?: string;
	};

	let {
		text = 'Thinking',
		onStop,
		stopLabel = 'Answer now',
		onclick,
		class: className,
		...rest
	}: Props = $props();
</script>

<div class={cn('flex min-w-0 items-center gap-3 text-sm', className)} {...rest}>
	<Loader size={14} class="shrink-0 text-primary" />

	{#if onclick}
		<button type="button" {onclick} class="min-w-0 text-left">
			<TextShimmer as="span" contentLength={text.length}>{text}…</TextShimmer>
		</button>
	{:else}
		<TextShimmer as="span" contentLength={text.length}>{text}…</TextShimmer>
	{/if}

	{#if onStop}
		<button
			type="button"
			onclick={onStop}
			class="ml-auto shrink-0 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
		>
			{stopLabel}
		</button>
	{/if}
</div>
