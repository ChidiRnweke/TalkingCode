<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
</script>

<main class="flex-1 overflow-y-auto bg-background selection:bg-primary/10">
	<article class="mx-auto max-w-2xl px-6 py-20 md:py-32 space-y-16">
		<header class="space-y-6 text-center">
			<Badge variant="outline" class="uppercase tracking-widest text-[10px] px-3 py-1">Technical Deep Dive</Badge>
			<h1 class="font-display text-4xl md:text-5xl font-bold tracking-tight text-foreground">
				Exploring <br /> Agentic Techniques
			</h1>
			<p class="text-muted-foreground text-lg md:text-xl font-medium italic">
				A look at the patterns I’ve been learning and refining.
			</p>
		</header>

		<div class="h-[1px] w-24 bg-border mx-auto"></div>

		<section class="space-y-6">
			<p class="text-foreground/80 leading-relaxed text-lg">
				Hi, I'm Chidi 👋. I've been exploring agentic AI for a while now, mostly out of 
				a simple curiosity about how code can reason. I believe that the future of 
				software development lies in systems that don't just search, but <em>reason</em> alongside us.
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
					Unlike standard RAG pipelines that follow a linear <em>Retrieve-then-Generate</em> path, 
					this agent employs a multi-step planning phase. Before any code is read or any answer 
					is drafted, the system decomposes your request into a set of logical intents.
				</p>
				<p class="text-foreground/80 leading-relaxed">
					This planning loop allows the agent to decide which tools are necessary, whether it 
					needs to explore the repository structure first, or if it can jump directly to 
					analyzing a specific module.
				</p>
			</div>

			<div class="space-y-4">
				<h2 class="font-display text-2xl font-bold text-foreground">Tool Calling & Infrastructure</h2>
				<p class="text-foreground/80 leading-relaxed">
					TalkingCode isn't just a wrapper around an LLM; it's a software engineer with access 
					to a specialized toolkit. It interacts directly with:
				</p>
				<ul class="list-disc pl-5 space-y-2 text-foreground/80">
					<li><strong>Git Integration:</strong> To understand history, ownership, and changes.</li>
					<li><strong>Vector Databases:</strong> For semantic search across thousands of files.</li>
					<li><strong>Language Servers:</strong> To perform precise symbol lookups and dependency analysis.</li>
				</ul>
			</div>

			<div class="space-y-4">
				<h2 class="font-display text-2xl font-bold text-foreground">Metadata Filtering</h2>
				<p class="text-foreground/80 leading-relaxed">
					Simple semantic search often fails in large codebases due to "token noise." 
					To solve this, I've implemented precision metadata filtering. The agent doesn't just 
					"search for code"; it filters by:
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
</main>
