<script lang="ts">
	import { Loader, Check, X, Clock } from 'lucide-svelte';
	import type { ToolSegment } from '$lib/utils/assistantTags';

	interface Props {
		tool: ToolSegment;
	}

	let { tool }: Props = $props();

	const toolName = $derived(
		tool.name
			.split('_')
			.filter(Boolean)
			.map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
			.join(' ')
	);

	const primary = $derived.by((): { keys: string[]; text: string | null } => {
		const query = tool.args.query;
		if (typeof query === 'string' && query.trim()) {
			return { keys: ['query'], text: query.trim() };
		}

		const repository = tool.args.repository;
		const filePath = tool.args.file_path;
		if (typeof repository === 'string' && typeof filePath === 'string') {
			return { keys: ['repository', 'file_path'], text: `${repository}/${filePath}` };
		}

		return { keys: [], text: null };
	});

	const extraArgs = $derived(
		Object.entries(tool.args)
			.filter(([key, value]) => !primary.keys.includes(key) && value !== '' && value != null)
			.map(([key, value]) => `${key}: ${typeof value === 'string' ? value : JSON.stringify(value)}`)
			.join('  ·  ')
	);
</script>

<div class="min-w-0 text-sm {tool.status === 'error' ? 'text-destructive' : 'text-muted-foreground'}">
	<div class="flex min-w-0 items-baseline gap-2">
		<span class="flex size-3.5 shrink-0 items-center self-center">
			{#if tool.status === 'running'}
				<Loader class="size-3.5 animate-spin text-primary" />
			{:else if tool.status === 'done'}
				<Check class="size-3.5 text-success" />
			{:else if tool.status === 'error'}
				<X class="size-3.5 text-destructive" />
			{:else}
				<Clock class="size-3.5 text-muted-foreground/70" />
			{/if}
		</span>

		<span class="shrink-0 font-medium text-foreground/75">{toolName}</span>

		{#if primary.text}
			<span class="min-w-0 truncate text-muted-foreground">{primary.text}</span>
		{/if}
	</div>

	{#if extraArgs}
		<p class="ml-[22px] mt-0.5 min-w-0 font-mono text-xs text-muted-foreground/70 wrap-anywhere">
			{extraArgs}
		</p>
	{/if}
</div>
