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
	<Reasoning isStreaming={true} defaultOpen={false} class="w-full min-w-0 max-w-full overflow-hidden">
		<ReasoningTrigger />
	</Reasoning>
{:else if hasPlan}
	<Reasoning isStreaming={isStreaming} defaultOpen={true} class="w-full min-w-0 max-w-full overflow-hidden">
		<ReasoningTrigger class="text-left">
			<span
				class="block w-full min-w-0 max-w-full whitespace-normal text-sm leading-snug text-muted-foreground [overflow-wrap:anywhere]"
			>
				{planText || plan?.intent || 'Planning'}
			</span>
		</ReasoningTrigger>
		<ReasoningContent>
			{#if planText}
				<p class="text-sm text-foreground whitespace-pre-wrap [overflow-wrap:anywhere]">{planText}</p>
			{:else if plan}
				<div class="flex min-w-0 flex-wrap gap-2">
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
