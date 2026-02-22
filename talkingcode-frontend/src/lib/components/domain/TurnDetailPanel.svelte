<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { X } from 'lucide-svelte';
	import type { ChatMessage } from '$lib/models';

	interface Props {
		message: ChatMessage | null;
		onClose: () => void;
	}

	let { message, onClose }: Props = $props();

	const statusColors = {
		started: 'secondary',
		finished: 'default',
		failed: 'destructive'
	} as const;
</script>

{#if message}
	<button
		type="button"
		class="fixed inset-x-0 bottom-0 top-16 z-40 bg-foreground/10 backdrop-blur-[1px] xl:hidden"
		onclick={onClose}
		aria-label="Close details panel"
	></button>

	<aside
		class="fixed right-0 top-16 z-50 flex h-[calc(100dvh-4rem)] w-[min(92vw,28rem)] flex-col border-l border-border/80 bg-background shadow-2xl xl:relative xl:top-0 xl:z-10 xl:h-[calc(100dvh-4rem)] xl:w-[26rem] xl:shadow-none"
	>
		<div class="flex h-14 items-center justify-between border-b border-border bg-surface-2/30 px-4">
			<div class="flex flex-col">
				<h3 class="font-display text-sm font-bold uppercase tracking-widest text-foreground">Activity</h3>
				{#if message.thoughtDurationS}
					<span class="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Thought for {message.thoughtDurationS}s</span>
				{/if}
			</div>
			<Button variant="ghost" size="icon-sm" onclick={onClose} aria-label="Close panel">
				<X class="h-4 w-4" />
			</Button>
		</div>

		<div class="min-h-0 flex-1 overflow-y-auto p-6 pb-20">
			<div class="flex flex-col gap-8">
			{#if message.plan || message.planText}
				<section class="space-y-4">
					<div class="flex items-center gap-2">
						<div class="h-1 w-1 rounded-full bg-primary"></div>
						<h4 class="font-display text-xs font-bold tracking-widest text-muted-foreground uppercase">
							Reasoning & Plan
						</h4>
					</div>
					
					{#if message.planText}
						<div class="whitespace-pre-wrap rounded-lg border border-border/40 bg-surface-2 p-4 text-[0.95rem] leading-7 text-foreground/90">
							{message.planText}
						</div>
					{:else if message.plan?.intent}
						<div class="rounded-lg border border-border/40 bg-surface-2 p-4 text-[0.95rem] text-foreground/90">
							{message.plan.intent}
						</div>
					{/if}

					{#if message.plan && (message.plan.filters.areas.length > 0 || message.plan.filters.languages.length > 0 || message.plan.filters.fileTypes.length > 0)}
						<div class="space-y-2">
							<p class="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Retrieval Filters</p>
							<div class="flex flex-wrap gap-1.5">
								{#each message.plan.filters.areas as area}
									<Badge variant="outline" class="text-[9px] uppercase font-bold text-primary border-primary/20">{area}</Badge>
								{/each}
								{#each message.plan.filters.languages as lang}
									<Badge variant="outline" class="text-[9px] uppercase font-bold text-accent border-accent/20">{lang}</Badge>
								{/each}
								{#each message.plan.filters.fileTypes as ft}
									<Badge variant="outline" class="text-[9px] uppercase font-bold">{ft}</Badge>
								{/each}
							</div>
						</div>
					{/if}
				</section>
			{/if}

			{#if message.toolCalls && message.toolCalls.length > 0}
				<section class="space-y-4">
					<div class="flex items-center gap-2">
						<div class="h-1 w-1 rounded-full bg-primary"></div>
						<h4 class="font-display text-xs font-bold tracking-widest text-muted-foreground uppercase">
							Tools & Research
						</h4>
					</div>
					<ul class="flex flex-col gap-3">
						{#each message.toolCalls as tool}
							<li class="group flex flex-col gap-2 rounded-xl border border-border/60 bg-background p-3 shadow-sm hover:shadow-md transition-shadow">
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-2">
										<span class="text-xs font-mono font-bold text-foreground">{tool.toolName}</span>
										{#if tool.iteration}
											<Badge variant="outline" class="text-[9px] h-4">Iter {tool.iteration}</Badge>
										{/if}
									</div>
									<Badge variant={statusColors[tool.status]} class="text-[9px] font-bold uppercase tracking-tighter px-1.5 h-4">
										{tool.status}
									</Badge>
								</div>
								
								{#if tool.visibleArgs && Object.keys(tool.visibleArgs).length > 0}
									<div class="text-[10px] bg-surface-2/50 rounded-md p-2 font-mono text-muted-foreground overflow-hidden text-ellipsis whitespace-nowrap">
										{JSON.stringify(tool.visibleArgs)}
									</div>
								{/if}

								{#if tool.durationMs}
									<div class="text-[9px] text-muted-foreground font-medium text-right italic">
										Took {tool.durationMs}ms
									</div>
								{/if}
							</li>
						{/each}
					</ul>
				</section>
			{/if}

			{#if message.error}
				<section class="space-y-4">
					<div class="flex items-center gap-2">
						<div class="h-1 w-1 rounded-full bg-destructive"></div>
						<h4 class="font-display text-xs font-bold tracking-widest text-destructive uppercase">
							Error
						</h4>
					</div>
					<div class="rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive leading-relaxed font-medium">
						{message.error}
					</div>
				</section>
			{/if}
			</div>
		</div>
	</aside>
{/if}
