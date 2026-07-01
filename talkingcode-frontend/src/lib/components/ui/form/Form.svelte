<script lang="ts">
	import type { HTMLFormAttributes } from 'svelte/elements';
	let { children, class: className = '', ...rest }: HTMLFormAttributes & { children?: import('svelte').Snippet } = $props();
</script>
<form class={className} {...rest}>
	{@render children?.()}
</form>
