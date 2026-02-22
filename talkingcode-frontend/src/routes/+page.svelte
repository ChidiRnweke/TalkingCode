<script lang="ts">
	import HeroComposer from '$lib/components/domain/HeroComposer.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { GitBranch, MessageSquare, Search, Zap } from 'lucide-svelte';
</script>

<main class="flex-1 flex flex-col bg-background">
	<!-- Hero Section -->
	<section class="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden">
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
						I've been building agentic AI <br class="hidden md:block" /> before it was a buzzword.
					</h2>
					<div class="h-1.5 w-32 bg-primary mx-auto md:mx-0"></div>
				</div>
				
				<div class="max-w-2xl space-y-6">
					<p class="text-lg md:text-xl text-foreground/70 leading-relaxed font-medium">
						I’ve spent years exploring the intersection of machine learning and software engineering. 
						I built <strong>TalkingCode</strong> to share the state-of-the-art techniques I use daily—helping 
						engineers navigate complex architectures with the same precision I strive for in my own work.
					</p>
				</div>
			</div>

			<HeroComposer />
		</div>
		
		<div class="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce opacity-40">
			<span class="text-[10px] uppercase tracking-widest font-bold">Explore the tech</span>
			<div class="w-[1px] h-8 bg-foreground"></div>
		</div>
	</section>

	<!-- Capabilities Section -->
	<section class="py-24 px-6 bg-surface-2 border-y border-border/40">
		<div class="max-w-5xl mx-auto">
			<div class="grid md:grid-cols-2 gap-16 items-center">
				<div class="space-y-8">
					<h3 class="font-display text-4xl md:text-5xl font-bold tracking-tight uppercase leading-none">
						Sharing <br /> <span class="text-primary">SOTA Patterns.</span>
					</h3>
					<p class="text-lg text-foreground/70 leading-relaxed">
						This agent isn't just for searching code. It's a demonstration of multi-step reasoning, 
						precise tool calling, and structural context—techniques I believe are the future of how we interact with software.
					</p>
					
					<div class="space-y-6">
						<div class="flex gap-4">
							<div class="bg-primary/10 p-2 h-fit rounded-lg">
								<Search class="size-5 text-primary" />
							</div>
							<div>
								<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Architectural Awareness</h4>
								<p class="text-sm text-muted-foreground">Moving beyond simple text search to understand how modules and services actually connect.</p>
							</div>
						</div>
						<div class="flex gap-4">
							<div class="bg-primary/10 p-2 h-fit rounded-lg">
								<Zap class="size-5 text-primary" />
							</div>
							<div>
								<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Reasoning Loops</h4>
								<p class="text-sm text-muted-foreground">The same agentic loops used in production environments, now applied to my own repositories.</p>
							</div>
						</div>
					</div>
				</div>
				
				<div class="grid grid-cols-2 gap-4">
					<div class="aspect-square bg-background rounded-3xl border border-border shadow-sm p-6 flex flex-col justify-between">
						<GitBranch class="size-8 text-primary/40" />
						<div>
							<span class="text-2xl font-bold font-display">Transparent</span>
							<p class="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Open Architecture</p>
						</div>
					</div>
					<div class="aspect-square bg-primary text-primary-foreground rounded-3xl shadow-xl p-6 flex flex-col justify-between transform translate-y-8">
						<MessageSquare class="size-8 opacity-40" />
						<div>
							<span class="text-2xl font-bold font-display">Honest</span>
							<p class="text-[10px] uppercase tracking-widest font-bold opacity-70">Citations Mandatory</p>
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
				<p class="text-muted-foreground uppercase tracking-widest text-sm font-bold">The Research & Strategy Loop</p>
			</div>

			<div class="grid md:grid-cols-3 gap-12 relative">
				<div class="absolute top-1/2 left-0 right-0 h-[1px] bg-border hidden md:block"></div>
				
				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-foreground text-background flex items-center justify-center rounded-full font-bold text-lg">1</div>
					<h4 class="font-bold uppercase tracking-widest text-sm">Semantic Ingest</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						Repositories are transformed into a dense vector space, preserving the structural hierarchy of the code.
					</p>
				</div>

				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-primary text-primary-foreground flex items-center justify-center rounded-full font-bold text-lg">2</div>
					<h4 class="font-bold uppercase tracking-widest text-sm text-primary">Multi-Step Plan</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						The agent doesn't guess. It plans a sequence of tool calls to gather evidence before answering.
					</p>
				</div>

				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-foreground text-background flex items-center justify-center rounded-full font-bold text-lg">3</div>
					<h4 class="font-bold uppercase tracking-widest text-sm">Grounded Answer</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						Responses are built from retrieved snippets, with explicit citations to ensure technical accuracy.
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
				I built this to be explored. Ask me about the architecture of this agent, or any of my other projects.
			</p>
			<a 
				href="/chat" 
				class="inline-block bg-primary text-primary-foreground px-12 py-4 rounded-full font-bold uppercase tracking-[0.2em] text-xs hover:scale-105 transition-transform shadow-xl"
			>
				Start a Conversation
			</a>
		</div>
		<footer class="pt-24 text-[10px] text-muted-foreground uppercase tracking-[0.3em] font-bold">
			&copy; {new Date().getFullYear()} Chidi Nweke. Sharing what I learn.
		</footer>
	</section>
</main>

<style>
	:global(body) {
		scroll-behavior: smooth;
	}
</style>
