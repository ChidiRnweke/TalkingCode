<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
</script>

<div class="flex flex-row ml-auto mr-0 gap-x-10">
	<section class=" bg-primary-50 box-border p-8">
		<P class="text-lg leading-10">
			<slot />
		</P>
	</section>
	<div>
		<Avatar rounded border src="you.jpg" size="xl" class="max-w-fit p-2 text-lg font-bold"></Avatar>
		<P class="mt-2 text-center font-semibold text-primary-900">Ana</P>
	</div>
</div>
