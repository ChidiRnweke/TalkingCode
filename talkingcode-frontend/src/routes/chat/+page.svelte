<script lang="ts">
	import { ChatThread, ChatComposer, TurnDetailPanel, ModelSelector } from '$lib/components/domain';
	import { chatStore } from '$lib/stores';
	import { AppFactory } from '$lib/factories/AppFactory';
	import { onDestroy, onMount } from 'svelte';

	interface Props {
		data: {
			models: Array<{ id: string; label: string }>;
			defaultModel: string | null;
		};
	}

	let { data }: Props = $props();

	const controller = AppFactory.getChatController();
	let activeRequestAbortController: AbortController | null = null;

	async function handleSubmit(question: string, skipAdd = false) {
		if (chatStore.isStreaming) {
			return;
		}

		activeRequestAbortController?.abort();
		activeRequestAbortController = new AbortController();

		if (!skipAdd) {
			chatStore.addUserMessage(question);
		}
		const localTurnId = chatStore.startAssistantTurn();

		try {
			const stream = controller.startAgenticTurn({
				conversationId: null,
				question,
				model: chatStore.selectedModel
			}, activeRequestAbortController.signal);

			for await (const event of stream) {
				chatStore.handleEvent(event, localTurnId);
			}
		} catch (err) {
			if (err instanceof Error && err.name === 'AbortError') {
				return;
			}

			chatStore.handleEvent({
				kind: 'agent_error',
				turnId: localTurnId,
				message: err instanceof Error ? err.message : 'Unexpected error',
				code: 'stream_error',
				timestamp: new Date().toISOString()
			}, localTurnId);
		} finally {
			activeRequestAbortController = null;
		}
	}

	onMount(() => {
		chatStore.initializeSelectedModel(data.defaultModel);

		if (
			chatStore.messages.length === 1 &&
			chatStore.messages[0].role === 'user' &&
			!chatStore.isStreaming &&
			chatStore.phase === 'idle'
		) {
			handleSubmit(chatStore.messages[0].content, true);
		}
	});

	onDestroy(() => {
		activeRequestAbortController?.abort();
		chatStore.clear();
	});

	function handleOpenDetail(messageId: string) {
		chatStore.openDetailPanel(messageId);
	}
</script>

<main class="relative flex flex-1 overflow-hidden">
	<div class="flex flex-1 flex-col overflow-hidden">
		<ModelSelector
			value={chatStore.selectedModel}
			onValueChange={(model) => chatStore.setSelectedModel(model)}
			models={data.models}
		/>

		<ChatThread
			messages={chatStore.messages}
			onOpenDetail={handleOpenDetail}
			onSuggestionClick={handleSubmit}
			onRetry={(question) => handleSubmit(question, true)}
		/>

		<ChatComposer
			onSubmit={handleSubmit}
			disabled={chatStore.isStreaming}
			selectedModel={chatStore.selectedModel}
			onModelChange={(model) => chatStore.setSelectedModel(model)}
			models={data.models}
			defaultModel={data.defaultModel}
		/>
	</div>

	<TurnDetailPanel
		message={chatStore.detailMessage}
		onClose={() => chatStore.closeDetailPanel()}
	/>
</main>
