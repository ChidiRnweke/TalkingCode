<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
</script>

<section class="flex flex-row mr-auto ml-0 lg:gap-x-10 gap-x-4">
	<div>
		<Avatar
			src="/portrait.jpg"
			rounded
			border
			class="md:w-24 md:h-24 lg:w-36 lg:h-36 w-16 h-16 max-w-fit p-2 text-lg font-bold"
		/>
		<P class="mt-2 text-center font-semibold text-primary-900">Chidi</P>
	</div>
	<P class="text-lg leading-10">
		<section class=" box-border md:p-8 p-4 bg-red-400 rounded-md">
			An error ocurred. Please try again later. If this persists it may be that a critical service
			(e.g. the chatGPT server) is down.
		</section>
	</P>
</section>
