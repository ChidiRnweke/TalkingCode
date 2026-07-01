<script lang="ts">
	import { Container } from '$lib/components/layout';
</script>

<main class="flex-1 overflow-y-auto bg-background selection:bg-primary/10">
	<Container>
		<article class="mx-auto max-w-2xl px-6 py-20 md:py-32 space-y-16">
		<header class="space-y-6 text-center">
			<h1 class="font-display text-4xl md:text-5xl font-bold tracking-tight text-foreground">
				Exploring <br /> Agentic Techniques
			</h1>
			<p class="text-muted-foreground text-lg md:text-xl font-medium italic">
				A look at the patterns I’ve been learning and refining.
			</p>
		</header>

		<div class="h-px w-1/4 sm:w-1/5 lg:w-1/6 bg-border mx-auto"></div>

		<section class="space-y-6">
			<p class="text-foreground/80 leading-relaxed text-lg">
				Hi, I'm Chidi 👋. I’ve been working with GenAI for the past years, both professionally 
				and as a hobby. I believe that the future of software development 
				lies in systems that don't just search, but <em>reason</em> alongside us.
			</p>
			<p class="text-foreground/80 leading-relaxed">
				I built TalkingCode to share some of the state-of-the-art techniques I've been 
				learning and refining in my daily work. My goal here is transparency: 
				I want to share exactly how these loops work, from planning to execution, 
				as a way for us to learn together.
			</p>
		</section>

		<section class="space-y-12 pt-8">
			<div class="space-y-4">
				<h2 class="font-display text-2xl font-bold text-foreground">Multi-step Reasoning</h2>
				<p class="text-foreground/80 leading-relaxed">
					The heart of this project lies in the planning phase. Rather than a linear search, 
					the agent uses multi-step reasoning to decompose your request. It treats the 
					underlying codebase as a structured dataset, deciding which tools and "research" 
					steps are necessary to build a complete answer.
				</p>
			</div>

			<div class="space-y-4">
				<h2 class="font-display text-2xl font-bold text-foreground">Grounded Tool Calling</h2>
				<p class="text-foreground/80 leading-relaxed">
					To ensure the agentic loops stay grounded, I've provided the system with direct access 
					to the raw data of my repositories. This includes semantic search for context 
					and git-level metadata to understand the history and evolution of the code.
				</p>
			</div>

			<div class="space-y-4">
				<h2 class="font-display text-2xl font-bold text-foreground">Dataset Precision</h2>
				<p class="text-foreground/80 leading-relaxed">
					By treating GitHub as a high-fidelity dataset, we can use metadata filtering to 
					provide the precision required for complex reasoning. The agent narrows its 
					focus before retrieval, ensuring the reasoning engine works with the most 
					relevant "facts" from my work.
				</p>
				<div class="grid grid-cols-2 gap-4 pt-2">
					<div class="p-4 rounded-lg bg-surface-2 border border-border/60">
						<span class="text-xs font-bold uppercase tracking-wider text-primary">Structural</span>
						<p class="text-sm mt-1">Filtering by file types, paths, and repository scopes.</p>
					</div>
					<div class="p-4 rounded-lg bg-surface-2 border border-border/60">
						<span class="text-xs font-bold uppercase tracking-wider text-primary">Contextual</span>
						<p class="text-sm mt-1">Filtering by language features, symbol hints, and tags.</p>
					</div>
				</div>
				<p class="text-foreground/80 leading-relaxed pt-2">
					By narrowing the search space before retrieval, we achieve higher accuracy and 
					lower latency, ensuring the LLM only sees the most relevant snippets of my code.
				</p>
			</div>
		</section>

		<footer class="pt-16 border-t border-border/40 text-center">
			<p class="text-sm text-muted-foreground italic">
				"Building systems that reason about systems."
			</p>
		</footer>
	</article>
	</Container>
</main>
