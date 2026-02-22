<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		padding?: 'none' | 'sm' | 'md' | 'lg';
		elevated?: boolean;
		variant?: 'default' | 'subtle' | 'highlight';
	}

	let {
		padding = 'md',
		elevated = false,
		variant = 'default',
		class: className = '',
		children,
		...rest
	}: Props = $props();

	const padMap = {
		none: '',
		sm: 'p-4',
		md: 'p-5',
		lg: 'p-8'
	};

	const variantMap = {
		default: 'border-border/85 bg-card/92 backdrop-blur-[2px]',
		subtle: 'border-border/60 bg-[hsl(var(--color-surface-2)/0.58)] backdrop-blur-sm',
		highlight: 'border-primary/24 bg-[hsl(var(--color-primary-light)/0.58)]'
	};
</script>

<div
	class="rounded-[var(--radius-lg)] border {variantMap[variant]} {padMap[padding]} {elevated
		? 'shadow-[var(--shadow-lg)]'
		: 'shadow-[var(--shadow-card)]'} {className}"
	{...rest}
>
	{@render children?.()}
</div>
