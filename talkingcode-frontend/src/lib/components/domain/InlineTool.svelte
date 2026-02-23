<script lang="ts">
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
			? `${Math.round(tool.durationMs)}ms`
			: currentDurationMs !== null
				? `${Math.round(currentDurationMs)}ms`
				: ''
	);

	const toolName = $derived(
		tool.toolName
			.split('_')
			.filter(Boolean)
			.map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
			.join(' ')
	);

	const statusLabel = $derived.by(() => {
		if (tool.status === 'started') return 'Running';
		if (tool.status === 'finished') return 'Completed';
		return 'Failed';
	});

	const statusClass = $derived.by(() => {
		if (tool.status === 'started') return 'text-muted-foreground';
		if (tool.status === 'finished') return 'text-emerald-700';
		return 'text-destructive';
	});

	const detailText = $derived.by(() => {
		const query = tool.visibleArgs?.query;
		if (typeof query === 'string' && query.trim()) {
			return `Query: ${query.trim()}`;
		}

		const repository = tool.visibleArgs?.repository;
		const filePath = tool.visibleArgs?.file_path;
		if (typeof repository === 'string' && typeof filePath === 'string') {
			return `File: ${repository}/${filePath}`;
		}

		return null;
	});
</script>

	<div class="py-1">
		<div class="flex items-center gap-2 text-sm">
			<span class="font-medium text-foreground">{toolName}</span>
			<span class={`text-xs ${statusClass}`}>{statusLabel}</span>
			{#if duration}
				<span class="text-xs text-muted-foreground">{duration}</span>
			{/if}
		</div>
		{#if detailText}
			<p class="mt-1 text-sm text-muted-foreground">{detailText}</p>
		{/if}
		{#if tool.status === 'failed'}
			<p class="mt-1 text-sm text-destructive">{tool.errorMessage ?? 'Tool failed'}</p>
		{/if}
	</div>
