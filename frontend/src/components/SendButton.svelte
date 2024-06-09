<script lang="ts">
	import Label from 'flowbite-svelte/Label.svelte';
	import Textarea from 'flowbite-svelte/Textarea.svelte';
	import PaperPlaneOutline from 'flowbite-svelte-icons/PaperPlaneOutline.svelte';
	import P from 'flowbite-svelte/P.svelte';

	let text = '';

	function handleInput(event: Event) {
		const textarea = event.target as HTMLTextAreaElement;
		if (textarea.scrollHeight > 280) {
			textarea.style.overflowY = '';
		} else {
			textarea.style.height = 'auto';
			textarea.style.overflowY = 'hidden';
		}
		textarea.style.height = textarea.scrollHeight + 'px';
		text = textarea.value;
	}
</script>

<div class="sticky bottom-0 bg-white pb-8">
	<div class=" mx-80 flex flex-row bg-primary-300 place-items-end rounded-md">
		<Label for="textarea-id" class="sr-only ">Your message</Label>
		<Textarea
			class="bg-transparent border-none placeholder:pl-4 resize-none max-h-52 py-2 focus:border-none focus:ring-0 dark:focus:ring-0 dark:focus:border-none text-lg placeholder:text-primary-900"
			id="textarea-id"
			placeholder="Ask me a question about my projects..."
			name="message"
			rows="1"
			tabindex="0"
			dir="auto"
			on:input={handleInput}
			bind:value={text}
		/>
		<PaperPlaneOutline
			class=" h-8 w-8 text-primary-100 bg-primary-900 rounded-full box-border my-0.5 p-2 align-bottom ml-4 mr-1"
		/>
	</div>
</div>
