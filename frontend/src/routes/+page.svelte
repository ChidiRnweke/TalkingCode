<script lang="ts">
	import Hr from 'flowbite-svelte/Hr.svelte';
	import Question from '../components/Question.svelte';
	import Answer from '../components/Answer.svelte';
	import SendButton from '../components/SendButton.svelte';
	import { ragClient, type PreviousContext, type RAGResponse, type inputQuery } from '$lib/client';
	import Suggestions from '../components/Suggestions.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import { setContext } from 'svelte';
	import { writable } from 'svelte/store';

	let input = writable('');
	setContext('input', input); // set the context for the input. This is used for the Suggestions component

	let previousContext: PreviousContext[] = [];
	let sessionID: string | undefined = undefined;
	$: inConversation = previousContext.length == 0 ? false : true;

	const getAnswer = async (question: string): Promise<RAGResponse> => {
		const inputQuery: inputQuery = {
			query: question,
			session_id: sessionID,
			previous_context: previousContext
		};
		const answer = await ragClient.getAnswer(inputQuery);
		sessionID = answer.session_id;
		previousContext = [...previousContext, { question: question, answer: answer.response }];
		return answer;
	};
	$: question = $input;
	let sendQuestion = async () => {
		const answer = await getAnswer(question);
	};
</script>

{#if inConversation === false}
	<section>
		<Heading class="text-primary-900 text-xl mb-8">Ask me a question about my projects...</Heading>

		<Suggestions />
	</section>
{:else}
	<section class="xl:mx-52 md:mx-20 grid grid-cols-1 gap-32 pb-10">
		{#each previousContext as ctx}
			<div class="flex flex-col justify-between gap-y-10">
				<Question>{ctx.question}</Question>
				<Hr />
				<Answer>{@html ctx.answer}</Answer>
			</div>
		{/each}
	</section>
{/if}

<SendButton bind:input={$input} bind:action={sendQuestion} />
