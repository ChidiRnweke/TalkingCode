<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Github } from 'lucide-svelte';
	import type { IngestionRunInfo, RepositoryInfo } from '$lib/models';
	import IngestionHistory from './IngestionHistory.svelte';

	interface Props {
		repo: RepositoryInfo;
		historyRuns: IngestionRunInfo[] | Promise<IngestionRunInfo[]>;
	}

	let { repo, historyRuns }: Props = $props();
	let showHistory = $state(false);

	function relativeLastIngested(timestamp: string | null): string {
		if (!timestamp) return 'Last automated sync: not run yet';
		const deltaMs = Date.now() - new Date(timestamp).getTime();
		if (deltaMs < 60_000) return 'Last automated sync: just now';
		const minutes = Math.floor(deltaMs / 60_000);
		if (minutes < 60) return `Last automated sync: ${minutes}m ago`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `Last automated sync: ${hours}h ago`;
		const days = Math.floor(hours / 24);
		return `Last automated sync: ${days}d ago`;
	}

	function toggleHistory() {
		if (showHistory) {
			showHistory = false;
			return;
		}

		showHistory = true;
	}
</script>

<div class="rounded-[var(--radius-lg)] border border-border bg-[hsl(var(--color-surface-2))] p-[var(--card-padding)]">
	<div class="flex items-start justify-between gap-3">
		<div class="min-w-0">
			<div class="flex items-center gap-2">
				<Github class="h-4 w-4 text-muted-foreground" />
				<h3 class="truncate font-display font-medium tracking-tight text-foreground">
					{repo.owner}/{repo.name}
				</h3>
			</div>
			<p class="mt-2 text-xs text-muted-foreground">{relativeLastIngested(repo.last_ingested_at)}</p>
		</div>
		<div class="flex items-center gap-2">
			<Badge variant="secondary">{repo.default_branch}</Badge>
			<Button variant="outline" size="sm" onclick={toggleHistory}>
				{showHistory ? 'Hide history' : 'Show history'}
			</Button>
		</div>
	</div>

	{#if showHistory}
		{#await historyRuns}
			<p class="mt-3 text-sm text-muted-foreground">Loading ingestion history...</p>
		{:then runs}
			<IngestionHistory {runs} />
		{:catch}
			<IngestionHistory runs={[]} />
		{/await}
	{/if}
</div>
