<script lang="ts">
	import Button from 'flowbite-svelte/Button.svelte';
	import Heading from 'flowbite-svelte/Heading.svelte';
	import P from 'flowbite-svelte/P.svelte';
	import CheckCircleOutline from 'flowbite-svelte-icons/CheckCircleOutline.svelte';
	import ArrowRightOutline from 'flowbite-svelte-icons/ArrowRightOutline.svelte';
</script>

<section class="py-10 flex flex-col items-center text-center">
	<div class="text-green-600 mb-8 animate-pulse">
		<CheckCircleOutline class="w-24 h-24 mx-auto" />
	</div>
	<div class="max-w-md">
		<Heading tag="h2" class="text-3xl mb-4 text-green-600 dark:text-green-500">
			Setup Complete!
		</Heading>
		<P class="text-gray-600 dark:text-gray-300 mb-10">
			Your configuration has been saved. You're all set to start using TalkingCode.
		</P>
		<Button
			href="/"
			size="xl"
			class="px-12 py-3 text-lg group transition-all duration-300 hover:shadow-lg"
		>
			Go to Dashboard
			<ArrowRightOutline
				class="ml-2 w-4 h-4 transition-transform duration-300 group-hover:translate-x-1"
			/>
		</Button>
	</div>
</section>
