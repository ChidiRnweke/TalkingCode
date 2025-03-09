<script lang="ts">
	import '../app.css';
	import Footer from '../components/Footer.svelte';
	interface Props {
		children: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<main class="lg:mx-40 lg:mt-20 mx-10 mt-10">
	{@render children()}
</main>
<Footer />
