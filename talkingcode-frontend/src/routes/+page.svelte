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

		<div class="max-w-4xl w-full space-y-16 relative z-10">
			<div class="space-y-8 text-center md:text-left">
				<div class="space-y-4">
					<Badge variant="outline" class="uppercase tracking-[0.2em] text-[10px] px-3 py-1 font-bold border-primary/30 text-primary">
						Senior Software Engineer & Creator
					</Badge>
					<h2 class="font-display text-5xl md:text-8xl font-bold tracking-tight text-foreground uppercase leading-[0.9]">
						Chidi <br class="hidden md:block" /> Nweke
					</h2>
					<div class="h-2 w-48 bg-primary mx-auto md:mx-0"></div>
				</div>
				
				<div class="max-w-2xl space-y-6">
					<p class="font-display text-3xl md:text-4xl text-muted-foreground leading-tight italic">
						"I build systems that reason about systems."
					</p>
					
					<p class="text-lg md:text-xl text-foreground/70 leading-relaxed font-medium">
						This isn't just a chatbot. It's an agentic interface into my professional work, 
						designed to help you navigate architecture and complex logic with precision.
					</p>
				</div>
			</div>

			<HeroComposer />
		</div>
		
		<div class="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce opacity-40">
			<span class="text-[10px] uppercase tracking-widest font-bold">Scroll to explore</span>
			<div class="w-[1px] h-8 bg-foreground"></div>
		</div>
	</section>

	<!-- Capabilities Section -->
	<section class="py-24 px-6 bg-surface-2 border-y border-border/40">
		<div class="max-w-5xl mx-auto">
			<div class="grid md:grid-cols-2 gap-16 items-center">
				<div class="space-y-8">
					<h3 class="font-display text-4xl md:text-5xl font-bold tracking-tight uppercase leading-none">
						Engineered for <br /> <span class="text-primary">Deep Context.</span>
					</h3>
					<p class="text-lg text-foreground/70 leading-relaxed">
						Standard RAG often misses the nuances of software architecture. 
						I've built TalkingCode to understand relationships, not just keywords.
					</p>
					
					<div class="space-y-6">
						<div class="flex gap-4">
							<div class="bg-primary/10 p-2 h-fit rounded-lg">
								<Search class="size-5 text-primary" />
							</div>
							<div>
								<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Semantic Navigation</h4>
								<p class="text-sm text-muted-foreground">Find logic across microservices or complex monorepos using intent-based retrieval.</p>
							</div>
						</div>
						<div class="flex gap-4">
							<div class="bg-primary/10 p-2 h-fit rounded-lg">
								<Zap class="size-5 text-primary" />
							</div>
							<div>
								<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Agentic Planning</h4>
								<p class="text-sm text-muted-foreground">The agent plans multi-step investigations before summarizing its findings.</p>
							</div>
						</div>
					</div>
				</div>
				
				<div class="grid grid-cols-2 gap-4">
					<div class="aspect-square bg-background rounded-3xl border border-border shadow-sm p-6 flex flex-col justify-between">
						<GitBranch class="size-8 text-primary/40" />
						<div>
							<span class="text-2xl font-bold font-display">12+</span>
							<p class="text-[10px] uppercase tracking-widest font-bold text-muted-foreground">Active Repos</p>
						</div>
					</div>
					<div class="aspect-square bg-primary text-primary-foreground rounded-3xl shadow-xl p-6 flex flex-col justify-between transform translate-y-8">
						<MessageSquare class="size-8 opacity-40" />
						<div>
							<span class="text-2xl font-bold font-display">Fast</span>
							<p class="text-[10px] uppercase tracking-widest font-bold opacity-70">Streaming Response</p>
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
				<p class="text-muted-foreground uppercase tracking-widest text-sm font-bold">The Journey from Query to Insight</p>
			</div>

			<div class="grid md:grid-cols-3 gap-12 relative">
				<div class="absolute top-1/2 left-0 right-0 h-[1px] bg-border hidden md:block"></div>
				
				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-foreground text-background flex items-center justify-center rounded-full font-bold text-lg">1</div>
					<h4 class="font-bold uppercase tracking-widest text-sm">Ingest</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						I index my repositories into a specialized vector store with rich structural metadata.
					</p>
				</div>

				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-primary text-primary-foreground flex items-center justify-center rounded-full font-bold text-lg">2</div>
					<h4 class="font-bold uppercase tracking-widest text-sm text-primary">Reason</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						The agent analyzes your query and plans a multi-step retrieval strategy across relevant files.
					</p>
				</div>

				<div class="relative bg-background p-6 space-y-4 z-10 border border-border/60 rounded-2xl shadow-sm">
					<div class="size-10 bg-foreground text-background flex items-center justify-center rounded-full font-bold text-lg">3</div>
					<h4 class="font-bold uppercase tracking-widest text-sm">Deliver</h4>
					<p class="text-sm text-muted-foreground leading-relaxed">
						Findings are presented with citations, explaining the "why" behind the code architecture.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Final CTA -->
	<section class="py-24 px-6 border-t border-border/40 text-center space-y-12">
		<div class="max-w-2xl mx-auto space-y-6">
			<h3 class="font-display text-4xl font-bold uppercase tracking-tight">Ready to explore?</h3>
			<p class="text-lg text-foreground/70 leading-relaxed">
				Dive into the pipelines, the patterns, and the decisions that shape my work.
			</p>
			<a 
				href="/chat" 
				class="inline-block bg-primary text-primary-foreground px-12 py-4 rounded-full font-bold uppercase tracking-[0.2em] text-xs hover:scale-105 transition-transform shadow-xl"
			>
				Start a Conversation
			</a>
		</div>
		<footer class="pt-24 text-[10px] text-muted-foreground uppercase tracking-[0.3em] font-bold">
			&copy; {new Date().getFullYear()} Chidi Nweke. All rights reserved.
		</footer>
	</section>
</main>

<style>
	:global(body) {
		scroll-behavior: smooth;
	}
</style>
