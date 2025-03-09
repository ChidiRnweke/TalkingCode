<script lang="ts">
	import ProgressBar from 'flowbite-svelte/Progressbar.svelte';

	interface Step {
		name: string;
		icon: any;
	}

	interface Props {
		steps: Step[];
		currentStep: number;
		progress: number;
	}

	let { steps, currentStep, progress }: Props = $props();
</script>

<div class="mb-12 max-w-2xl mx-auto">
	<div class="flex items-center justify-between mb-2">
		{#each steps as step, idx}
			{#if idx < steps.length - 1}
				<div class="flex flex-col items-center">
					<div
						class="{currentStep >= idx
							? 'bg-primary-600 text-white'
							: 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'} 
							w-10 h-10 rounded-full flex items-center justify-center
							transition-all duration-300 shadow-md"
					>
						{#key step.icon}
							<step.icon class="w-5 h-5" />
						{/key}
					</div>
					<span
						class="mt-2 text-sm {currentStep === idx
							? 'font-bold text-primary-700 dark:text-primary-400'
							: 'text-gray-500 dark:text-gray-400'}"
					>
						{step.name}
					</span>
				</div>
			{/if}
		{/each}
	</div>
	<ProgressBar {progress} size="lg" color="blue" class="h-2" />
</div>
