<script lang="ts">
	import Input from 'flowbite-svelte/Input.svelte';
	import Button from 'flowbite-svelte/Button.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import ArrowRightOutline from 'flowbite-svelte-icons/ArrowRightOutline.svelte';

	interface Props {
		label: string;
		placeholder: string;
		value: string;
		onSubmit: (value: string) => void;
		helpText?: string;
		inputValue?: string;
	}

	let {
		label,
		placeholder,
		value,
		onSubmit,
		helpText = '',
		inputValue = $bindable('')
	}: Props = $props();

	const handleInput = (e: Event) => {
		const input = e.target as HTMLInputElement;
		inputValue = input.value;
	};

	const handleSubmit = (e: Event) => {
		e.preventDefault();
		if (inputValue.trim()) {
			onSubmit(inputValue);
		}
	};

	let isValid = $derived(inputValue && inputValue.trim().length > 0);
	let isButtonEnabled = $derived(isValid);
</script>

<form onsubmit={handleSubmit} class="w-full">
	<div class="space-y-4">
		<div>
			<Input
				type="text"
				{label}
				{placeholder}
				value={inputValue}
				on:input={handleInput}
				class="dark:bg-gray-700 focus:ring-2 focus:ring-primary-300 dark:focus:ring-primary-600 transition-all duration-200"
				size="lg"
				color={isValid ? 'base' : 'red'}
			/>
			{#if helpText}
				<P class="text-sm text-gray-500 dark:text-gray-400 mt-1.5 ml-1">{helpText}</P>
			{/if}
		</div>
		<Button
			type="submit"
			size="lg"
			class="w-full transition-all duration-200 hover:shadow-md group"
			disabled={!isButtonEnabled}
		>
			<span>Continue</span>
			<ArrowRightOutline
				class="ml-2 w-4 h-4 transition-transform duration-300 group-hover:translate-x-1"
			/>
		</Button>
	</div>
</form>
