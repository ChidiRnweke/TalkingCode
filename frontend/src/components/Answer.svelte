<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
</script>

<section class="flex flex-row mr-auto ml-0 gap-x-10">
	<div>
		<Avatar src="/portrait.jpg" rounded border size="xl" class="max-w-fit" />
		<P class="mt-2 text-center font-semibold text-primary-900">Chidi</P>
	</div>
	<P class="text-lg leading-10">
		<div class="generated">
			<slot />
		</div>
	</P>
</section>

<style>
	.generated :global(ul) {
		list-style-type: disc;
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
