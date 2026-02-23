<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { X } from 'lucide-svelte';
	import InlineTool from './InlineTool.svelte';
	import type { ChatMessage, ReasoningStep } from '$lib/models';

	interface Props {
		message: ChatMessage | null;
		onClose: () => void;
	}

	let { message, onClose }: Props = $props();

	function toTitleCaseTool(name: string): string {
		return name
			.split('_')
			.filter(Boolean)
			.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
			.join(' ');
	}

	function displayToolArgs(args: Record<string, unknown>): string {
		const query = args.query;
		if (typeof query === 'string' && query.trim()) {
			return `Query: ${query}`;
		}

		const repository = args.repository;
		const filePath = args.file_path;
		if (typeof repository === 'string' && typeof filePath === 'string') {
			return `File: ${repository}/${filePath}`;
		}

		return Object.entries(args)
			.map(([key, value]) => {
				const label = key
					.split('_')
					.filter(Boolean)
					.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
					.join(' ');

				if (Array.isArray(value)) {
					return `${label}: ${value.join(', ')}`;
				}

				if (value && typeof value === 'object') {
					return `${label}: ${Object.keys(value as Record<string, unknown>).join(', ')}`;
				}

				return `${label}: ${String(value)}`;
			})
			.join('\n');
	}

	function formatDurationSeconds(durationMs: number): string {
		const seconds = durationMs / 1000;
		return `${Math.max(0.1, seconds).toFixed(durationMs < 1000 ? 1 : 2)}s`;
	}

	const statusColors = {
		started: 'secondary',
		finished: 'default',
		failed: 'destructive'
	} as const;

	const sortedReasoningSteps = $derived.by(() => {
		const steps = [...(message?.reasoningSteps ?? [])];
		return steps.sort((a, b) => {
			const timeDiff = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
			if (timeDiff !== 0) return timeDiff;
			if (a.kind === 'plan' && b.kind === 'tool') return -1;
			if (a.kind === 'tool' && b.kind === 'plan') return 1;
			return 0;
		});
	});

	function reasoningKey(step: ReasoningStep): string {
		if (step.kind === 'tool') {
			return step.tool.callId ?? step.id;
		}
		return step.id;
	}
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
					<span class="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Thought for {message.thoughtDurationS} seconds</span>
				{/if}
			</div>
			<Button variant="ghost" size="icon-sm" onclick={onClose} aria-label="Close panel">
				<X class="h-4 w-4" />
			</Button>
		</div>

		<div class="min-h-0 flex-1 overflow-y-auto p-6 pb-20">
			<div class="flex flex-col gap-8">
			{#if sortedReasoningSteps.length > 0}
				<section class="space-y-4">
					<div class="flex items-center gap-2">
						<div class="h-1 w-1 rounded-full bg-primary"></div>
						<h4 class="font-display text-xs font-bold tracking-widest text-muted-foreground uppercase">
							Reasoning Timeline
						</h4>
					</div>

					<div class="space-y-2">
						{#each sortedReasoningSteps as step (reasoningKey(step))}
							{#if step.kind === 'plan'}
								<div class="whitespace-pre-wrap rounded-md border border-border/40 bg-surface-2 p-4 text-[0.95rem] leading-7 text-foreground/90">
									<p class="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
										Plan {step.iteration}
									</p>
									{step.text}
								</div>
							{:else if step.kind === 'tool'}
								<InlineTool tool={step.tool} />
							{:else if step.phase === 'answer_started'}
								<p class="text-xs font-medium italic text-muted-foreground">Switching to final answer...</p>
							{/if}
						{/each}
					</div>
				</section>
			{:else if message.plan || message.planText}
				<section class="space-y-4">
					<div class="flex items-center gap-2">
						<div class="h-1 w-1 rounded-full bg-primary"></div>
						<h4 class="font-display text-xs font-bold tracking-widest text-muted-foreground uppercase">
							Reasoning & Plan
						</h4>
					</div>
					
					{#if message.planText}
						<div class="whitespace-pre-wrap rounded-md border border-border/40 bg-surface-2 p-4 text-[0.95rem] leading-7 text-foreground/90">
							{message.planText}
						</div>
					{:else if message.plan?.intent}
						<div class="rounded-md border border-border/40 bg-surface-2 p-4 text-[0.95rem] text-foreground/90">
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

			{#if !sortedReasoningSteps.length && message.toolCalls && message.toolCalls.length > 0}
				<section class="space-y-4">
					<div class="flex items-center gap-2">
						<div class="h-1 w-1 rounded-full bg-primary"></div>
						<h4 class="font-display text-xs font-bold tracking-widest text-muted-foreground uppercase">
							Tools & Research
						</h4>
					</div>
					<ul class="flex flex-col gap-3">
						{#each message.toolCalls as tool}
							<li class="group flex flex-col gap-2 rounded-lg border border-border/60 bg-background p-3 shadow-sm hover:shadow-md transition-shadow">
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-2">
									<span class="text-xs font-mono font-bold text-foreground">{toTitleCaseTool(tool.toolName)}</span>
										{#if tool.iteration}
											<Badge variant="outline" class="text-[9px] h-4">Iter {tool.iteration}</Badge>
										{/if}
									</div>
									<Badge variant={statusColors[tool.status]} class="text-[9px] font-bold uppercase tracking-tighter px-1.5 h-4">
										{tool.status}
									</Badge>
								</div>
								
								{#if tool.visibleArgs && Object.keys(tool.visibleArgs).length > 0}
									<div class="max-h-24 overflow-y-auto rounded-md bg-surface-2/50 p-2 text-[11px] leading-relaxed text-muted-foreground">
										{displayToolArgs(tool.visibleArgs)}
									</div>
								{/if}

								{#if tool.durationMs !== undefined}
									<div class="text-[9px] text-muted-foreground font-medium text-right italic">
										Took {formatDurationSeconds(tool.durationMs)}
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
