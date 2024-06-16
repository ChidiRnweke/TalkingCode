<script lang="ts">
	import Question from '../components/Question.svelte';
	import Answer from '../components/Answer.svelte';
	import SendButton from '../components/SendButton.svelte';
	import {
		ragClient,
		remainingSpace,
		type PreviousContext,
		type RAGResponse,
		type inputQuery
	} from '$lib/client';
	import Suggestions from '../components/Suggestions.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import { setContext, onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import Button from 'flowbite-svelte/Button.svelte';
	import Undo from 'flowbite-svelte-icons/UndoOutline.svelte';
	import ErrorMessage from '../components/ErrorMessage.svelte';
	import TextPlaceholder from 'flowbite-svelte/TextPlaceholder.svelte';
	import CurrentSpend from '../components/CurrentSpend.svelte';

	let input = writable('');
	setContext('input', input); // set the context for the input. This is used for the Suggestions component

	let previousContext: PreviousContext[] = [];
	let sessionID: string | undefined = undefined;
	let latestQuestion: string = '';
	let inConversation = false;
	enum GenerateAnswerStatus {
		NONE,
		LOADING
	}

	let status = GenerateAnswerStatus.NONE;
	$: disabled = status === GenerateAnswerStatus.LOADING;

	const generateAnswer = async (question: string): Promise<RAGResponse> => {
		const inputQuery: inputQuery = {
			query: question,
			session_id: sessionID,
			previous_context: previousContext
		};
		inConversation = true;
		status = GenerateAnswerStatus.LOADING;
		const answer = await ragClient.getAnswer(inputQuery);
		sessionID = answer.session_id;
		previousContext = [...previousContext, { question: question, answer: answer.response }];
		status = GenerateAnswerStatus.NONE;
		error = false;
		return answer;
	};

	const submitQuestion = async (): Promise<void> => {
		latestQuestion = $input;
		try {
			await generateAnswer(latestQuestion);
			await ragClient.refreshRemainingSpend();
		} catch (error) {
			handleError();
		}
	};

	const reset = (): void => {
		previousContext = [];
		sessionID = undefined;
		input.set('');
		error = false;
		inConversation = false;
		status = GenerateAnswerStatus.NONE;
	};

	let error: boolean = false;

	const handleError = (): void => {
		inConversation = true;
		error = true;
		status = GenerateAnswerStatus.NONE;
	};

	onMount(async () => {
		await ragClient.refreshRemainingSpend();
	});
</script>

{#if inConversation === false}
	<section>
		<Heading class="text-primary-700 text-xl mb-8">Ask me a question about my projects...</Heading>

		<Suggestions />
	</section>
{:else}
	<div class="grid grid-col">
		<Button on:click={reset} class="mb-8 justify-self-end">
			Start a new conversation <span class="ml-1"> <Undo /></span>
		</Button>
		<section class="xl:mx-52 md:mx-20 grid grid-cols-1 gap-32 pb-10">
			{#each previousContext as ctx}
				<div class="flex flex-col justify-between gap-y-10">
					<Question>{ctx.question}</Question>
					<hr />
					<Answer>{@html ctx.answer}</Answer>
				</div>
			{/each}
			{#if status === GenerateAnswerStatus.LOADING}
				<Question>{latestQuestion}</Question>
				<Answer>
					<section>
						<Heading tag="h3" class="text-primary-700 text-xl mb-8">Loading...</Heading>
						<TextPlaceholder size="xxl" class="mt-8" />
					</section>
				</Answer>
			{/if}
			{#if error}
				<Question>{latestQuestion}</Question>
				<hr />
				<ErrorMessage />
			{/if}
		</section>
	</div>
{/if}

<div class="flex flex-col">
	<CurrentSpend amount={$remainingSpace} />
	<SendButton {disabled} bind:input={$input} action={submitQuestion} />
</div>
