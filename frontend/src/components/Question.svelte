<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
</script>

<div class="flex flex-row ml-auto mr-0 lg:gap-x-10 gap-x-4">
	<section class=" bg-primary-50 box-border md:p-8 p-4">
		<P class="text-lg leading-10">
			<slot />
		</P>
	</section>
	<div>
		<Avatar
			rounded
			border
			src="you.jpg"
			class="lg:w-36 lg:h-36 md:w-24 md:h-24 w-16 h-16 max-w-fit p-2 text-lg font-bold"
		></Avatar>
		<P class="mt-2 text-center font-semibold text-primary-900">Ana</P>
	</div>
</div>
