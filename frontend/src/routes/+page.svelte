<script lang="ts">
	import Hr from 'flowbite-svelte/Hr.svelte';
	import Question from '../components/Question.svelte';
	import Answer from '../components/Answer.svelte';
	import SendButton from '../components/SendButton.svelte';
	import { ragClient, type PreviousContext, type RAGResponse, type inputQuery } from '$lib/client';
	let input = '';
	let previousContext: PreviousContext[] = [];
	let sessionID: string | undefined = undefined;

	export const getAnswer = async (question: string): Promise<RAGResponse> => {
		const inputQuery: inputQuery = {
			query: question,
			session_id: sessionID,
			previous_context: previousContext
		};
		const answer = await ragClient.getAnswer(inputQuery);
		sessionID = answer.session_id;
		previousContext = [...previousContext, { question: question, answer: answer.response }];
		console.log(previousContext);
		return answer;
	};

	export let sendQuestion = async () => {
		const question = input;
		const answer = await getAnswer(question);
	};
</script>

<section class="mx-52 grid grid-cols-1 gap-32 pb-10">
	{#each previousContext as ctx}
		<div class="flex flex-col justify-between gap-y-10">
			<Question>{ctx.question}</Question>
			<Hr />
			<Answer>{@html ctx.answer}</Answer>
		</div>
	{/each}
</section>

<SendButton bind:input bind:action={sendQuestion} />
