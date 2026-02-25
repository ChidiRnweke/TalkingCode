<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import type { IngestionRunView } from '$lib/models';

	interface Props {
		runs: IngestionRunView[];
	}

	let { runs }: Props = $props();

	function formatDuration(startedAt: string, completedAt: string | null): string | null {
		if (!completedAt) return null;
		const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
		if (!Number.isFinite(ms) || ms < 0) return null;
		const seconds = Math.round(ms / 1000);
		if (seconds < 60) return `${seconds}s`;
		const minutes = Math.floor(seconds / 60);
		const remSeconds = seconds % 60;
		return `${minutes}m ${remSeconds}s`;
	}

	function statusVariant(status: IngestionRunView['status']): 'default' | 'secondary' | 'destructive' {
		if (status === 'done') return 'default';
		if (status === 'failed') return 'destructive';
		return 'secondary';
	}
</script>

<div class="mt-3 space-y-2 rounded-[var(--radius-md)] border border-border bg-[hsl(var(--color-surface-2))] p-3">
	{#if runs.length === 0}
		<p class="text-sm text-muted-foreground">No ingestion runs yet.</p>
	{:else}
		{#each runs as run (run.id)}
			<div class="rounded-[var(--radius-md)] border border-border/70 bg-background/70 p-3">
				<div class="flex items-center justify-between gap-2">
					<Badge variant={statusVariant(run.status)}>{run.status}</Badge>
					<span class="text-xs text-muted-foreground">
						{new Date(run.startedAt).toLocaleString()}
					</span>
				</div>
				{#if formatDuration(run.startedAt, run.completedAt)}
					<p class="mt-2 text-xs text-muted-foreground">
						Duration: {formatDuration(run.startedAt, run.completedAt)}
					</p>
				{/if}
				{#if run.errorMessage}
					<p class="mt-2 line-clamp-2 text-xs text-destructive">{run.errorMessage}</p>
				{/if}
			</div>
		{/each}
	{/if}
</div>
