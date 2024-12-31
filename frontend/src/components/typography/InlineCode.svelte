<script lang="ts">
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<code class="bg-primary-200 px-2 text-yellow-600 dark:bg-primary-900 dark:text-yellow-300">
	{@render children?.()}
</code>
