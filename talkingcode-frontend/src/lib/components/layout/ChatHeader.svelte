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
	class="sticky top-0 z-50 flex h-16 shrink-0 items-center justify-between border-b border-border/40 bg-background/80 px-8 md:px-12 backdrop-blur-md"
>
	<a href="/" class="flex items-center gap-3 transition-opacity hover:opacity-80">
		<div class="bg-primary p-1 rounded-md">
			<Code2 class="h-5 w-5 text-primary-foreground" />
		</div>
		<div class="flex flex-col">
			<h1 class="font-display text-base font-bold tracking-tight text-foreground uppercase leading-none">TalkingCode</h1>
			<span class="text-[9px] uppercase tracking-widest text-muted-foreground font-bold mt-1">by Chidi Nweke</span>
		</div>
	</a>

	<div class="flex items-center gap-6">
		<nav class="hidden md:flex items-center gap-6">
			<a
				href="/about"
				class={`text-[11px] font-bold uppercase tracking-widest transition-colors ${
					currentPath === '/about'
						? 'text-primary'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				About
			</a>
			<a
				href="/repos"
				class={`text-[11px] font-bold uppercase tracking-widest transition-colors ${
					currentPath === '/repos'
						? 'text-primary'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				Repos
			</a>
			<a
				href="/chat"
				class={`text-[11px] font-bold uppercase tracking-widest transition-colors ${
					currentPath === '/chat'
						? 'text-primary'
						: 'text-muted-foreground hover:text-foreground'
				}`}
			>
				Chat
			</a>
		</nav>

		<div class="hidden md:block h-4 w-[1px] bg-border mx-1"></div>

		<div class="flex items-center gap-3">
			<Button variant="ghost" size="sm" class="gap-1.5 h-8 text-[10px] uppercase tracking-widest font-bold" onclick={handleNewChat}>
				<Plus class="h-3.5 w-3.5" />
				<span class="hidden sm:inline">New Chat</span>
			</Button>

			{#if phase && phase !== 'idle'}
				<Badge variant="secondary" class="text-[9px] px-1.5 h-5 uppercase tracking-widest font-bold">{phase}</Badge>
			{/if}
		</div>
	</div>
</header>
