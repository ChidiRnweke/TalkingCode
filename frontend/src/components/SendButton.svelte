<script lang="ts">
	import Label from 'flowbite-svelte/Label.svelte';
	import Textarea from 'flowbite-svelte/Textarea.svelte';
	import PaperPlaneOutline from 'flowbite-svelte-icons/PaperPlaneOutline.svelte';
	import Button from 'flowbite-svelte/Button.svelte';
	export let input = '';
	export let action: () => void;

	function handleInput(event: Event) {
		const textarea = event.target as HTMLTextAreaElement;
		if (textarea.scrollHeight > 280) {
			textarea.style.overflowY = '';
		} else {
			textarea.style.height = 'auto';
			textarea.style.overflowY = 'hidden';
		}
		textarea.style.height = textarea.scrollHeight + 'px';
		input = textarea.value;
	}

	const handleKeydown = (event: KeyboardEvent): void => {
		const { key, shiftKey } = event;

		if (key === 'Enter') {
			if (shiftKey) {
				input += '\n';
			} else {
				event.preventDefault();
				action();
			}
		}
	};
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
			bind:value={input}
			on:keydown={handleKeydown}
		/>
		<Button class=" bg-primary-900 rounded-md" on:click={action}>
			<PaperPlaneOutline class=" text-primary-100 " />
		</Button>
	</div>
</div>
