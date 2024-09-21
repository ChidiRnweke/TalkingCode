<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
</script>

<section class="flex flex-row mr-auto ml-0 lg:gap-x-10 gap-x-4 max-w-fit">
	<div>
		<Avatar
			src="/portrait.jpg"
			rounded
			border
			class="md:w-24 md:h-24 lg:w-36 lg:h-36 w-16 h-16 max-w-fit p-2 text-lg font-bold"
		/>
		<P class="mt-2 text-center font-semibold text-primary-900">Chidi</P>
	</div>
	<P class="text-lg leading-10 text-wrap">
		<div class="generated">
			<slot />
		</div>
	</P>
</section>

<style>
	.generated :global(ul) {
		list-style-type: disc;
	}

	.generated :global(pre) {
		background-color: rgb(248 250 252 / var(--tw-bg-opacity));
		box-sizing: border-box;
		padding: 1rem;
		border-radius: 0.375rem;
		margin-top: 1rem;
		margin-bottom: 1rem;
		margin-left: 1rem;
		margin-right: 1rem;
		color: orangered;
	}

	:global(.dark) .generated :global(pre) {
		background-color: rgb(15 23 42 / var(--tw-bg-opacity));
		color: rgb(250 202 21 / var(--tw-text-opacity));
	}

	:global(.dark) .generated :global(a) {
		color: lightblue;
	}

	.generated :global(a) {
		color: blue;
	}

	.generated :global(code) {
		background-color: rgb(248 250 252 / var(--tw-bg-opacity));
		padding-left: 0.5rem;
		padding-right: 0.5rem;
		color: orangered;
	}

	:global(.dark) .generated :global(code) {
		background-color: rgb(15 23 42 / var(--tw-bg-opacity));
		color: rgb(250 202 21 / var(--tw-text-opacity));
	}

	.generated :global(h3) {
		font-size: 1.5rem;
		font-weight: 600;
		color: blue-900;
	}

	.generated :global(p) {
		margin-top: 1rem;
	}
</style>
