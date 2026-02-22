<script lang="ts">
	import type { TextareaHTMLAttributes } from 'svelte/elements';

	interface Props extends TextareaHTMLAttributes {
		tone?: 'default' | 'muted';
	}

	let { tone = 'default', class: className = '', ...rest }: Props = $props();

	const toneMap = {
		default: 'bg-transparent text-foreground placeholder:text-muted-foreground/70',
		muted: 'bg-[hsl(var(--color-surface-2)/0.7)] text-foreground placeholder:text-muted-foreground/75'
	};
</script>

<textarea
	class="w-full resize-none rounded-[var(--radius-md)] border border-border/60 px-4 py-3 text-sm leading-relaxed shadow-[var(--shadow-sm)] outline-none transition-colors focus:border-primary/40 focus:ring-2 focus:ring-primary/15 {toneMap[
		tone
	]} {className}"
	{...rest}
/>
