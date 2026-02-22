<script lang="ts">
	import { Card, Badge, Button, Textarea } from '$lib/components/primitives';
	import { EmptyState, LoadingState } from '$lib/components/layout';
	import { PlanCard, ToolTimeline } from '$lib/components/domain';
	import { chatStore } from '$lib/stores';
	import type { AgentStreamEvent, Area, FileType } from '$lib/models';
	import { Send, Bot, Sparkles, AlertCircle } from 'lucide-svelte';

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
						areas: (filterRoot.areas as Area[]) || [],
						languages: (filterRoot.languages as string[]) || [],
						fileTypes: (filterRoot.file_types as FileType[]) || [],
						pathGlobs: (filterRoot.path_globs as string[]) || [],
						repoScopes: (filterRoot.repo_scopes as string[]) || [],
						symbolHints: (filterRoot.symbol_hints as string[]) || [],
						tags: (filterRoot.tags as string[]) || []
					},
					timestamp
				};
			}
			case 'tool_call_started':
				return {
					kind: 'tool_call_started',
					turnId,
					toolName: typeof raw.tool_name === 'string' ? raw.tool_name : 'unknown_tool',
					visibleArgs: (raw.visible_args as Record<string, unknown>) || {},
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
	const hasResponse = $derived(Boolean(chatStore.streamingContent) || chatStore.phase === 'done');

	const phaseBadge = $derived.by(() => {
		switch (chatStore.phase) {
			case 'planning':
				return { variant: 'warning' as const, label: 'Planning' };
			case 'tools':
				return { variant: 'primary' as const, label: 'Running Tools' };
			case 'streaming':
				return { variant: 'accent' as const, label: 'Streaming' };
			case 'done':
				return { variant: 'success' as const, label: 'Complete' };
			case 'error':
				return { variant: 'danger' as const, label: 'Error' };
			default:
				return { variant: 'default' as const, label: 'Idle' };
		}
	});
</script>

<div class="mx-auto flex min-h-screen w-full max-w-[92rem] flex-col px-[var(--page-padding)] py-8 lg:py-10">
	<!-- Header -->
	<header class="mb-7 lg:mb-9">
		<Card padding="lg" elevated class="relative overflow-hidden">
			<div class="absolute inset-0 opacity-60">
				<div class="absolute -top-20 -right-20 h-64 w-64 rounded-full bg-accent/12 blur-3xl"></div>
				<div
					class="absolute -bottom-20 -left-20 h-48 w-48 rounded-full bg-primary/12 blur-3xl"
				></div>
			</div>
			<div class="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
				<div>
					<div class="mb-3 flex items-center gap-2">
						<div
							class="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] border border-primary/20 bg-primary/12"
						>
							<Bot class="h-4 w-4 text-primary" />
						</div>
						<p class="text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">
							Editorial Light / Agentic RAG Canvas
						</p>
					</div>
					<h1 class="font-display text-4xl tracking-tight text-foreground sm:text-5xl">
						TalkingCode
					</h1>
					<p class="mt-3 max-w-2xl text-base leading-relaxed text-muted-foreground">
						Research your codebase in a Claude-like workspace: planning context on the left, streamed
						answers in the center, and tool evidence alongside each turn.
					</p>
				</div>
				<div class="flex items-center gap-3 self-start lg:self-auto">
					<Badge variant={phaseBadge.variant} size="md">
						{phaseBadge.label}
					</Badge>
					<Badge variant={hasResponse ? 'success' : 'default'} size="md">
						{hasResponse ? 'Conversation Active' : 'Waiting For Prompt'}
					</Badge>
				</div>
			</div>
		</Card>
	</header>

	<!-- Main Content Grid -->
	<div class="grid flex-1 gap-6 xl:grid-cols-[320px_1fr]">
		<!-- Left Sidebar -->
		<aside class="order-2 space-y-5 xl:order-1">
			<!-- Planner Section -->
			<section>
				<div class="mb-3 flex items-center gap-2">
					<Sparkles class="h-4 w-4 text-primary" />
					<p class="text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">Planner</p>
				</div>
				<PlanCard plan={chatStore.currentPlan} />
			</section>

			<!-- Tool Timeline Section -->
			<section>
				<div class="mb-3 flex items-center gap-2">
					<svg
						class="h-4 w-4 text-primary"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<path
							d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"
						/>
					</svg>
					<p class="text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">Tool Timeline</p>
				</div>
				<Card padding="md">
					<ToolTimeline items={chatStore.timeline} />
				</Card>
			</section>
		</aside>

		<!-- Main Chat Area -->
		<Card padding="none" class="order-1 flex min-h-[640px] flex-col xl:order-2">
			<div class="border-b border-border/80 px-6 py-4">
				<div class="flex items-center gap-2">
					<div
						class="flex h-6 w-6 items-center justify-center rounded-[var(--radius-sm)] border border-primary/20 bg-primary/10"
					>
						<Bot class="h-3.5 w-3.5 text-primary" />
					</div>
					<p class="text-xs tracking-[var(--tracking-wider)] text-muted-foreground uppercase">Assistant Output</p>
				</div>
			</div>

			<div class="flex-1 overflow-auto px-6 py-6">
				{#if showEmptyState}
					<EmptyState
						title="Stock your coding context"
						description="Ask for architecture walkthroughs, ownership mapping, or bug triage. Planning and tool activity will stay visible while the answer streams."
					/>
				{:else if chatStore.phase === 'planning'}
					<LoadingState phase="planning" />
				{:else if chatStore.phase === 'tools'}
					<LoadingState phase="tools" />
				{:else}
					<div class="max-w-[72ch]">
						{#if chatStore.streamingContent}
							<Card
								padding="lg"
								variant="subtle"
								class="prose prose-sm prose-p:leading-relaxed prose-pre:rounded-[var(--radius-lg)] prose-code:text-[0.9em] max-w-none"
							>
								{@html chatStore.streamingContent}
							</Card>
						{:else if chatStore.phase === 'streaming'}
							<LoadingState phase="streaming" showSkeleton={false} />
						{:else if chatStore.phase === 'done'}
							<div class="flex items-center gap-2 text-sm text-muted-foreground">
								<div class="h-2 w-2 rounded-full bg-[hsl(var(--color-success))]"></div>
								Turn completed
							</div>
						{/if}
					</div>
				{/if}

				{#if chatStore.error}
					<div
						class="mt-6 flex items-start gap-3 rounded-[var(--radius-lg)] border border-destructive/30 bg-destructive/12 p-4"
					>
						<AlertCircle class="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
						<div>
							<p class="text-sm font-medium text-destructive">Error</p>
							<p class="mt-1 text-sm text-destructive/80">{chatStore.error}</p>
						</div>
					</div>
				{/if}
			</div>

			<!-- Composer -->
			<div class="sticky bottom-0 border-t border-border/80 bg-[hsl(var(--color-surface)/0.85)] px-6 py-5 backdrop-blur-sm">
				<form onsubmit={handleSubmit}>
					<Card
						padding="md"
						variant="subtle"
						class="transition-all focus-within:border-primary/30 focus-within:shadow-[var(--shadow-md)]"
					>
						<Textarea
							name="question"
							bind:value={question}
							rows="3"
							placeholder="Ask about architecture, modules, ownership, or behavior..."
							class="border-0 bg-transparent p-0 shadow-none focus:ring-0"
						/>
						<div
							class="mt-4 flex items-center justify-between gap-4 border-t border-border/50 pt-4"
						>
							<p class="text-xs text-muted-foreground">
								Assistant responses stream in real time with tool evidence.
							</p>
							<Button type="submit" disabled={!canSubmit} class="min-w-[120px] gap-2">
								{#if isSending}
									<span
										class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
									></span>
									Sending...
								{:else}
									<Send class="h-4 w-4" />
									Send
								{/if}
							</Button>
						</div>
					</Card>
				</form>
			</div>
		</Card>
	</div>
</div>
