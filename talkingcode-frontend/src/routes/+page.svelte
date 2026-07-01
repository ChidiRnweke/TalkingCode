<script lang="ts">
	import HeroSection from '$lib/components/domain/HeroSection.svelte';
	import CapabilitiesSection from '$lib/components/domain/CapabilitiesSection.svelte';
	import HowItWorksSection from '$lib/components/domain/HowItWorksSection.svelte';
	import CTASection from '$lib/components/domain/CTASection.svelte';
	import StickyChatBar from '$lib/components/domain/StickyChatBar.svelte';
	import { onMount } from 'svelte';

	let showStickyBar = $state(false);
	let heroRef = $state<HTMLElement | null>(null);

	onMount(() => { // noqa: onmount-no-browser-api — IntersectionObserver is a browser API
		if (!heroRef || !document) return;

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

<main class="flex-1 flex flex-col bg-background overflow-y-auto">
	<HeroSection bind:element={heroRef} />
	<CapabilitiesSection />
	<HowItWorksSection />
	<CTASection />
	<StickyChatBar showStickyBar={showStickyBar} />
</main>
