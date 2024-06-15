<script lang="ts">
	import Navbar from 'flowbite-svelte/Navbar.svelte';
	import NavBrand from 'flowbite-svelte/NavBrand.svelte';
	import NavUl from 'flowbite-svelte/NavUl.svelte';
	import NavLi from 'flowbite-svelte/NavLi.svelte';
	import ArrowLeft from 'flowbite-svelte-icons/ArrowLeftToBracketOutline.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
	import DarkMode from 'flowbite-svelte/DarkMode.svelte';
</script>

<Navbar>
	<NavBrand href="/">
		<Avatar src="/portrait.jpg" size="md" rounded border alt="Flowbite Logo" />
		<span class="ml-2 self-center whitespace-nowrap text-xl font-semibold dark:text-white"
			>ChatGITpt (Alpha)</span
		>
	</NavBrand>
	<div class="flex flex-row">
		<NavUl>
			<NavLi href="/">Home</NavLi>
			<NavLi href="/about">About</NavLi>
			<NavLi href="/host-it-yourself">Host it yourself</NavLi>
			<NavLi
				href="https://github.com/ChidiRnweke/chatGITpt"
				class="flex flex-row place-items-center gap-x-1"
			>
				Source code <ArrowLeft size="md" />
			</NavLi>
		</NavUl>
		<DarkMode />
	</div>
</Navbar>
