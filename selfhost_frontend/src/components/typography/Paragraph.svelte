<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<P class="text-lg leading-10">
	{@render children?.()}
</P>
