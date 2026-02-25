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
		"text-muted-foreground hover:text-foreground flex w-full min-w-0 max-w-full items-start gap-2 overflow-hidden text-sm transition-colors sm:text-base",
		className
	)}
	{onclick}
>
	<div class="flex w-full min-w-0 max-w-full items-start gap-2 overflow-hidden">
		{#if reasoningContext.isStreaming}
			<Loader size={14} class="text-primary mt-0.5 shrink-0" />
			{#if children}
				<div class="w-full min-w-0 max-w-full flex-1 text-left">
					<Shimmer
						as="span"
						class="block w-full min-w-0 max-w-full whitespace-normal leading-snug wrap-anywhere"
					>
						{@render children()}
					</Shimmer>
				</div>
			{:else}
				<div class="w-full min-w-0 max-w-full flex-1 text-left">
					<Shimmer
						as="span"
						class="block w-full min-w-0 max-w-full whitespace-normal leading-snug wrap-anywhere"
					>
						{getThinkingMessage}
					</Shimmer>
				</div>
			{/if}
		{:else}
			{#if children}
				<div class="w-full min-w-0 max-w-full flex-1 text-left whitespace-normal leading-snug wrap-anywhere">
					{@render children()}
				</div>
			{:else}
				<ChevronRightIcon
					class={cn(
						"size-4 mt-0.5 shrink-0 transition-transform",
						reasoningContext.isOpen ? "rotate-90" : "rotate-0"
					)}
				/>
				<p class="w-full min-w-0 max-w-full flex-1 whitespace-normal leading-snug wrap-anywhere">
					{getThinkingMessage}
				</p>
			{/if}
		{/if}
	</div>
</CollapsibleTrigger>
