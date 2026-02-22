<script lang="ts">
	import type { AgentPlanView, Area } from '$lib/models';
	import { Card, Badge } from '$lib/components/primitives';
	import { Target, Filter, Code, FileText, GitBranch, Terminal } from 'lucide-svelte';

	interface Props {
		plan: AgentPlanView | null;
	}

	let { plan }: Props = $props();

	const areaIcons: Record<Area, typeof Target> = {
		backend: Code,
		frontend: Code,
		infra: Target,
		scripts: Terminal,
		docs: FileText,
		tests: GitBranch
	};
</script>

{#if plan}
	<Card padding="md" variant="default">
		<div class="space-y-4">
			<div class="flex items-start gap-3">
				<div
					class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] border border-primary/20 bg-primary/10"
				>
					<Target class="h-5 w-5 text-primary" />
				</div>
				<div class="min-w-0 flex-1">
					<p class="text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">Intent</p>
					<p class="mt-1 text-sm leading-snug font-medium text-foreground">{plan.intent}</p>
				</div>
			</div>

			{#if plan.filters.areas.length > 0 || plan.filters.languages.length > 0}
				<div class="border-t border-border/50 pt-4">
					<div class="flex items-center gap-2">
						<Filter class="h-4 w-4 text-muted-foreground/60" />
						<p class="text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">Filters</p>
					</div>
					<div class="mt-3 flex flex-wrap gap-2">
						{#each plan.filters.areas as area (area)}
							{@const Icon = areaIcons[area] || Target}
							<Badge variant="primary" size="sm">
								<Icon class="h-3 w-3" />
								{area}
							</Badge>
						{/each}
						{#each plan.filters.languages as lang (lang)}
							<Badge variant="secondary" size="sm">{lang}</Badge>
						{/each}
						{#each plan.filters.fileTypes as ft (ft)}
							<Badge variant="default" size="sm">{ft}</Badge>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</Card>
{:else}
	<Card padding="lg" variant="subtle">
		<div class="flex flex-col items-center justify-center py-4 text-center">
			<div
				class="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--radius-lg)] border border-border/60 bg-[hsl(var(--color-surface)/0.8)]"
			>
				<Target class="h-6 w-6 text-muted-foreground/50" />
			</div>
			<p class="text-sm text-muted-foreground">
				Planner details appear here when you start a new turn.
			</p>
		</div>
	</Card>
{/if}
