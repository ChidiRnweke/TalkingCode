<script lang="ts">
	import HeroComposer from './HeroComposer.svelte';
	import { fly } from 'svelte/transition';

	let { showStickyBar }: { showStickyBar: boolean } = $props();
</script>

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
