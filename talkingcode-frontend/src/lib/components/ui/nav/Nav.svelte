<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';
	let { children, class: className = '', ...rest }: HTMLAttributes<HTMLElement> & { children?: import('svelte').Snippet } = $props();
</script>
<nav class={className} {...rest}>
	{@render children?.()}
</nav>
