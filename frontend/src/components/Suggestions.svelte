<script lang="ts">
	import SuggestionCard from './SuggestionCard.svelte';
</script>

<section class="flex md:flex-row flex-col md:gap-x-4 gap-y-4 justify-center lg:my-32 md:my-20">
	<SuggestionCard input="What projects have you done in Rust? " />
	<SuggestionCard input="What is your coding style?" />
	<SuggestionCard input="What are your core skills?" />
	<SuggestionCard input="What is your strategy for testing your code?" />
	<SuggestionCard input="Do you know anything about DevOps? How do you apply it." />
</section>
