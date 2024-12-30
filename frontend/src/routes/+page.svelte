<script lang="ts">
	import Question from '../components/Question.svelte';
	import Answer from '../components/Answer.svelte';
	import SendButton from '../components/SendButton.svelte';
	import {
		ragClient,
		remainingSpace,
		type PreviousContext,
		currentAnswer,
		type InputQuery
	} from '$lib/client';
	import Suggestions from '../components/Suggestions.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import { setContext, onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import Button from 'flowbite-svelte/Button.svelte';
	import Undo from 'flowbite-svelte-icons/UndoOutline.svelte';
	import ErrorMessage from '../components/ErrorMessage.svelte';
	import CurrentSpend from '../components/CurrentSpend.svelte';

	let input = writable('');
	setContext('input', input); // set the context for the input. This is used for the Suggestions component

	let previousContext: PreviousContext[] = $state([]);
	let latestQuestion: string = $state('');
	let inConversation = $state(false);
	enum GenerateAnswerStatus {
		NONE,
		LOADING
	}
	const generateId = (): string => {
		return (
			Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
		);
	};

	let sessionId = generateId();

	let status = $state(GenerateAnswerStatus.NONE);
	// @ts-expect-error
	let disabled = $derived(status === GenerateAnswerStatus.LOADING);
	let answer = $derived($currentAnswer);

	const generateAnswer = async (question: string): Promise<void> => {
		const inputQuery: InputQuery = {
			query: question,
			session_id: sessionId,
			previous_context: previousContext
		};
		inConversation = true;
		status = GenerateAnswerStatus.LOADING;
		previousContext = [...previousContext, { question: question, answer: answer }];
		status = GenerateAnswerStatus.NONE;
		error = false;
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
		sessionId = generateId();
		input.set('');
		error = false;
		inConversation = false;
		status = GenerateAnswerStatus.NONE;
	};

	let error: boolean = $state(false);

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
				<Answer loading={status === GenerateAnswerStatus.LOADING}>
					{@html $currentAnswer}
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
