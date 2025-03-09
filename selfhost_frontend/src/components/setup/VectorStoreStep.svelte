<script lang="ts">
	import Button from 'flowbite-svelte/Button.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import ServerOutline from 'flowbite-svelte-icons/ServerOutline.svelte';
	import ConfigurationForm from '../ConfigurationForm.svelte';

	interface Props {
		qdrantMode: string;
		qdrantUrl: string;
		onSelectMode: (mode: string) => void;
		onSubmitUrl: (url: string) => void;
		inputValue?: string;
	}

	let {
		qdrantMode,
		qdrantUrl,
		onSelectMode,
		onSubmitUrl,
		inputValue = $bindable('')
	}: Props = $props();
</script>

<section class="space-y-8 flex flex-col items-center">
	<div class="flex items-center gap-3 text-primary-700 dark:text-primary-400 self-start">
		<ServerOutline class="w-8 h-8" />
		<Heading tag="h2" class="text-2xl">Vector Store Configuration</Heading>
	</div>

	<div class="w-full max-w-md">
		<P class="mb-6 text-gray-600 dark:text-gray-300">
			Select the vector storage option for your embeddings.
		</P>

		<div class="flex flex-col sm:flex-row gap-4 justify-center mb-8">
			<Button
				on:click={() => onSelectMode('local')}
				class="flex-1 py-6 flex flex-col items-center justify-center transition-all duration-200 hover:scale-[1.02]"
				color={qdrantMode === 'local' ? 'blue' : 'light'}
			>
				<ServerOutline class="w-5 h-5 mb-2" />
				<span class="font-semibold">Local Storage</span>
				<P class="text-xs mt-1 font-normal">Recommended for personal use</P>
			</Button>
			<Button
				on:click={() => onSelectMode('server')}
				class="flex-1 py-6 flex flex-col items-center justify-center transition-all duration-200 hover:scale-[1.02]"
				color={qdrantMode === 'server' ? 'blue' : 'light'}
			>
				<ServerOutline class="w-5 h-5 mb-2" />
				<span class="font-semibold">Remote Qdrant</span>
				<P class="text-xs mt-1 font-normal">For custom server setup</P>
			</Button>
		</div>

		{#if qdrantMode === 'server'}
			<ConfigurationForm
				label="Qdrant Server URL"
				placeholder="http://localhost:6334"
				value={qdrantUrl}
				onSubmit={onSubmitUrl}
				helpText="Enter your Qdrant server URL"
				bind:inputValue
			/>
		{/if}
	</div>
</section>
