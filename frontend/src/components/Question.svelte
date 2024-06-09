<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
</script>

<section class="flex flex-row place-items-start gap-x-10">
	<P class="text-lg leading-10">
		<slot />
	</P>
	<Avatar rounded border src="you.jpg" size="xl" class="max-w-fit p-2 text-lg font-bold"></Avatar>
</section>
