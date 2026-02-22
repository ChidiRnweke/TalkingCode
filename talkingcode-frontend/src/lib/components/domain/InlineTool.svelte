<script lang="ts">
	import Tool from '$lib/components/ai-elements/tool/Tool.svelte';
	import ToolHeader from '$lib/components/ai-elements/tool/ToolHeader.svelte';
	import ToolInput from '$lib/components/ai-elements/tool/ToolInput.svelte';
	import ToolOutput from '$lib/components/ai-elements/tool/ToolOutput.svelte';
	import type { ToolCallTimelineItem } from '$lib/models';

	interface Props {
		tool: ToolCallTimelineItem;
	}

	let { tool }: Props = $props();

	const stateMap: Record<string, 'input-streaming' | 'output-available' | 'output-error'> = {
		started: 'input-streaming',
		finished: 'output-available',
		failed: 'output-error'
	};

	const duration = $derived(
		tool.durationMs !== undefined
			? `${Math.round(tool.durationMs)}ms`
			: tool.status === 'started'
				? 'Running...'
				: ''
	);
</script>

<Tool>
	<ToolHeader
		type={tool.toolName}
		state={stateMap[tool.status]}
		{duration}
	/>
	{#if tool.visibleArgs && Object.keys(tool.visibleArgs).length > 0}
		<ToolInput input={tool.visibleArgs} />
	{/if}
	{#if tool.status === 'failed'}
		<ToolOutput type="error">{tool.errorMessage ?? 'Tool failed'}</ToolOutput>
	{/if}
</Tool>