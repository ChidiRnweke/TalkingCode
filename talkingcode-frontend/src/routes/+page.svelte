<script lang="ts">
	import { chatStore } from '$lib/stores';
	
	let { data } = $props();
	let question = $state('');
	
	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!question.trim()) return;
		
		const response = await fetch('/api/chat/agentic', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				conversation_id: null,
				question: question,
				selected_model: null
			})
		});
		
		if (response.body) {
			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			
			chatStore.startTurn();
			
			try {
				while (true) {
					const { done, value } = await reader.read();
					if (done) break;
					
					const chunk = decoder.decode(value, { stream: true });
					const lines = chunk.split('\n');
					
					for (const line of lines) {
						if (line.startsWith('event:')) {
							// Event type line
						} else if (line.startsWith('data:')) {
							const data = JSON.parse(line.slice(5));
							// Parse and handle event
							if (data.turn_id) {
								chatStore.handleEvent({
									kind: 'planner_started',
									turnId: data.turn_id,
									timestamp: data.timestamp
								});
							}
						}
					}
				}
			} finally {
				reader.releaseLock();
			}
		}
		
		question = '';
	}
</script>

<div class="flex h-screen flex-col">
	<header class="border-b px-6 py-4">
		<h1 class="text-xl font-semibold">TalkingCode</h1>
	</header>
	
	<div class="flex-1 overflow-auto p-6">
		{#if chatStore.phase === 'idle' && !chatStore.streamingContent}
			<div class="flex h-full items-center justify-center text-gray-500">
				<p>Ask a question about your codebase</p>
			</div>
		{:else}
			{#if chatStore.currentPlan}
				<div class="mb-4 rounded-lg border bg-gray-50 p-4">
					<p class="text-sm font-medium">Intent: {chatStore.currentPlan.intent}</p>
					{#if chatStore.currentPlan.filters.areas.length > 0}
						<div class="mt-2 flex gap-2">
							{#each chatStore.currentPlan.filters.areas as area}
								<span class="rounded bg-blue-100 px-2 py-1 text-xs">{area}</span>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
			
			{#if chatStore.timeline.length > 0}
				<div class="mb-4 space-y-2">
					{#each chatStore.timeline as item}
						<div class="flex items-center gap-2 rounded border bg-gray-50 p-3 text-sm">
							<span class="font-medium">{item.toolName}</span>
							<span class="text-xs text-gray-500">
								{item.status === 'started' ? '⏳' : item.status === 'finished' ? '✓' : '✗'}
							</span>
							{#if item.durationMs}
								<span class="text-xs text-gray-500">({item.durationMs}ms)</span>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
			
			{#if chatStore.streamingContent || chatStore.phase === 'streaming'}
				<div class="prose max-w-none">
					{@html chatStore.streamingContent}
				</div>
			{/if}
			
			{#if chatStore.error}
				<div class="rounded border border-red-200 bg-red-50 p-4 text-red-600">
					{chatStore.error}
				</div>
			{/if}
		{/if}
	</div>
	
	<div class="border-t p-4">
		<form onsubmit={handleSubmit} class="flex gap-2">
			<input
				type="text"
				name="question"
				bind:value={question}
				placeholder="Ask about your code..."
				class="flex-1 rounded-md border bg-white px-4 py-2"
			/>
			<button
				type="submit"
				disabled={chatStore.phase !== 'idle' && chatStore.phase !== 'done' && chatStore.phase !== 'error'}
				class="rounded-md bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
			>
				Send
			</button>
		</form>
	</div>
</div>
