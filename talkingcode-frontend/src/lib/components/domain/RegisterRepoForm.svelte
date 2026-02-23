<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import type { RegisterRepoInput } from '$lib/models';

	interface Props {
		onRegister: (input: RegisterRepoInput) => void;
		loading: boolean;
	}

	let { onRegister, loading }: Props = $props();

	let owner = $state('');
	let name = $state('');
	let defaultBranch = $state('main');

	function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!owner.trim() || !name.trim()) {
			return;
		}
		onRegister({
			owner: owner.trim(),
			name: name.trim(),
			defaultBranch: defaultBranch.trim() || 'main'
		});
	}
</script>

<form
	onsubmit={handleSubmit}
	class="grid gap-3 rounded-[var(--radius-lg)] border border-border bg-[hsl(var(--color-surface-2))] p-[var(--card-padding)] md:grid-cols-[1fr_1fr_180px_auto]"
>
	<Input placeholder="Owner (e.g. chidinweke)" bind:value={owner} required />
	<Input placeholder="Repository name" bind:value={name} required />
	<Input placeholder="Default branch" bind:value={defaultBranch} />
	<Button type="submit" disabled={loading || !owner.trim() || !name.trim()}>
		{loading ? 'Registering...' : 'Register'}
	</Button>
</form>
