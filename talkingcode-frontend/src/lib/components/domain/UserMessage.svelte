<script lang="ts">
	import Message from '$lib/components/ai-elements/new-message/Message.svelte';
	import MessageContent from '$lib/components/ai-elements/new-message/MessageContent.svelte';
	import type { ChatMessage } from '$lib/models';

	interface Props {
		message: ChatMessage;
	}

	let { message }: Props = $props();
</script>

<Message from="user">
	<MessageContent>
		<p class="whitespace-pre-wrap">{message.content}</p>
	</MessageContent>
</Message>