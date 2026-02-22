<script lang="ts">
	import type { ToolCallTimelineItem } from '$lib/models';
	import { Card, Badge } from '$lib/components/primitives';
	import { CheckCircle2, XCircle, Clock, Terminal } from 'lucide-svelte';

	interface Props {
		items: ToolCallTimelineItem[];
	}

	let { items }: Props = $props();

	const statusConfig = {
		started: {
			variant: 'warning' as const,
			icon: Clock,
			label: 'Running'
		},
		finished: {
			variant: 'success' as const,
			icon: CheckCircle2,
			label: 'Done'
		},
		failed: {
			variant: 'danger' as const,
			icon: XCircle,
			label: 'Failed'
		}
	};
</script>

{#if items.length === 0}
	<div class="flex flex-col items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-border/70 bg-[hsl(var(--color-surface-2)/0.5)] py-8 text-center">
		<Terminal class="mb-3 h-10 w-10 text-muted-foreground/45" />
		<p class="text-sm text-muted-foreground">
			No tool calls yet. They will appear here while the agent investigates.
		</p>
	</div>
{:else}
	<div class="space-y-2">
		{#each items as item (item.toolName + item.timestamp)}
			<Card padding="sm" variant="subtle" class="relative overflow-hidden transition-all hover:border-border">
				{@const config = statusConfig[item.status]}
				<div class="absolute top-0 bottom-0 left-0 w-1 bg-[hsl(var(--color-primary)/0.18)]"></div>
				<div class="flex items-center justify-between gap-3">
					<div class="flex items-center gap-3 overflow-hidden pl-2">
						<Terminal class="h-4 w-4 shrink-0 text-muted-foreground/60" />
						<p class="truncate text-sm font-medium text-foreground" title={item.toolName}>
							{item.toolName}
						</p>
					</div>
					<Badge variant={config.variant} size="sm">
						<config.icon class="h-3 w-3" />
						{config.label}
					</Badge>
				</div>
				{#if item.durationMs}
					<p class="mt-2 pl-2 text-xs text-muted-foreground tabular-nums">{item.durationMs}ms</p>
				{/if}
			</Card>
		{/each}
	</div>
{/if}
