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
	class="flex w-full min-w-0 flex-wrap items-start gap-x-2 gap-y-0.5 py-1 text-sm {tool.status === 'failed'
		? 'text-destructive'
		: 'text-muted-foreground'}"
>
	<div class="flex shrink-0 items-center gap-2">
		{#if tool.status === 'started'}
			<Loader class="size-3.5 shrink-0 animate-spin" />
		{:else if tool.status === 'finished'}
			<Check class="size-3.5 shrink-0 text-emerald-600" />
		{:else}
			<X class="size-3.5 shrink-0 text-destructive" />
		{/if}

		<Search class="size-3.5 shrink-0 text-muted-foreground/60" />
		<span class="font-medium text-foreground/90">{toolName}</span>
	</div>

	{#if detailText}
		<span class="min-w-0 flex-1 text-muted-foreground/80 [overflow-wrap:anywhere]">{detailText}</span>
	{/if}

	{#if duration}
		<span class="shrink-0 text-xs tabular-nums text-muted-foreground/60">{duration}</span>
	{/if}
</div>
