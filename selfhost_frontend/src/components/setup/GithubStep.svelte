<script lang="ts">
	import Button from 'flowbite-svelte/Button.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import GithubSolid from 'flowbite-svelte-icons/GithubSolid.svelte';
	import ConfigurationForm from '../ConfigurationForm.svelte';

	interface Props {
		token: string;
		onSubmit: (value: string) => void;
		inputValue?: string;
	}

	let { token, onSubmit, inputValue = $bindable('') }: Props = $props();
</script>

<section class="space-y-8 flex flex-col items-center">
	<div class="flex items-center gap-3 text-primary-700 dark:text-primary-400 self-start">
		<GithubSolid class="w-8 h-8" />
		<Heading tag="h2" class="text-2xl">GitHub Configuration</Heading>
	</div>

	<div class="w-full max-w-md">
		<P class="mb-6 text-gray-600 dark:text-gray-300">
			We need a GitHub token to access your repositories.
		</P>

		<ConfigurationForm
			label="GitHub Token"
			placeholder="Enter your GitHub token"
			value={token}
			{onSubmit}
			helpText="This token will be used to access your GitHub repositories"
			bind:inputValue
		/>

		<div class="flex flex-wrap justify-center gap-4 mt-8">
			<Button
				color="light"
				href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
				class="flex-1 min-w-fit text-sm"
			>
				Learn how to create a token
			</Button>
			<Button
				color="light"
				href="https://github.com/settings/tokens?type=beta"
				class="flex-1 min-w-fit text-sm"
			>
				Open GitHub tokens page
			</Button>
		</div>
	</div>
</section>
