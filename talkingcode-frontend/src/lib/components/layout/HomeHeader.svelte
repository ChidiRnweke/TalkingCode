<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Code2 } from 'lucide-svelte';
	import { goto } from '$app/navigation';

	function handleGetStarted() {
		goto('/chat');
	}
</script>

<header
	class="flex h-20 items-center justify-between px-8 md:px-12 bg-transparent absolute top-0 left-0 right-0 z-50"
>
	<div class="flex items-center gap-3">
		<div class="bg-primary p-1.5 rounded-lg">
			<Code2 class="h-6 w-6 text-primary-foreground" />
		</div>
		<h1 class="font-display text-xl font-bold tracking-tight text-foreground uppercase">
			TalkingCode
		</h1>
	</div>

	<nav class="hidden md:flex items-center gap-8">
		<a href="/about" class="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors uppercase tracking-widest">About</a>
		<a href="/repos" class="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors uppercase tracking-widest">Repositories</a>
		<Button variant="default" size="sm" class="rounded-full px-6 uppercase tracking-widest text-[10px] font-bold" onclick={handleGetStarted}>
			Get Started
		</Button>
	</nav>
	
	<Button variant="ghost" size="icon" class="md:hidden">
		<Code2 class="h-6 w-6" />
	</Button>
</header>
