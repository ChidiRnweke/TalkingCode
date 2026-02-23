<script lang="ts">
	import { enhance } from '$app/forms';
	import { EmptyState } from '$lib/components/layout';
	import { RepoCard } from '$lib/components/domain';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import type { RepositoryInfo } from '$lib/models';

	interface Props {
		data: {
			repos: RepositoryInfo[];
		};
	}

	let { data }: Props = $props();
	let syncing = $state(false);
	let registering = $state(false);
	let ingestingRepo = $state<string | null>(null);
</script>

<main class="flex-1 overflow-y-auto px-[var(--page-padding)] py-8">
	<div class="mx-auto max-w-3xl">
		<div class="mb-8 flex items-center justify-between">
			<h1 class="font-display text-2xl font-semibold tracking-tight text-foreground">Repositories</h1>
			<form
				method="POST"
				action="?/ingestOwned"
				use:enhance={() => {
					syncing = true;
					return async ({ update }) => {
						await update();
						syncing = false;
					};
				}}
			>
				<Button variant="outline" size="sm" disabled={syncing}>
					{syncing ? 'Syncing...' : 'Sync Owned Repos'}
				</Button>
			</form>
		</div>

		<form
			method="POST"
			action="?/register"
			class="mb-6 grid gap-3 rounded-[var(--radius-lg)] border border-border bg-[hsl(var(--color-surface-2))] p-[var(--card-padding)] md:grid-cols-[1fr_1fr_180px_auto]"
			use:enhance={() => {
				registering = true;
				return async ({ update }) => {
					await update();
					registering = false;
				};
			}}
		>
			<Input name="owner" placeholder="Owner (e.g. chidinweke)" required />
			<Input name="name" placeholder="Repository name" required />
			<Input name="defaultBranch" placeholder="Default branch" value="main" />
			<Button type="submit" disabled={registering}>{registering ? 'Registering...' : 'Register'}</Button>
		</form>

		{#if data.repos.length === 0}
			<EmptyState
				title="No repositories tracked"
				description="Repositories must be registered by an administrator."
			/>
		{:else}
			<div class="grid gap-4">
				{#each data.repos as repo (repo.id)}
					<div class="space-y-2">
						<form
							method="POST"
							action="?/ingest"
							class="flex justify-end"
							use:enhance={() => {
								ingestingRepo = repo.id;
								return async ({ update }) => {
									await update();
									ingestingRepo = null;
								};
							}}
						>
							<input type="hidden" name="owner" value={repo.owner} />
							<input type="hidden" name="name" value={repo.name} />
							<Button type="submit" size="sm" variant="outline" disabled={ingestingRepo === repo.id}>
								{ingestingRepo === repo.id ? 'Starting ingest...' : 'Ingest now'}
							</Button>
						</form>
						<RepoCard {repo} />
					</div>
				{/each}
			</div>
		{/if}
	</div>
</main>
