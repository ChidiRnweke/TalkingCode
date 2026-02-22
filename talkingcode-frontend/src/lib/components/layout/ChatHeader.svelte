<script lang="ts">
	import {Badge} from '$lib/components/ui/badge';
	import { Code2 } from 'lucide-svelte';

	type TurnPhase = 'idle' | 'planning' | 'tools' | 'streaming' | 'done' | 'error';

	type BadgeVariant = 'default' | 'secondary' | 'outline' | 'destructive';

	interface Props {
		phase?: TurnPhase;
	}

	let { phase = 'idle' }: Props = $props();

	const phaseLabels: Record<TurnPhase, string> = {
		idle: 'Ready',
		planning: 'Planning',
		tools: 'Using tools',
		streaming: 'Generating',
		done: 'Done',
		error: 'Error'
	};

	const phaseVariants: Record<TurnPhase, BadgeVariant> = {
		idle: 'secondary',
		planning: 'secondary',
		tools: 'secondary',
		streaming: 'outline',
		done: 'secondary',
		error: 'destructive'
	};
</script>

<header class="flex h-14 items-center justify-between border-b border-border px-[var(--page-padding)]">
	<div class="flex items-center gap-2">
		<Code2 class="h-6 w-6 text-primary" />
		<span class="font-display text-xl tracking-tight text-foreground">TalkingCode</span>
	</div>
	<Badge variant={phaseVariants[phase]}>{phaseLabels[phase]}</Badge>
</header>
