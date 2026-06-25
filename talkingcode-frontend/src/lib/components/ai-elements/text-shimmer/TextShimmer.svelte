<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	type Props = HTMLAttributes<HTMLElement> & {
		children: Snippet;
		as?: keyof HTMLElementTagNameMap;
		duration?: number;
		/** Highlight band factor; multiplied by the text length. */
		spread?: number;
		/** Approximate length of the text, used to size the shimmer band. */
		contentLength?: number;
		class?: string;
	};

	let {
		children,
		as = 'span',
		duration = 2,
		spread = 2,
		contentLength = 30,
		class: className,
		...rest
	}: Props = $props();

	let dynamicSpread = $derived(Math.max(24, contentLength * spread));
</script>

<svelte:element
	this={as}
	class={cn(
		'relative inline-block bg-[length:250%_100%,auto] bg-clip-text text-transparent',
		'[background-repeat:no-repeat,padding-box]',
		'[--bg:linear-gradient(90deg,#0000_calc(50%-var(--spread)),var(--color-background),#0000_calc(50%+var(--spread)))]',
		'motion-safe:animate-text-shimmer',
		className
	)}
	style="--spread: {dynamicSpread}px; --shimmer-duration: {duration}s; background-image: var(--bg), linear-gradient(var(--color-muted-foreground), var(--color-muted-foreground)); background-position: 100% center;"
	{...rest}
>
	{@render children()}
</svelte:element>

<style>
	@keyframes text-shimmer {
		from {
			background-position: 100% center;
		}
		to {
			background-position: 0% center;
		}
	}

	:global(.animate-text-shimmer) {
		animation: text-shimmer var(--shimmer-duration, 2s) linear infinite;
	}
</style>
