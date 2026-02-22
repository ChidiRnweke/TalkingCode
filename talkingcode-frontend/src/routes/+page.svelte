<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import type { AgentStreamEvent, Area, FileType } from '$lib/models';
	import { chatStore } from '$lib/stores';

	let question = $state('');
	let isSending = $state(false);

	function toEvent(kind: string, raw: Record<string, unknown>): AgentStreamEvent | null {
		const turnId = typeof raw.turn_id === 'string' ? raw.turn_id : '';
		const timestamp = typeof raw.timestamp === 'string' ? raw.timestamp : new Date().toISOString();

		switch (kind) {
			case 'planner_started':
				return { kind: 'planner_started', turnId, timestamp };
			case 'planner_ready': {
				const visible = (raw.visible_args as Record<string, unknown>) || {};
				const filterRoot = (visible.filters as Record<string, unknown>) || {};
				return {
					kind: 'planner_ready',
					turnId,
					intent: typeof visible.intent === 'string' ? visible.intent : 'Analyze request',
					filters: {
						areas: ((filterRoot.areas as Area[]) || []),
						languages: ((filterRoot.languages as string[]) || []),
						fileTypes: ((filterRoot.file_types as FileType[]) || []),
						pathGlobs: ((filterRoot.path_globs as string[]) || []),
						repoScopes: ((filterRoot.repo_scopes as string[]) || []),
						symbolHints: ((filterRoot.symbol_hints as string[]) || []),
						tags: ((filterRoot.tags as string[]) || [])
					},
					timestamp
				};
			}
			case 'tool_call_started':
				return {
					kind: 'tool_call_started',
					turnId,
					toolName: typeof raw.tool_name === 'string' ? raw.tool_name : 'unknown_tool',
					visibleArgs: ((raw.visible_args as Record<string, unknown>) || {}),
					timestamp
				};
			case 'tool_call_finished': {
				const visible = (raw.visible_args as Record<string, unknown>) || {};
				return {
					kind: 'tool_call_finished',
					turnId,
					toolName: typeof raw.tool_name === 'string' ? raw.tool_name : 'unknown_tool',
					success: Boolean(visible.success),
					durationMs: typeof visible.duration_ms === 'number' ? visible.duration_ms : 0,
					timestamp
				};
			}
			case 'assistant_token':
				return {
					kind: 'assistant_token',
					turnId,
					token: typeof raw.message === 'string' ? raw.message : '',
					timestamp
				};
			case 'assistant_done':
				return { kind: 'assistant_done', turnId, timestamp };
			case 'agent_error': {
				const visible = (raw.visible_args as Record<string, unknown>) || {};
				return {
					kind: 'agent_error',
					turnId,
					message: typeof raw.message === 'string' ? raw.message : 'Agent execution failed',
					code: typeof visible.code === 'string' ? visible.code : null,
					timestamp
				};
			}
			default:
				return null;
		}
	}

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!question.trim() || isSending) return;

		chatStore.startTurn();
		isSending = true;

		try {
			const response = await fetch('/api/chat/agentic', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					conversation_id: null,
					question,
					selected_model: null
				})
			});

			if (!response.ok || !response.body) {
				throw new Error('Chat stream unavailable');
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			let currentEventType = '';

			try {
				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					buffer += decoder.decode(value, { stream: true });
					const lines = buffer.split('\n');
					buffer = lines.pop() ?? '';

					for (const line of lines) {
						if (line.startsWith('event:')) {
							currentEventType = line.slice(6).trim();
							continue;
						}

						if (line.startsWith('data:')) {
							const payload = JSON.parse(line.slice(5).trim()) as Record<string, unknown>;
							const mapped = toEvent(currentEventType, payload);
							if (mapped) {
								chatStore.handleEvent(mapped);
							}
						}
					}
				}
			} finally {
				reader.releaseLock();
			}

			question = '';
		} catch (err) {
			chatStore.handleEvent({
				kind: 'agent_error',
				turnId: chatStore.currentTurnId ?? 'unknown',
				message: err instanceof Error ? err.message : 'Unexpected error',
				code: 'stream_error',
				timestamp: new Date().toISOString()
			});
		} finally {
			isSending = false;
		}
	}

	const showEmptyState = $derived(chatStore.phase === 'idle' && !chatStore.streamingContent);
	const canSubmit = $derived(
		!isSending &&
		(chatStore.phase === 'idle' || chatStore.phase === 'done' || chatStore.phase === 'error')
	);
</script>

<div class="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-10">
	<header class="mb-6 rounded-[var(--radius-xl)] border border-border/90 bg-card/90 p-6 shadow-sm backdrop-blur">
		<p class="mb-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">Editorial Light / Agentic RAG</p>
		<div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
			<div>
				<h1 class="text-3xl tracking-tight text-foreground sm:text-4xl">TalkingCode</h1>
				<p class="mt-2 max-w-2xl text-sm text-muted-foreground sm:text-base">
					Ask questions about your repository and watch planning, tool calls, and answer streaming in one whitebox timeline.
				</p>
			</div>
			<div class="rounded-full border border-border bg-background px-4 py-2 text-xs text-muted-foreground">
				Phase: <span class="font-semibold text-foreground">{chatStore.phase}</span>
			</div>
		</div>
	</header>

	<div class="grid flex-1 gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
		<aside class="space-y-4">
			<section class="rounded-[var(--radius-lg)] border border-border bg-card/95 p-4 shadow-sm">
				<p class="mb-3 text-xs uppercase tracking-[0.12em] text-muted-foreground">Planner</p>
				{#if chatStore.currentPlan}
					<p class="text-sm font-medium text-foreground">{chatStore.currentPlan.intent}</p>
					<div class="mt-3 flex flex-wrap gap-2">
						{#each chatStore.currentPlan.filters.areas as area}
							<span class="rounded-full border border-border bg-secondary px-2.5 py-1 text-xs text-secondary-foreground">
								{area}
							</span>
						{/each}
						{#each chatStore.currentPlan.filters.languages as language}
							<span class="rounded-full border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground">
								{language}
							</span>
						{/each}
					</div>
				{:else}
					<p class="text-sm text-muted-foreground">
						Planner details appear here as soon as a turn starts.
					</p>
				{/if}
			</section>

			<section class="rounded-[var(--radius-lg)] border border-border bg-card/95 p-4 shadow-sm">
				<p class="mb-3 text-xs uppercase tracking-[0.12em] text-muted-foreground">Tool Timeline</p>
				{#if chatStore.timeline.length === 0}
					<p class="text-sm text-muted-foreground">No tool calls yet.</p>
				{:else}
					<div class="space-y-2">
						{#each chatStore.timeline as item}
							<div class="rounded-[var(--radius-md)] border border-border bg-background p-3">
								<div class="flex items-center justify-between gap-2">
									<p class="truncate text-sm font-medium text-foreground" title={item.toolName}>{item.toolName}</p>
									<span
										class="rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide"
										class:text-amber-900={item.status === 'started'}
										class:bg-amber-200={item.status === 'started'}
										class:text-emerald-900={item.status === 'finished'}
										class:bg-emerald-200={item.status === 'finished'}
										class:text-rose-900={item.status === 'failed'}
										class:bg-rose-200={item.status === 'failed'}
									>
										{item.status}
									</span>
								</div>
								{#if item.durationMs}
									<p class="mt-1 text-xs text-muted-foreground">{item.durationMs}ms</p>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</section>
		</aside>

		<section class="flex min-h-[520px] flex-col rounded-[var(--radius-xl)] border border-border bg-card/95 p-4 shadow-sm sm:p-6">
			<div class="mb-4 border-b border-border pb-4">
				<p class="text-xs uppercase tracking-[0.12em] text-muted-foreground">Assistant Output</p>
			</div>

			<div class="flex-1 overflow-auto pb-4">
				{#if showEmptyState}
					<div class="flex h-full flex-col items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-border bg-background/60 px-6 text-center">
						<h2 class="text-2xl text-foreground">Ask your first repository question</h2>
						<p class="mt-3 max-w-lg text-sm text-muted-foreground">
							The assistant will show planning context, tool activity, and a streamed answer without exposing payload bodies.
						</p>
					</div>
				{:else}
					<div class="max-w-[72ch] rounded-[var(--radius-lg)] border border-border bg-background p-4 sm:p-5">
						{#if chatStore.streamingContent}
							<div class="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:rounded-md prose-code:text-[0.9em]">
								{@html chatStore.streamingContent}
							</div>
						{:else if chatStore.phase === 'planning' || chatStore.phase === 'tools'}
							<p class="text-sm text-muted-foreground">Working through planner and tool execution...</p>
						{:else if chatStore.phase === 'done'}
							<p class="text-sm text-muted-foreground">Turn completed.</p>
						{/if}
					</div>
				{/if}

				{#if chatStore.error}
					<div class="mt-4 rounded-[var(--radius-md)] border border-destructive/35 bg-destructive/10 p-3 text-sm text-foreground">
						{chatStore.error}
					</div>
				{/if}
			</div>

			<form onsubmit={handleSubmit} class="mt-2 border-t border-border pt-4">
				<div class="rounded-[var(--radius-lg)] border border-border bg-background p-3">
					<textarea
						name="question"
						bind:value={question}
						rows="3"
						placeholder="Ask about architecture, modules, ownership, or behavior..."
						class="w-full resize-none border-0 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
					></textarea>
					<div class="mt-3 flex items-center justify-between gap-3 border-t border-border pt-3">
						<p class="text-xs text-muted-foreground">Assistant responses stream in real time</p>
						<Button type="submit" disabled={!canSubmit} class="min-w-24">
							{isSending ? 'Sending...' : 'Send'}
						</Button>
					</div>
				</div>
			</form>
		</section>
	</div>
</div>
