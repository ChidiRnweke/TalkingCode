<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Code2 } from 'lucide-svelte';

	interface Props {
		phase?: string;
		currentPath?: string;
	}

	let { phase = 'idle', currentPath = '/' }: Props = $props();
</script>

<header
	class="flex h-14 items-center justify-between border-b border-border bg-background px-[var(--page-padding)]"
>
	<div class="flex items-center gap-3">
		<Code2 class="h-5 w-5 text-primary" />
		<div class="flex items-baseline gap-2">
			<h1 class="font-display text-lg font-semibold tracking-tight text-foreground">TalkingCode</h1>
			<span class="text-xs text-muted-foreground">Chat with Chidi's code</span>
		</div>
	</div>

	<div class="flex items-center gap-3">
		<nav class="flex items-center gap-1">
			<a
				href="/"
				class={`rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors ${
					currentPath === '/'
						? 'bg-[hsl(var(--color-primary)/0.12)] text-foreground'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				Chat
			</a>
			<a
				href="/repos"
				class={`rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors ${
					currentPath === '/repos'
						? 'bg-[hsl(var(--color-primary)/0.12)] text-foreground'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				Repos
			</a>
		</nav>

		{#if phase && phase !== 'idle'}
			<Badge variant="secondary" class="text-xs">{phase}</Badge>
		{/if}
	</div>
</header>
