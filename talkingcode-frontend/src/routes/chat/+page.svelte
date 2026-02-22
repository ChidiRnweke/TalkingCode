<script lang="ts">
	import { ChatThread, ChatComposer, TurnDetailPanel } from '$lib/components/domain';
	import { chatStore } from '$lib/stores';
	import { AppFactory } from '$lib/factories/AppFactory';

	const controller = AppFactory.getChatController();

	async function handleSubmit(question: string, skipAdd = false) {
		if (!skipAdd) {
			chatStore.addUserMessage(question);
		}
		const turnId = chatStore.startAssistantTurn();

		try {
			const stream = controller.startAgenticTurn({
				conversationId: null,
				question,
				model: chatStore.selectedModel
			});

			for await (const event of stream) {
				chatStore.handleEvent(event);
			}
		} catch (err) {
			chatStore.handleEvent({
				kind: 'agent_error',
				turnId,
				message: err instanceof Error ? err.message : 'Unexpected error',
				code: 'stream_error',
				timestamp: new Date().toISOString()
			});
		}
	}

	// Handle initial message from Hero page or New Chat with pre-filled message
	$effect(() => {
		if (chatStore.messages.length === 1 && chatStore.messages[0].role === 'user' && !chatStore.isStreaming && chatStore.phase === 'idle') {
			handleSubmit(chatStore.messages[0].content, true);
		}
	});

	function handleOpenDetail(messageId: string) {
		chatStore.openDetailPanel(messageId);
	}
</script>

<main class="relative flex flex-1 overflow-hidden">
	<div class="flex flex-1 flex-col overflow-hidden">
		<ChatThread
			messages={chatStore.messages}
			onOpenDetail={handleOpenDetail}
			onSuggestionClick={handleSubmit}
		/>

		<ChatComposer
			onSubmit={handleSubmit}
			disabled={chatStore.isStreaming}
			selectedModel={chatStore.selectedModel}
			onModelChange={(model) => chatStore.setSelectedModel(model)}
		/>
	</div>

	<TurnDetailPanel
		message={chatStore.detailMessage}
		onClose={() => chatStore.closeDetailPanel()}
	/>
</main>
