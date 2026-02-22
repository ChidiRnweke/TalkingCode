<script lang="ts">
	import HeroComposer from '$lib/components/domain/HeroComposer.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { GitBranch, MessageSquare, Search, Zap } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	let showStickyBar = $state(false);
	let heroRef = $state<HTMLElement | null>(null);

	onMount(() => {
		if (!heroRef) return;
		
		const observer = new IntersectionObserver(
			([entry]) => {
				showStickyBar = !entry.isIntersecting;
			},
			{ threshold: 0.1 }
		);

		observer.observe(heroRef);
		return () => observer.disconnect();
	});
</script>

<main class="flex-1 flex flex-col bg-background">
	<!-- Hero Section -->
	<section 
		bind:this={heroRef}
		class="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden"
	>
		<!-- Background Accents -->
		<div class="absolute top-1/4 -left-20 w-80 h-80 bg-primary/5 rounded-full blur-3xl"></div>
		<div class="absolute bottom-1/4 -right-20 w-96 h-96 bg-accent/5 rounded-full blur-3xl"></div>

		<div class="max-w-4xl w-full space-y-12 relative z-10">
			<div class="space-y-8 text-center md:text-left">
				<div class="space-y-4">
					<p class="font-display text-2xl md:text-3xl font-medium text-primary italic">
						Hi, I'm Chidi 👋
					</p>
					<h2 class="font-display text-4xl md:text-7xl font-bold tracking-tight text-foreground uppercase leading-[1.1]">
						I built this to share <br class="hidden md:block" /> what I've learned.
					</h2>
					<div class="h-1.5 w-32 bg-primary mx-auto md:mx-0"></div>
				</div>
				
				<div class="max-w-2xl space-y-6">
					<p class="text-lg md:text-xl text-foreground/70 leading-relaxed font-medium">
						I’ve been exploring agentic AI for a while now, mostly out of a deep curiosity for how we can make 
						software more helpful. <strong>TalkingCode</strong> is a project I built to share some of the 
						state-of-the-art techniques I’ve picked up along the way, and to give you a chance to 
						get to know me through the code I write.
					</p>
				</div>
			</div>

			<HeroComposer />
		</div>
		
		<div class="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce opacity-40">
			<span class="text-[10px] uppercase tracking-widest font-bold">Explore the techniques</span>
			<div class="w-[1px] h-8 bg-foreground"></div>
		</div>
	</section>

	<!-- Capabilities Section -->
	<section class="py-24 px-6 bg-surface-2 border-y border-border/40">
		<div class="max-w-5xl mx-auto">
			<div class="grid md:grid-cols-2 gap-16 items-center">
				<div class="space-y-8">
					<h3 class="font-display text-4xl md:text-5xl font-bold tracking-tight uppercase leading-none">
						Learning <br /> <span class="text-primary">In Public.</span>
					</h3>
					<p class="text-lg text-foreground/70 leading-relaxed">
						This agent is a sandbox for the techniques I find most interesting: multi-step reasoning, 
						precise tool calling, and structural context. I’m sharing them here so we can see how they 
						perform on real-world repository structures.
					</p>
					
					<div class="space-y-6">
						<div class="flex gap-4">
							<div class="bg-primary/10 p-2 h-fit rounded-lg">
								<Search class="size-5 text-primary" />
							</div>
							<div>
								<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Contextual Retrieval</h4>
								<p class="text-sm text-muted-foreground">My attempt at making search feel more like how an engineer actually reads a codebase.</p>
							</div>
						</div>
						<div class="flex gap-4">
							<div class="bg-primary/10 p-2 h-fit rounded-lg">
								<Zap class="size-5 text-primary" />
							</div>
							<div>
								<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Thoughtful Planning</h4>
								<p class="text-sm text-muted-foreground">Using agentic loops to plan investigations before jumping to conclusions.</p>
							</div>
						</div>
					</div>
				</div>
				
				<div class="grid grid-cols-2 gap-4">
					<div class="aspect-square bg-background rounded-3xl border border-border shadow-sm p-6 flex flex-col justify-between">
						<GitBranch class="size-8 text-primary/40" />
						<div>
							<span class="text-2xl font-bold font-display">Curiosity</span>
							<p class="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Driven by Research</p>
						</div>
					</div>
					<div class="aspect-square bg-primary text-primary-foreground rounded-3xl shadow-xl p-6 flex flex-col justify-between transform translate-y-8">
						<MessageSquare class="size-8 opacity-40" />
						<div>
							<span class="text-2xl font-bold font-display">Shared</span>
							<p class="text-[10px] uppercase tracking-widest font-bold opacity-70">Techniques & Patterns</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- How it Works -->
	<section class="py-32 px-6">
		<div class="max-w-4xl mx-auto space-y-20">
			<div class="text-center space-y-4">
				<h3 class="font-display text-4xl md:text-6xl font-bold tracking-tight uppercase">How It Works</h3>
				<p class="text-muted-foreground uppercase tracking-widest text-sm font-bold">The Process Behind the Agent</p>
			</div>

			<div class="grid md:grid-cols-3 gap-12 relative">
				<div class="absolute top-1/2 left-0 right-0 h-[1px] bg-border hidden md:block"></div>
				
				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-foreground text-background flex items-center justify-center rounded-full font-bold text-lg">1</div>
					<h4 class="font-bold uppercase tracking-widest text-sm">Understanding</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						We index repositories by preserving the structural hierarchy, making it easier for the AI to "see" the code.
					</p>
				</div>

				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-primary text-primary-foreground flex items-center justify-center rounded-full font-bold text-lg">2</div>
					<h4 class="font-bold uppercase tracking-widest text-sm text-primary">Reasoning</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						Instead of a direct search, the agent takes a moment to plan which parts of the code are most relevant to your question.
					</p>
				</div>

				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-foreground text-background flex items-center justify-center rounded-full font-bold text-lg">3</div>
					<h4 class="font-bold uppercase tracking-widest text-sm">Sharing</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						The final answer includes citations, so you can see exactly which files and logic the agent used to reach its conclusion.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Final CTA -->
	<section class="py-24 px-6 border-t border-border/40 text-center space-y-12">
		<div class="max-w-2xl mx-auto space-y-6">
			<h3 class="font-display text-4xl font-bold uppercase tracking-tight text-primary">Let's talk code.</h3>
			<p class="text-lg text-foreground/70 leading-relaxed font-medium">
				I’m always happy to talk about architecture, patterns, or the techniques used here. 
				Feel free to explore and see how it works.
			</p>
			<a 
				href="/chat" 
				class="inline-block bg-primary text-primary-foreground px-12 py-4 rounded-full font-bold uppercase tracking-[0.2em] text-xs hover:scale-105 transition-transform shadow-xl"
			>
				Start a Conversation
			</a>
		</div>
		<footer class="pt-24 text-[10px] text-muted-foreground uppercase tracking-[0.3em] font-bold">
			&copy; {new Date().getFullYear()} Chidi Nweke. Learning and sharing.
		</footer>
	</section>

	<!-- Sticky Chat Bar -->
	{#if showStickyBar}
		<div 
			transition:fly={{ y: 50, duration: 300 }}
			class="fixed bottom-0 left-0 right-0 z-50 p-4 pointer-events-none"
		>
			<div class="mx-auto max-w-2xl w-full pointer-events-auto">
				<div class="bg-background/80 backdrop-blur-xl border border-border/60 shadow-2xl rounded-2xl p-2">
					<HeroComposer compact />
				</div>
			</div>
		</div>
	{/if}
</main>

<style>
	:global(body) {
		scroll-behavior: smooth;
	}
</style>
