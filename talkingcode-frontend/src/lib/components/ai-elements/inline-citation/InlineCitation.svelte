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
					class="ml-0.5 inline text-[0.72em] font-medium align-super text-muted-foreground no-underline hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
					aria-label={`Open citation ${label}`}
				>
					{label}
				</a>
			</Tooltip.Trigger>
			<Tooltip.Content
				side="top"
				sideOffset={6}
				class="max-w-sm space-y-1.5 rounded-lg border border-border bg-popover p-3 text-left shadow-lg"
			>
				<p class="text-xs font-semibold text-foreground">{source.title}</p>
				{#if source.location}
					<p class="text-[11px] text-muted-foreground">{source.location}</p>
				{/if}
				<p class="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/80">Open source</p>
			</Tooltip.Content>
		</Tooltip.Root>
	</Tooltip.Provider>
{:else}
	<span class="ml-0.5 inline text-[0.72em] font-medium align-super text-muted-foreground">
		{label}
	</span>
{/if}
