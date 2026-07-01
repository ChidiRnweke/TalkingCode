<script lang="ts">
	import { cn } from '$lib/utils';

	interface Props {
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div class={cn('mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8', className)}>
	{@render children?.()}
</div>
