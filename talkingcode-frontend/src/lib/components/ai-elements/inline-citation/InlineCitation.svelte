<script lang="ts">
	import * as Tooltip from '$lib/components/ui/tooltip';

	interface CitationSource {
		title: string;
		url: string;
		location?: string;
	}

	interface Props {
		label: string;
		source?: CitationSource;
	}

	let { label, source }: Props = $props();
</script>

{#if source}
	<Tooltip.Provider>
		<Tooltip.Root delayDuration={120}>
			<Tooltip.Trigger>
				<a
					href={source.url}
					target="_blank"
					rel="noopener noreferrer"
					class="ml-1 inline text-xs font-medium text-primary/80 align-super hover:text-primary hover:underline"
				>
					{label}
				</a>
			</Tooltip.Trigger>
			<Tooltip.Content side="top" class="max-w-sm space-y-1 p-2.5 text-left">
				<p class="text-xs font-semibold text-background">{source.title}</p>
				{#if source.location}
					<p class="text-[11px] opacity-90">{source.location}</p>
				{/if}
			</Tooltip.Content>
		</Tooltip.Root>
	</Tooltip.Provider>
{:else}
	<span class="ml-1 text-[10px] text-muted-foreground align-super">{label}</span>
{/if}
