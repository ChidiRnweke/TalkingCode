<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Code2, Plus } from 'lucide-svelte';
	import { chatStore } from '$lib/stores';
	import { goto } from '$app/navigation';

	interface Props {
		phase?: string;
		currentPath?: string;
	}

	let { phase = 'idle', currentPath = '/' }: Props = $props();

	function handleNewChat() {
		chatStore.clear();
		goto('/chat');
	}
</script>

<header
	class="sticky top-0 z-50 flex h-14 items-center justify-between border-b border-border bg-background/80 px-[var(--page-padding)] backdrop-blur-md"
>
	<a href="/" class="flex items-center gap-3 transition-opacity hover:opacity-80">
		<Code2 class="h-5 w-5 text-primary" />
		<div class="flex items-baseline gap-2">
			<h1 class="font-display text-lg font-semibold tracking-tight text-foreground">TalkingCode</h1>
			<span class="text-xs text-muted-foreground hidden sm:inline">Chat with Chidi's code</span>
		</div>
	</a>

	<div class="flex items-center gap-3">
		<nav class="flex items-center gap-1">
			<a
				href="/about"
				class={`rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors ${
					currentPath === '/about'
						? 'bg-primary/10 text-primary'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				About
			</a>
			<a
				href="/repos"
				class={`rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors ${
					currentPath === '/repos'
						? 'bg-primary/10 text-primary'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				Repos
			</a>
			<a
				href="/chat"
				class={`rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors ${
					currentPath === '/chat'
						? 'bg-primary/10 text-primary'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				Chat
			</a>
		</nav>

		<div class="h-4 w-[1px] bg-border mx-1"></div>

		<Button variant="ghost" size="sm" class="gap-1.5 h-8 text-xs" onclick={handleNewChat}>
			<Plus class="h-3.5 w-3.5" />
			<span>New Chat</span>
		</Button>

		{#if phase && phase !== 'idle'}
			<Badge variant="secondary" class="text-[10px] px-1.5 h-5">{phase}</Badge>
		{/if}
	</div>
</header>
