<script>
	import '../app.css';
	import Navbar from '../components/Navbar.svelte';
</script>

<Navbar />
<main class="lg:mx-40 lg:mt-20 mx-10 mt-10">
	<slot />
</main>
