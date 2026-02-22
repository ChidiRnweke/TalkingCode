<script lang="ts">
	import HeroComposer from '$lib/components/domain/HeroComposer.svelte';
</script>

<main class="flex-1 flex flex-col">
	<section class="flex-1 flex flex-col items-center justify-center px-6 py-12 md:py-24">
		<div class="max-w-3xl w-full space-y-12">
			<div class="space-y-6 text-center md:text-left">
				<div class="space-y-2">
					<h2 class="font-display text-4xl md:text-6xl font-bold tracking-tight text-foreground uppercase">
						Chidi Nweke
					</h2>
					<div class="h-1.5 w-32 bg-primary mx-auto md:mx-0"></div>
				</div>
				
				<p class="font-display text-2xl md:text-3xl text-muted-foreground leading-snug">
					Solving problems with machine learning and code that works.
				</p>
				
				<p class="text-lg md:text-xl text-foreground/80 leading-relaxed max-w-2xl">
					I build things to satisfy my curiosity. This agent is here to help you explore my projects, 
					from agentic loops to the pipelines behind them.
				</p>
			</div>

			<HeroComposer />
		</div>
	</section>

	<footer class="py-8 border-t border-border/40 text-center text-sm text-muted-foreground">
		<p>&copy; {new Date().getFullYear()} Chidi Nweke. Built with curiosity.</p>
	</footer>
</main>
