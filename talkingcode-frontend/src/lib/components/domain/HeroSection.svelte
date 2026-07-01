<script lang="ts">
	import HeroComposer from './HeroComposer.svelte';

	let { element = $bindable(null as HTMLElement | null) } = $props();
</script>

<section
	bind:this={element}
	class="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden"
>
	<!-- Background Accents -->
	<div class="absolute top-1/4 -left-20 w-64 sm:w-80 lg:w-96 h-64 sm:h-80 lg:h-96 bg-primary/5 rounded-full blur-3xl"></div>
	<div class="absolute bottom-1/4 -right-20 w-72 sm:w-80 lg:w-96 h-72 sm:h-80 lg:h-96 bg-accent/5 rounded-full blur-3xl"></div>

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
					I've been working with GenAI for the past years, both professionally for fun.
					<strong>TalkingCode</strong> is a project I built to share some of the
					state-of-the-art techniques I've picked up along the way, and to give you a chance to
					get to know me through the code I write.
				</p>
			</div>
		</div>

		<HeroComposer />
	</div>

	<div class="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce opacity-40">
		<span class="text-3xs uppercase tracking-widest font-bold">Explore the techniques</span>
		<div class="w-px h-8 bg-foreground"></div>
	</div>
</section>
