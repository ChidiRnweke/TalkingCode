<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		count?: number;
		columns?: number;
	}

	let { count = 3, columns = 1, class: className = '', ...rest }: Props = $props();
</script>

<div class="space-y-3 {className}" {...rest}>
	{#each Array(count) as _, rowIndex (rowIndex)}
		<div class="space-y-2">
			{#each Array(columns) as __, colIndex (colIndex)}
				<div
					class="h-4 rounded-md bg-[hsl(var(--color-surface-3)/0.85)] animate-pulse {rowIndex % 2 === 0 &&
					colIndex === columns - 1
						? 'w-5/6'
						: 'w-full'}"
				></div>
			{/each}
		</div>
	{/each}
</div>
