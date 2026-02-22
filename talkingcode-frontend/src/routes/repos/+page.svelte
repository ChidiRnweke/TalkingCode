<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { ChatLayout, ChatHeader, EmptyState } from '$lib/components/layout';
	import { RepoCard, RegisterRepoForm } from '$lib/components/domain';
	import { RepoService } from '$lib/services/RepoService';
	import type { RegisterRepoInput, RepositoryInfo } from '$lib/models';

	interface Props {
		data: {
			repos: RepositoryInfo[];
		};
	}

	let { data }: Props = $props();

	const repoService = new RepoService();
	let repos = $state<RepositoryInfo[]>(data.repos || []);
	let ingestingRepos = $state<Set<string>>(new Set());
	let registering = $state(false);
	let showRegisterForm = $state(false);

	async function handleRegister(input: RegisterRepoInput) {
		registering = true;
		try {
			const repo = await repoService.registerRepo(input);
			repos = [repo, ...repos.filter((r) => r.id !== repo.id)];
			showRegisterForm = false;
		} catch (err) {
			console.error(err);
		} finally {
			registering = false;
		}
	}

	async function handleIngest(owner: string, name: string) {
		const key = `${owner}/${name}`;
		ingestingRepos.add(key);
		ingestingRepos = new Set(ingestingRepos);
		try {
			await repoService.startIngestion(owner, name);
			repos = await repoService.listRepos();
		} catch (err) {
			console.error(err);
		} finally {
			ingestingRepos.delete(key);
			ingestingRepos = new Set(ingestingRepos);
		}
	}
</script>

<ChatLayout>
	<ChatHeader currentPath="/repos" />

	<main class="flex-1 overflow-y-auto px-[var(--page-padding)] py-8">
		<div class="mx-auto max-w-3xl">
			<div class="mb-8 flex items-center justify-between">
				<h1 class="font-display text-2xl font-semibold tracking-tight text-foreground">Repositories</h1>
				<Button onclick={() => (showRegisterForm = !showRegisterForm)}>
					{showRegisterForm ? 'Cancel' : 'Register repo'}
				</Button>
			</div>

			{#if showRegisterForm}
				<div class="mb-8">
					<RegisterRepoForm onRegister={handleRegister} loading={registering} />
				</div>
			{/if}

			{#if repos.length === 0}
				<EmptyState
					title="No repositories tracked"
					description="Register a GitHub repository to start indexing its code for chat."
				/>
			{:else}
				<div class="grid gap-4">
					{#each repos as repo (repo.id)}
						<RepoCard
							{repo}
							onIngest={handleIngest}
							ingesting={ingestingRepos.has(`${repo.owner}/${repo.name}`)}
						/>
					{/each}
				</div>
			{/if}
		</div>
	</main>
</ChatLayout>
