<script lang="ts">
	import Button from 'flowbite-svelte/Button.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import { onMount } from 'svelte';
	import { type Config, saveConfig, loadConfig } from '$lib/config';
	import Card from 'flowbite-svelte/Card.svelte';
	import ArrowLeftOutline from 'flowbite-svelte-icons/ArrowLeftOutline.svelte';
	import GithubSolid from 'flowbite-svelte-icons/GithubSolid.svelte';
	import DatabaseOutline from 'flowbite-svelte-icons/DatabaseOutline.svelte';
	import ServerOutline from 'flowbite-svelte-icons/ServerOutline.svelte';
	import BrainOutline from 'flowbite-svelte-icons/BrainOutline.svelte';
	import CheckCircleOutline from 'flowbite-svelte-icons/CheckCircleOutline.svelte';

	import StepIndicator from '../../components/setup/StepIndicator.svelte';
	import GithubStep from '../../components/setup/GithubStep.svelte';
	import OpenAIStep from '../../components/setup/OpenAIStep.svelte';
	import DatabaseStep from '../../components/setup/DatabaseStep.svelte';
	import VectorStoreStep from '../../components/setup/VectorStoreStep.svelte';
	import CompletionStep from '../../components/setup/CompletionStep.svelte';

	enum SetupStep {
		GITHUB,
		OPENAI,
		DATABASE,
		VECTOR_STORE,
		COMPLETE
	}

	const steps = [
		{ name: 'GitHub', icon: GithubSolid },
		{ name: 'OpenAI', icon: BrainOutline },
		{ name: 'Database', icon: DatabaseOutline },
		{ name: 'Vector Store', icon: ServerOutline },
		{ name: 'Complete', icon: CheckCircleOutline }
	];

	let currentStep = $state(SetupStep.GITHUB);
	let config = $state<Config>({
		githubToken: '',
		openaiKey: '',
		dbType: 'sqlite',
		dbUrl: '',
		qdrantMode: 'local',
		qdrantUrl: ''
	});
	let inputValue = $state('');

	onMount(async () => {
		const savedConfig = await loadConfig();
		if (savedConfig) {
			config = savedConfig;
		}
	});

	const nextStep = () => {
		if (currentStep < SetupStep.COMPLETE) {
			currentStep++;
		}
	};

	const prevStep = () => {
		if (currentStep > SetupStep.GITHUB) {
			currentStep--;
		}
	};

	const handleGithubConfig = (value: string) => {
		config.githubToken = value;
		nextStep();
	};

	const handleOpenAIConfig = (value: string) => {
		config.openaiKey = value;
		nextStep();
	};

	const handleDatabaseTypeSelect = (type: string) => {
		config.dbType = type as 'sqlite' | 'postgres';
		if (type === 'sqlite') {
			nextStep();
		}
	};

	const handleDatabaseUrlSubmit = (url: string) => {
		config.dbUrl = url;
		nextStep();
	};

	const handleVectorStoreModeSelect = (mode: string) => {
		config.qdrantMode = mode as 'local' | 'server';
		if (mode === 'local') {
			saveConfig(config).then(() => nextStep());
		}
	};

	const handleVectorStoreUrlSubmit = (url: string) => {
		config.qdrantUrl = url;
		saveConfig(config).then(() => nextStep());
	};

	let progress = $derived(
		Math.min(100, (currentStep / (Object.keys(SetupStep).length / 2 - 0.5)) * 100)
	);
	let canGoBack = $derived(currentStep > SetupStep.GITHUB && currentStep < SetupStep.COMPLETE);
</script>

<div class="container mx-auto px-4 py-12 max-w-3xl">
	<div class="text-center mb-8">
		<Heading tag="h1" class="mb-4 text-4xl font-bold text-primary-700 dark:text-primary-400">
			TalkingCode Setup
		</Heading>
		<P class="text-lg text-gray-600 dark:text-gray-300 max-w-xl mx-auto">
			This wizard will help you set up your GitHub code analysis environment.
		</P>
	</div>

	<!-- Step Indicator Component -->
	<StepIndicator {steps} {currentStep} {progress} />

	<Card class="p-8 shadow-lg border-0 dark:border dark:border-gray-700 transition-all duration-300">
		{#if currentStep === SetupStep.GITHUB}
			<GithubStep token={config.githubToken} onSubmit={handleGithubConfig} bind:inputValue />
		{:else if currentStep === SetupStep.OPENAI}
			<OpenAIStep apiKey={config.openaiKey} onSubmit={handleOpenAIConfig} bind:inputValue />
		{:else if currentStep === SetupStep.DATABASE}
			<DatabaseStep
				dbType={config.dbType}
				dbUrl={config.dbUrl}
				onSelectType={handleDatabaseTypeSelect}
				onSubmitUrl={handleDatabaseUrlSubmit}
				bind:inputValue
			/>
		{:else if currentStep === SetupStep.VECTOR_STORE}
			<VectorStoreStep
				qdrantMode={config.qdrantMode}
				qdrantUrl={config.qdrantUrl}
				onSelectMode={handleVectorStoreModeSelect}
				onSubmitUrl={handleVectorStoreUrlSubmit}
				bind:inputValue
			/>
		{:else if currentStep === SetupStep.COMPLETE}
			<CompletionStep />
		{/if}
	</Card>

	<div class="flex justify-between mt-8 max-w-2xl mx-auto px-4">
		{#if canGoBack}
			<Button color="light" on:click={prevStep} class="group flex items-center">
				<ArrowLeftOutline
					class="mr-2 w-4 h-4 transition-transform duration-300 group-hover:-translate-x-1"
				/>
				Back
			</Button>
		{:else}
			<div></div>
		{/if}

		<div
			class="text-sm font-medium px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-gray-700 dark:text-gray-300"
		>
			Step {currentStep + 1} of {Object.keys(SetupStep).length / 2}
		</div>
	</div>
</div>
