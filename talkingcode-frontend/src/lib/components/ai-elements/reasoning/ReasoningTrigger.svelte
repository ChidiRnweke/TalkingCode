<script lang="ts">
	import { cn } from "$lib/utils";
	import { CollapsibleTrigger } from "$lib/components/ui/collapsible/index.js";
	import { getReasoningContext } from "./reasoning-context.svelte.js";
	import ChevronRightIcon from "@lucide/svelte/icons/chevron-right";

	interface Props {
		class?: string;
		onclick?: () => void;
		children?: import("svelte").Snippet;
	}

	let { class: className = "", onclick, children }: Props = $props();

	let reasoningContext = getReasoningContext();

	let getThinkingMessage = $derived.by(() => {
		let { isStreaming, duration } = reasoningContext;

		if (isStreaming || duration === 0) {
			return "Thinking...";
		}
		if (duration === undefined) {
			return "Thought for a few seconds";
		}
		return `Thought for ${duration} seconds`;
	});
</script>

<CollapsibleTrigger
	class={cn(
		"text-muted-foreground hover:text-foreground flex w-full items-center gap-2 text-sm transition-colors",
		className
	)}
	{onclick}
>
	{#if children}
		{@render children()}
	{:else}
		<ChevronRightIcon
			class={cn(
				"size-4 transition-transform",
				reasoningContext.isOpen ? "rotate-90" : "rotate-0"
			)}
		/>
		<p>{getThinkingMessage}</p>
	{/if}
</CollapsibleTrigger>
