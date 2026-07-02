<script lang="ts">
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		class?: string;
		children: Snippet;
	}

	let { class: className, children, ...restProps }: Props = $props();
</script>

<div
	class={cn(
		'is-user:dark flex w-fit flex-col gap-2 overflow-hidden text-sm',
		'group-[.is-user]:ml-auto group-[.is-user]:rounded-lg group-[.is-user]:bg-secondary group-[.is-user]:px-4 group-[.is-user]:py-3 group-[.is-user]:text-foreground',
		'group-[.is-assistant]:max-w-full md:group-[.is-assistant]:max-w-[74ch] group-[.is-assistant]:text-[1.04rem] group-[.is-assistant]:leading-relaxed group-[.is-assistant]:font-medium group-[.is-assistant]:text-foreground',
		className
	)}
	{...restProps}
>
	{@render children()}
</div>
