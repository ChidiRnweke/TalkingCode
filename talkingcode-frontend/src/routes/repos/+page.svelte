<script lang="ts">
	import { EmptyState } from '$lib/components/layout';
	import { RepoCard } from '$lib/components/domain';
	import type { IngestionRunView, RepositoryView } from '$lib/models';

	interface Props {
		data: {
			repos: RepositoryView[];
			runsByRepo: Record<string, Promise<IngestionRunView[]> | IngestionRunView[]>;
		};
	}

	let { data }: Props = $props();
</script>

<main class="flex-1 overflow-y-auto px-[var(--page-padding)] py-8">
	<div class="mx-auto max-w-3xl">
		<div class="mb-3 flex items-center justify-between">
			<h1 class="font-display text-2xl font-semibold tracking-tight text-foreground">Repositories</h1>
		</div>
		<p class="mb-6 text-sm text-muted-foreground">
			Syncing is fully automated. The date shown on each repository is the last successful automated run.
		</p>

		{#if data.repos.length === 0}
			<EmptyState
				title="No repositories tracked"
				description="Repositories must be registered by an administrator."
			/>
		{:else}
			<div class="grid gap-4">
				{#each data.repos as repo (repo.id)}
					<RepoCard {repo} historyRuns={data.runsByRepo[repo.id] ?? []} />
				{/each}
			</div>
		{/if}
	</div>
</main>
