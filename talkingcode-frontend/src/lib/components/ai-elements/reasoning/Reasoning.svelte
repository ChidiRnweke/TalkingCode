<script lang="ts">
	import { cn } from "$lib/utils";
	import { watch } from "runed";
	import { Collapsible } from "$lib/components/ui/collapsible/index.js";
	import { ReasoningContext, setReasoningContext } from "./reasoning-context.svelte";
	import { untrack } from "svelte";

	interface Props {
		class?: string;
		isStreaming?: boolean;
		open?: boolean;
		defaultOpen?: boolean;
		onOpenChange?: (open: boolean) => void;
		duration?: number;
		children?: import("svelte").Snippet;
	}

	let {
		class: className = "",
		isStreaming = false,
		open = $bindable(),
		defaultOpen = false,
		onOpenChange,
		duration = $bindable(),
		children,
		...props
	}: Props = $props();

	let AUTO_CLOSE_DELAY = 1000;
	let MS_IN_S = 1000;

	// Create the reasoning context
	let reasoningContext = new ReasoningContext({
		isStreaming: untrack(() => isStreaming),
		isOpen: untrack(() => open ?? defaultOpen),
		duration: untrack(() => duration ?? 0),
	});

	// Set up controllable state for open
	let isOpen = $state(untrack(() => open ?? defaultOpen));
	let currentDuration = $state(untrack(() => duration ?? 0));
	let hasAutoClosed = $state(false);
	let startTime = $state<number | null>(null);

	// Sync external props to context and local state
	$effect(() => {
		reasoningContext.isStreaming = isStreaming;
	});

	$effect(() => {
		if (open !== undefined) {
			isOpen = open;
			reasoningContext.isOpen = open;
		}
	});

	$effect(() => {
		if (duration !== undefined) {
			currentDuration = duration;
			reasoningContext.duration = duration;
		}
	});

	// Track duration when streaming starts and ends
	watch(
		() => isStreaming,
		(isStreamingValue) => {
			if (isStreamingValue) {
				if (startTime === null) {
					startTime = Date.now();
				}
				
				const interval = setInterval(() => {
					if (startTime !== null) {
						let newDuration = Math.ceil((Date.now() - startTime) / MS_IN_S);
						currentDuration = newDuration;
						reasoningContext.duration = newDuration;
					}
				}, 100);

				return () => clearInterval(interval);
			} else if (startTime !== null) {
				let newDuration = Math.ceil((Date.now() - startTime) / MS_IN_S);
				currentDuration = newDuration;
				reasoningContext.duration = newDuration;
				if (duration !== undefined) {
					duration = newDuration;
				}
				startTime = null;
			}
		}
	);

	// Auto-close when streaming ends (once only, respects manual toggle)
	let userManuallyToggled = $state(false);
	watch(
		() => [isStreaming, isOpen, hasAutoClosed] as const,
		([isStreamingValue, isOpenValue, hasAutoClosedValue]) => {
			if (!isStreamingValue && isOpenValue && !hasAutoClosedValue && !userManuallyToggled) {
				let timer = setTimeout(() => {
					handleOpenChange(false);
					hasAutoClosed = true;
				}, AUTO_CLOSE_DELAY);

				return () => clearTimeout(timer);
			}
		}
	);

	let handleOpenChange = (newOpen: boolean, manual = false) => {
		if (manual) {
			userManuallyToggled = true;
		}
		isOpen = newOpen;
		reasoningContext.setIsOpen(newOpen);

		if (open !== undefined) {
			open = newOpen;
		}

		onOpenChange?.(newOpen);
	};

	// Set the context for child components
	setReasoningContext(reasoningContext);
</script>

<Collapsible
	class={cn("not-prose mb-4 min-w-0", className)}
	bind:open={isOpen}
	onOpenChange={(newOpen) => handleOpenChange(newOpen, true)}
	{...props}
>
	{@render children?.()}
</Collapsible>
