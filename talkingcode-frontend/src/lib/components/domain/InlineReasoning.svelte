<script lang="ts">
	import Reasoning from '$lib/components/ai-elements/reasoning/Reasoning.svelte';
	import ReasoningTrigger from '$lib/components/ai-elements/reasoning/ReasoningTrigger.svelte';
	import ReasoningContent from '$lib/components/ai-elements/reasoning/ReasoningContent.svelte';

	interface Props {
		planText?: string;
		isStreaming?: boolean;
	}

	let { planText = '', isStreaming = false }: Props = $props();
</script>

{#if isStreaming && !planText.trim()}
	<Reasoning isStreaming={true} defaultOpen={false}>
		<ReasoningTrigger />
	</Reasoning>
{:else if planText.trim()}
	<Reasoning isStreaming={isStreaming} defaultOpen={true}>
		<ReasoningTrigger>
			<span class="text-sm leading-snug text-muted-foreground">{planText}</span>
		</ReasoningTrigger>
		<ReasoningContent>
			<p class="text-sm text-foreground whitespace-pre-wrap [overflow-wrap:anywhere]">{planText}</p>
		</ReasoningContent>
	</Reasoning>
{/if}
