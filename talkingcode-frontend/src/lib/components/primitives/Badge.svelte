<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLSpanElement> {
		variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'accent';
		size?: 'sm' | 'md';
	}

	let {
		variant = 'default',
		size = 'md',
		class: className = '',
		children,
		...rest
	}: Props = $props();

	const variantMap = {
		default: 'border-border bg-muted text-muted-foreground',
		primary: 'border-primary/30 bg-primary/12 text-primary',
		secondary: 'border-border/80 bg-secondary/70 text-secondary-foreground',
		success: 'border-[hsl(var(--color-success)/0.35)] bg-[hsl(var(--color-success)/0.15)] text-[hsl(var(--color-success))]',
		warning: 'border-[hsl(var(--color-warning)/0.3)] bg-[hsl(var(--color-warning)/0.16)] text-[hsl(var(--color-warning))]',
		danger: 'border-destructive/35 bg-destructive/12 text-destructive',
		accent: 'border-accent/30 bg-accent/15 text-accent-foreground'
	};

	const sizeMap = {
		sm: 'px-2 py-0.5 text-[11px]',
		md: 'px-2.5 py-1 text-xs'
	};
</script>

<span
	class="inline-flex items-center gap-1 rounded-full border font-medium tracking-wide uppercase {variantMap[
		variant
	]} {sizeMap[size]} {className}"
	{...rest}
>
	{@render children?.()}
</span>
