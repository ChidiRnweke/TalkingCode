<script lang="ts">
	import Reasoning from '$lib/components/ai-elements/reasoning/Reasoning.svelte';
	import ReasoningTrigger from '$lib/components/ai-elements/reasoning/ReasoningTrigger.svelte';
	import ReasoningContent from '$lib/components/ai-elements/reasoning/ReasoningContent.svelte';
	import Shimmer from '$lib/components/ai-elements/shimmer/Shimmer.svelte';
	import {Badge} from '$lib/components/ui/badge';
	import type { AgentPlanView } from '$lib/models';

	interface Props {
		plan: AgentPlanView | null | undefined;
		isStreaming?: boolean;
	}

	let { plan, isStreaming = false }: Props = $props();

	const hasPlan = $derived(!!plan && plan.intent !== '');
</script>

{#if isStreaming && !hasPlan}
	<Reasoning isStreaming={true}>
		<Shimmer>Analyzing your request...</Shimmer>
	</Reasoning>
{:else if plan && hasPlan}
	<Reasoning isStreaming={isStreaming}>
		<ReasoningTrigger>
			<span class="text-sm text-muted-foreground">{plan.intent}</span>
		</ReasoningTrigger>
		<ReasoningContent>
			<div class="flex flex-wrap gap-2">
				{#if plan.filters.areas.length > 0}
					{#each plan.filters.areas as area}
						<Badge variant="secondary" size="sm">{area}</Badge>
					{/each}
				{/if}
				{#if plan.filters.languages.length > 0}
					{#each plan.filters.languages as lang}
						<Badge variant="secondary" size="sm">{lang}</Badge>
					{/each}
				{/if}
				{#if plan.filters.fileTypes.length > 0}
					{#each plan.filters.fileTypes as ft}
						<Badge variant="secondary" size="sm">{ft}</Badge>
					{/each}
				{/if}
			</div>
		</ReasoningContent>
	</Reasoning>
{/if}