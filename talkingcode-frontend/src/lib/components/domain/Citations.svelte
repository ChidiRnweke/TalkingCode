<script lang="ts">
	interface Source {
		index: number;
		repository: string;
		path: string;
		startLine: number | null;
		endLine: number | null;
	}

	interface Props {
		sources: Source[];
	}

	let { sources }: Props = $props();

	function githubUrl(source: Source): string {
		const lineRef = source.startLine
			? `#L${source.startLine}${source.endLine ? `-L${source.endLine}` : ''}`
			: '';
		return `https://github.com/${source.repository}/blob/main/${source.path}${lineRef}`;
	}
</script>

{#if sources.length > 0}
	<div class="mt-4 border-t border-border pt-3">
		<p class="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Sources</p>
		<ol class="space-y-1 text-sm">
			{#each sources as source}
				<li class="flex items-start gap-1.5">
					<span class="font-mono text-xs text-muted-foreground">[{source.index}]</span>
					<a
						href={githubUrl(source)}
						target="_blank"
						rel="noopener"
						class="truncate text-primary hover:underline"
					>
						{source.repository}: {source.path}
						{#if source.startLine}
							<span class="text-muted-foreground">
								(L{source.startLine}{source.endLine ? `-${source.endLine}` : ''})
							</span>
						{/if}
					</a>
				</li>
			{/each}
		</ol>
	</div>
{/if}
