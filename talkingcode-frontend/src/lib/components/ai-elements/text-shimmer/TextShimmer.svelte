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
		'relative inline-block shimmer-bg-size bg-clip-text text-transparent',
		'[background-repeat:no-repeat,padding-box]',
		'[--bg:linear-gradient(90deg,#0000_calc(50%-var(--spread)),var(--color-background),#0000_calc(50%+var(--spread)))]',
		'motion-safe:animate-text-shimmer shimmer-effect',
		className
	)}
	style:--spread="{dynamicSpread}px"
	style:--shimmer-duration="{duration}s"
	{...rest}
>
	{@render children()}
</svelte:element>

