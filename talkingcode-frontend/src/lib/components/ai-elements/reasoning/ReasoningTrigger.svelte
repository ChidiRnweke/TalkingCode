<script lang="ts">
	import { cn } from "$lib/utils";
	import { CollapsibleTrigger } from "$lib/components/ui/collapsible/index.js";
	import { getReasoningContext } from "./reasoning-context.svelte.js";
	import ChevronRightIcon from "@lucide/svelte/icons/chevron-right";
	import Loader from "../loader/Loader.svelte";
	import Shimmer from "../shimmer/Shimmer.svelte";

	interface Props {
		class?: string;
		onclick?: () => void;
		toolCount?: number;
		children?: import("svelte").Snippet;
	}

	let { class: className = "", onclick, toolCount = 0, children }: Props = $props();

	let reasoningContext = getReasoningContext();

	let getThinkingMessage = $derived.by(() => {
		let { isStreaming, duration } = reasoningContext;

		if (isStreaming) {
			return "Thinking...";
		}
		if (!duration) {
			return "Thought for a few seconds";
		}
		return `Thought for ${duration === 1 ? "1 second" : `${duration} seconds`}`;
	});
</script>

<CollapsibleTrigger
	class={cn(
		"text-muted-foreground hover:text-foreground group/reasoning inline-flex w-fit min-w-0 max-w-full items-center gap-1.5 text-left text-sm transition-colors",
		className
	)}
	{onclick}
>
	{#if reasoningContext.isStreaming}
		<Loader size={14} class="shrink-0 text-primary" />
		<Shimmer
			as="span"
			class="min-w-0 whitespace-normal leading-snug [overflow-wrap:anywhere]"
		>
			{#if children}{@render children()}{:else}{getThinkingMessage}{/if}
		</Shimmer>
	{:else}
		<ChevronRightIcon
			class={cn(
				"size-3.5 shrink-0 text-muted-foreground/70 transition-transform",
				reasoningContext.isOpen ? "rotate-90" : "rotate-0"
			)}
		/>
		<span class="min-w-0 whitespace-normal leading-snug [overflow-wrap:anywhere]">
			{#if children}{@render children()}{:else}{getThinkingMessage}{/if}
		</span>
		{#if toolCount > 0}
			<span class="shrink-0 whitespace-nowrap text-muted-foreground/60">
				· {toolCount} {toolCount === 1 ? "tool call" : "tool calls"}
			</span>
		{/if}
	{/if}
</CollapsibleTrigger>
