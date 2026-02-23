<script lang="ts">
	import Reasoning from '$lib/components/ai-elements/reasoning/Reasoning.svelte';
	import ReasoningTrigger from '$lib/components/ai-elements/reasoning/ReasoningTrigger.svelte';
	import ReasoningContent from '$lib/components/ai-elements/reasoning/ReasoningContent.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import type { AgentPlanView } from '$lib/models';

	interface Props {
		plan: AgentPlanView | null | undefined;
		planText?: string;
		isStreaming?: boolean;
	}

	let { plan, planText = '', isStreaming = false }: Props = $props();

	const hasPlan = $derived((!!plan && plan.intent !== '') || !!planText.trim());
</script>

{#if isStreaming && !hasPlan}
	<Reasoning isStreaming={true} defaultOpen={false}>
		<ReasoningTrigger />
	</Reasoning>
{:else if hasPlan}
	<Reasoning isStreaming={isStreaming} defaultOpen={true}>
		<ReasoningTrigger>
			<span class="text-sm text-muted-foreground">{planText || plan?.intent || 'Planning'}</span>
		</ReasoningTrigger>
		<ReasoningContent>
			{#if planText}
				<p class="text-sm text-foreground">{planText}</p>
			{:else if plan}
				<div class="flex flex-wrap gap-2">
					{#if plan.filters.areas.length > 0}
						{#each plan.filters.areas as area}
							<Badge variant="secondary">{area}</Badge>
						{/each}
					{/if}
					{#if plan.filters.languages.length > 0}
						{#each plan.filters.languages as lang}
							<Badge variant="secondary">{lang}</Badge>
						{/each}
					{/if}
					{#if plan.filters.fileTypes.length > 0}
						{#each plan.filters.fileTypes as ft}
							<Badge variant="secondary">{ft}</Badge>
						{/each}
					{/if}
				</div>
			{/if}
		</ReasoningContent>
	</Reasoning>
{/if}
