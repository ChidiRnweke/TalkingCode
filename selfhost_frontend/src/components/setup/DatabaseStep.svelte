<script lang="ts">
	import Button from 'flowbite-svelte/Button.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import DatabaseOutline from 'flowbite-svelte-icons/DatabaseOutline.svelte';
	import ConfigurationForm from '../ConfigurationForm.svelte';

	interface Props {
		dbType: string;
		dbUrl: string;
		onSelectType: (type: string) => void;
		onSubmitUrl: (url: string) => void;
		inputValue?: string;
	}

	let { dbType, dbUrl, onSelectType, onSubmitUrl, inputValue = $bindable('') }: Props = $props();
</script>

<section class="space-y-8 flex flex-col items-center">
	<div class="flex items-center gap-3 text-primary-700 dark:text-primary-400 self-start">
		<DatabaseOutline class="w-8 h-8" />
		<Heading tag="h2" class="text-2xl">Database Configuration</Heading>
	</div>

	<div class="w-full max-w-md">
		<P class="mb-6 text-gray-600 dark:text-gray-300">
			Select the database type you'd like to use with TalkingCode.
		</P>

		<div class="flex flex-col sm:flex-row gap-4 justify-center mb-8">
			<Button
				on:click={() => onSelectType('sqlite')}
				class="flex-1 py-6 flex flex-col items-center justify-center transition-all duration-200 hover:scale-[1.02]"
				color={dbType === 'sqlite' ? 'blue' : 'light'}
			>
				<DatabaseOutline class="w-5 h-5 mb-2" />
				<span class="font-semibold">SQLite</span>
				<P class="text-xs mt-1 font-normal">Recommended for local development</P>
			</Button>
			<Button
				on:click={() => onSelectType('postgres')}
				class="flex-1 py-6 flex flex-col items-center justify-center transition-all duration-200 hover:scale-[1.02]"
				color={dbType === 'postgres' ? 'blue' : 'light'}
			>
				<DatabaseOutline class="w-5 h-5 mb-2" />
				<span class="font-semibold">PostgreSQL</span>
				<P class="text-xs mt-1 font-normal">Recommended for production</P>
			</Button>
		</div>

		{#if dbType === 'postgres'}
			<ConfigurationForm
				label="PostgreSQL URL"
				placeholder="postgresql://user:pass@localhost:5432/dbname"
				value={dbUrl}
				onSubmit={onSubmitUrl}
				helpText="Enter your PostgreSQL connection URL"
				bind:inputValue
			/>
		{/if}
	</div>
</section>
