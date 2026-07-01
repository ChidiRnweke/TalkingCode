<script lang="ts">
	import { cn } from "$lib/utils";
	import { watch } from "runed";
	import type { ShimmerProps } from "./types";

	let {
		children,
		as = "p",
		class: className,
		duration = 2,
		spread = 2,
		content_length = 30,
		...rest
	}: ShimmerProps = $props();

	// Calculate dynamic spread based on text length
	let dynamicSpread = $derived(content_length * spread);
</script>

<svelte:element
	this={as}
	class={cn(
		"relative inline-block shimmer-bg-size bg-clip-text text-transparent",
		"[background-repeat:no-repeat,padding-box] [--bg:linear-gradient(90deg,#0000_calc(50%-var(--spread)),var(--color-background),#0000_calc(50%+var(--spread)))]",
		"animate-shimmer shimmer-effect",
		className
	)}
	style:--spread="{dynamicSpread}px"
	style:--shimmer-duration="{duration}s"
	{...rest}
>
	{@render children()}
</svelte:element>

