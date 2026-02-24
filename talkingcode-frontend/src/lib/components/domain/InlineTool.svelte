<script lang="ts">
	import { Search, Loader, Check, X } from 'lucide-svelte';
	import type { ToolCallTimelineItem } from '$lib/models';

	interface Props {
		tool: ToolCallTimelineItem;
	}

	let { tool }: Props = $props();

	let startTime = $state<number | null>(null);
	let currentDurationMs = $state<number | null>(null);

	$effect(() => {
		if (tool.status === 'started') {
			if (startTime === null) {
				startTime = Date.now();
			}
			const interval = setInterval(() => {
				if (startTime !== null) {
					currentDurationMs = Date.now() - startTime;
				}
			}, 100);
			return () => clearInterval(interval);
		} else if (tool.status === 'finished' || tool.status === 'failed') {
			startTime = null;
		}
	});

	const duration = $derived(
		tool.durationMs !== undefined
			? `${Math.max(0.1, tool.durationMs / 1000).toFixed(tool.durationMs < 1000 ? 1 : 2)}s`
			: currentDurationMs !== null
				? `${Math.max(0.1, currentDurationMs / 1000).toFixed(currentDurationMs < 1000 ? 1 : 2)}s`
				: ''
	);

	const toolName = $derived(
		tool.toolName
			.split('_')
			.filter(Boolean)
			.map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
			.join(' ')
	);

	const detailText = $derived.by(() => {
		const query = tool.visibleArgs?.query;
		if (typeof query === 'string' && query.trim()) {
			return query.trim();
		}

		const repository = tool.visibleArgs?.repository;
		const filePath = tool.visibleArgs?.file_path;
		if (typeof repository === 'string' && typeof filePath === 'string') {
			return `${repository}/${filePath}`;
		}

		return null;
	});
</script>

<div
	class="flex items-center gap-2 py-1 text-sm min-w-0 {tool.status === 'failed'
		? 'text-destructive'
		: 'text-muted-foreground'}"
>
	{#if tool.status === 'started'}
		<Loader class="size-3.5 animate-spin shrink-0" />
	{:else if tool.status === 'finished'}
		<Check class="size-3.5 text-emerald-600 shrink-0" />
	{:else}
		<X class="size-3.5 text-destructive shrink-0" />
	{/if}

	<Search class="size-3.5 text-muted-foreground/60 shrink-0" />
	<span class="font-medium text-foreground/90 shrink-0">{toolName}</span>

	{#if detailText}
		<span class="text-muted-foreground/80 truncate min-w-0 flex-1">{detailText}</span>
	{/if}

	{#if duration}
		<span class="ml-auto text-xs tabular-nums text-muted-foreground/60 shrink-0">{duration}</span>
	{/if}
</div>
