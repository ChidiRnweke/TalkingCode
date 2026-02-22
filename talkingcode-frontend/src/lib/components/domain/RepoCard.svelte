<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Github } from 'lucide-svelte';
	import type { RepositoryInfo } from '$lib/models';

	interface Props {
		repo: RepositoryInfo;
		onIngest: (owner: string, name: string) => void;
		ingesting: boolean;
	}

	let { repo, onIngest, ingesting }: Props = $props();

	function relativeLastIngested(timestamp: string | null): string {
		if (!timestamp) return 'Never ingested';
		const deltaMs = Date.now() - new Date(timestamp).getTime();
		if (deltaMs < 60_000) return 'Last ingested: just now';
		const minutes = Math.floor(deltaMs / 60_000);
		if (minutes < 60) return `Last ingested: ${minutes}m ago`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `Last ingested: ${hours}h ago`;
		const days = Math.floor(hours / 24);
		return `Last ingested: ${days}d ago`;
	}
</script>

<div class="rounded-[var(--radius-lg)] border border-border bg-[hsl(var(--color-surface-2))] p-[var(--card-padding)]">
	<div class="flex items-start justify-between gap-3">
		<div class="min-w-0">
			<div class="flex items-center gap-2">
				<Github class="h-4 w-4 text-muted-foreground" />
				<h3 class="truncate font-medium text-foreground">{repo.owner}/{repo.name}</h3>
			</div>
			<p class="mt-2 text-xs text-muted-foreground">{relativeLastIngested(repo.last_ingested_at)}</p>
		</div>
		<div class="flex items-center gap-2">
			<Badge variant="secondary">{repo.default_branch}</Badge>
			<Button
				variant="default"
				size="sm"
				disabled={ingesting}
				onclick={() => onIngest(repo.owner, repo.name)}
			>
				{ingesting ? 'Ingesting...' : 'Ingest now'}
			</Button>
		</div>
	</div>
</div>
