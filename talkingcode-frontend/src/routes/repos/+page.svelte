<script lang="ts">
	import { EmptyState } from '$lib/components/layout';
	import { RepoCard } from '$lib/components/domain';
	import type { RepositoryInfo } from '$lib/models';

	interface Props {
		data: {
			repos: RepositoryInfo[];
		};
	}

	let { data }: Props = $props();

	let repos = $state<RepositoryInfo[]>(data.repos || []);
</script>

<main class="flex-1 overflow-y-auto px-[var(--page-padding)] py-8">
	<div class="mx-auto max-w-3xl">
		<div class="mb-8 flex items-center justify-between">
			<h1 class="font-display text-2xl font-semibold tracking-tight text-foreground">Repositories</h1>
		</div>

		{#if repos.length === 0}
			<EmptyState
				title="No repositories tracked"
				description="Repositories must be registered by an administrator."
			/>
		{:else}
			<div class="grid gap-4">
				{#each repos as repo (repo.id)}
					<RepoCard {repo} />
				{/each}
			</div>
		{/if}
	</div>
</main>
