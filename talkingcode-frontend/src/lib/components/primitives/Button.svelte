<script lang="ts">
	import {
		Button as UIButton,
		type ButtonProps,
		type ButtonSize,
		type ButtonVariant
	} from '$lib/components/ui/button';

	interface Props extends Omit<ButtonProps, 'variant' | 'size'> {
		variant?: ButtonVariant;
		size?: ButtonSize;
	}

	let { variant = 'default', size = 'default', class: className = '', children, ...rest }: Props =
		$props();

	const baseTone =
		'font-medium tracking-wide transition-all duration-200 data-[slot=button]:rounded-[var(--radius-md)]';

	const toneMap: Record<ButtonVariant, string> = {
		default:
			'bg-primary text-primary-foreground shadow-[var(--shadow-sm)] hover:bg-primary/92 hover:shadow-[var(--shadow-md)]',
		destructive:
			'bg-destructive text-primary-foreground shadow-[var(--shadow-sm)] hover:bg-destructive/90',
		outline:
			'border-border bg-[hsl(var(--color-surface-2)/0.72)] text-foreground hover:bg-[hsl(var(--color-surface-3)/0.9)]',
		secondary:
			'bg-[hsl(var(--color-surface-3)/0.9)] text-foreground shadow-[var(--shadow-sm)] hover:bg-[hsl(var(--color-surface-3))]',
		ghost:
			'text-muted-foreground hover:bg-[hsl(var(--color-surface-3)/0.6)] hover:text-foreground',
		link: 'text-primary underline-offset-4 hover:underline'
	};
</script>

<UIButton variant={variant} size={size} class="{baseTone} {toneMap[variant]} {className}" {...rest}>
	{@render children?.()}
</UIButton>
