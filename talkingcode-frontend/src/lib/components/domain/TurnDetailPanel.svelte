<script lang="ts">
	import {Badge} from '$lib/components/ui/badge';
	import { X } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';

	interface Props {
		message: ChatMessage | null;
		onClose: () => void;
	}

	let { message, onClose }: Props = $props();

	const statusColors = {
		started: 'secondary',
		finished: 'success',
		failed: 'danger'
	} as const;
</script>

{#if message}
	<aside
		class="fixed right-0 top-14 h-[calc(100dvh-3.5rem)] w-80 transform border-l border-border bg-background shadow-xl transition-transform duration-200 ease-in-out xl:relative xl:top-0 xl:h-full xl:w-80 xl:translate-x-0"
		class:translate-x-full={!message}
	>
		<div class="flex h-14 items-center justify-between border-b border-border px-4">
			<h3 class="font-display text-lg tracking-tight">Turn Details</h3>
			<button
				onclick={onClose}
				class="rounded-md p-1 hover:bg-secondary/50"
				aria-label="Close panel"
			>
				<X class="h-5 w-5" />
			</button>
		</div>

		<div class="flex flex-col gap-6 overflow-y-auto p-4">
			{#if message.plan}
				<section>
					<h4 class="mb-2 text-sm font-medium text-muted-foreground uppercase tracking-wider">Planner</h4>
					<p class="text-sm text-foreground">{message.plan.intent}</p>
					{#if message.plan.filters.areas.length > 0 || message.plan.filters.languages.length > 0 || message.plan.filters.fileTypes.length > 0}
						<div class="mt-3 flex flex-wrap gap-1.5">
							{#each message.plan.filters.areas as area}
								<Badge variant="secondary" size="sm">{area}</Badge>
							{/each}
							{#each message.plan.filters.languages as lang}
								<Badge variant="secondary" size="sm">{lang}</Badge>
							{/each}
							{#each message.plan.filters.fileTypes as ft}
								<Badge variant="secondary" size="sm">{ft}</Badge>
							{/each}
						</div>
					{/if}
				</section>
			{/if}

			{#if message.toolCalls && message.toolCalls.length > 0}
				<section>
					<h4 class="mb-2 text-sm font-medium text-muted-foreground uppercase tracking-wider">Tools</h4>
					<ul class="flex flex-col gap-2">
						{#each message.toolCalls as tool}
							<li class="flex items-center justify-between rounded-md border border-border/50 bg-surface-2/50 p-2">
								<span class="text-sm font-mono text-foreground">{tool.toolName}</span>
								<div class="flex items-center gap-2">
									{#if tool.durationMs}
										<span class="text-xs text-muted-foreground">{tool.durationMs}ms</span>
									{/if}
									<Badge variant={statusColors[tool.status]} size="sm">{tool.status}</Badge>
								</div>
							</li>
						{/each}
					</ul>
				</section>
			{/if}

			{#if message.error}
				<section>
					<h4 class="mb-2 text-sm font-medium text-muted-foreground uppercase tracking-wider">Error</h4>
					<div class="rounded-md bg-destructive/12 p-3 text-sm text-destructive">
						{message.error}
					</div>
				</section>
			{/if}
		</div>
	</aside>
{/if}