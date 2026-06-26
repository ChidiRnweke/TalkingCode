<script lang="ts">
	import { cn } from '$lib/utils';
	import {
		Collapsible,
		CollapsibleTrigger,
		CollapsibleContent
	} from '$lib/components/ui/collapsible/index.js';
	import { Check, ChevronRight, X } from 'lucide-svelte';
	import Loader from '../loader/Loader.svelte';
	import TextShimmer from '../text-shimmer/TextShimmer.svelte';
	import { untrack, type Snippet } from 'svelte';

	interface Props {
		summary: string;
		status?: 'running' | 'done' | 'error';
		durationLabel?: string;
		children?: Snippet;
		class?: string;
	}

	let {
		summary,
		status = 'done',
		durationLabel,
		children,
		class: className = ''
	}: Props = $props();

	let hasContent = $derived(!!children);
	let isOpen = $state(untrack(() => status === 'running'));
	let userToggled = $state(false);

	// Auto-open while running; collapse shortly after finishing unless toggled.
	$effect(() => {
		if (userToggled) return;
		if (status === 'running') {
			isOpen = true;
			return;
		}
		const timer = setTimeout(() => {
			if (!userToggled) isOpen = false;
		}, 1200);
		return () => clearTimeout(timer);
	});
</script>

<div class={cn('flex min-w-0 gap-3', className)}>
	<!-- timeline gutter -->
	<div class="flex flex-col items-center">
		<div class="mt-0.5 flex size-5 shrink-0 items-center justify-center">
			{#if status === 'running'}
				<Loader size={14} class="text-primary" />
			{:else if status === 'error'}
				<X class="size-4 text-destructive" />
			{:else}
				<Check class="size-4 text-emerald-600" />
			{/if}
		</div>
		{#if isOpen && hasContent}
			<div class="my-1 w-px flex-1 bg-border"></div>
		{/if}
	</div>

	<Collapsible
		bind:open={isOpen}
		onOpenChange={() => (userToggled = true)}
		class="min-w-0 flex-1"
	>
		<CollapsibleTrigger
			class={cn(
				'flex w-full min-w-0 items-center gap-2 text-left',
				hasContent ? 'cursor-pointer' : 'cursor-default'
			)}
			disabled={!hasContent}
		>
			<span class="min-w-0 flex-1">
				{#if status === 'running'}
					<TextShimmer
						as="span"
						contentLength={summary.length}
						class="block min-w-0 whitespace-normal text-sm leading-snug wrap-anywhere"
					>
						{summary}
					</TextShimmer>
				{:else}
					<span
						class="block min-w-0 whitespace-normal text-sm leading-snug text-[hsl(var(--color-text-subtle))] wrap-anywhere"
					>
						{summary}
					</span>
				{/if}
			</span>

			{#if durationLabel}
				<span class="shrink-0 text-xs tabular-nums text-muted-foreground/60">{durationLabel}</span>
			{/if}

			{#if hasContent}
				<ChevronRight
					class={cn(
						'size-4 shrink-0 text-muted-foreground/50 transition-transform',
						isOpen ? 'rotate-90' : 'rotate-0'
					)}
				/>
			{/if}
		</CollapsibleTrigger>

		{#if hasContent}
			<CollapsibleContent
				class="min-w-0 pt-2 pb-1 text-sm data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 outline-none"
			>
				{@render children?.()}
			</CollapsibleContent>
		{/if}
	</Collapsible>
</div>
