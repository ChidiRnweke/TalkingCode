<script lang="ts">
	import Button from 'flowbite-svelte/Button.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import BrainOutline from 'flowbite-svelte-icons/BrainOutline.svelte';
	import ConfigurationForm from '../ConfigurationForm.svelte';

	interface Props {
		apiKey: string;
		onSubmit: (value: string) => void;
		inputValue?: string;
	}

	let { apiKey, onSubmit, inputValue = $bindable('') }: Props = $props();
</script>

<section class="space-y-8 flex flex-col items-center">
	<div class="flex items-center gap-3 text-primary-700 dark:text-primary-400 self-start">
		<BrainOutline class="w-8 h-8" />
		<Heading tag="h2" class="text-2xl">OpenAI Configuration</Heading>
	</div>

	<div class="w-full max-w-md">
		<P class="mb-6 text-gray-600 dark:text-gray-300">
			TalkingCode uses OpenAI's APIs for embeddings and chat.
		</P>

		<ConfigurationForm
			label="OpenAI API Key"
			placeholder="Enter your OpenAI API key"
			value={apiKey}
			{onSubmit}
			helpText="This key will be used for generating embeddings and chat responses"
			bind:inputValue
		/>

		<div class="flex flex-wrap justify-center gap-4 mt-8">
			<Button
				color="light"
				href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
				class="flex-1 min-w-fit text-sm"
			>
				Learn how to get an API key
			</Button>
			<Button
				color="light"
				href="https://platform.openai.com/api-keys"
				class="flex-1 min-w-fit text-sm"
			>
				Open OpenAI dashboard
			</Button>
		</div>
	</div>
</section>
