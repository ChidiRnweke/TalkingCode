<script lang="ts">
	import { GitBranch, MessageSquare, Search, Wrench } from 'lucide-svelte';
</script>

<section class="py-24 px-6 border-y border-border/40">
	<div class="max-w-5xl mx-auto">
		<div class="grid md:grid-cols-2 gap-16 items-center">
			<div class="space-y-8">
				<h3 class="font-display text-4xl md:text-5xl font-bold tracking-tight uppercase leading-none">
					Learning <br /> <span class="text-primary">In Public.</span>
				</h3>
				<p class="text-lg text-foreground/70 leading-relaxed">
					This agent is a sandbox for the techniques I find most interesting: multi-step reasoning,
					precise tool calling, and structural context. I'm sharing them here so we can see how they
					perform on real-world data.
				</p>

				<div class="space-y-6">
					<div class="flex gap-4">
						<div class="bg-primary/10 p-2 h-fit rounded-lg">
							<Search class="size-5 text-primary" />
						</div>
						<div>
							<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Reasoning over Data</h4>
							<p class="text-sm text-muted-foreground">Using my GitHub code as a rich dataset to demonstrate how agents can navigate and interpret complex information.</p>
						</div>
					</div>
					<div class="flex gap-4">
						<div class="bg-primary/10 p-2 h-fit rounded-lg">
							<Wrench class="size-5 text-primary" />
						</div>
						<div>
							<h4 class="font-bold uppercase tracking-wider text-sm mb-1">Multi-Step Planning</h4>
							<p class="text-sm text-muted-foreground">The core of the project: agentic loops that plan, research, and synthesize answers through iterative reasoning.</p>
						</div>
					</div>
				</div>
			</div>

			<div class="grid grid-cols-2 gap-4">
				<div class="aspect-square bg-background rounded-3xl border border-border shadow-sm p-6 flex flex-col justify-between">
					<GitBranch class="size-8 text-primary/40" />
					<div>
						<span class="text-2xl font-bold font-display">Curiosity</span>
						<p class="text-3xs uppercase tracking-widest font-bold text-muted-foreground">Driven by Research</p>
					</div>
				</div>
				<div class="aspect-square bg-primary text-primary-foreground rounded-3xl shadow-xl p-6 flex flex-col justify-between transform translate-y-8">
					<MessageSquare class="size-8 opacity-40" />
					<div>
						<span class="text-2xl font-bold font-display">Shared</span>
						<p class="text-3xs uppercase tracking-widest font-bold opacity-70">Techniques & Patterns</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</section>
