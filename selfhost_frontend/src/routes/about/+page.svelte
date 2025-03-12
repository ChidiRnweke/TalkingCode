<script lang="ts">
	import Heading from 'flowbite-svelte/Heading.svelte';
	import List from 'flowbite-svelte/List.svelte';
	import Li from 'flowbite-svelte/Li.svelte';
	import A from 'flowbite-svelte/A.svelte';
	import Paragraph from '../../components/typography/Paragraph.svelte';
	import InlineCode from '../../components/typography/InlineCode.svelte';
</script>

<article class="lg:mx-52 grid grid-cols-1 gap-y-10 mb-10">
	<header>
		<Heading>Some info about...</Heading>
	</header>
	<section>
		<Heading tag="h2" class="mb-8">The idea</Heading>
		<Paragraph>
			The idea is simple. Make a retrieval augmented generation (RAG) app that has access to all of
			my GitHub code. That way people can ask questions about my project and the models try, to the
			best of their ability, to formulate a coherent answer.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">The inspiration</Heading>
		<Paragraph>
			As a student I took the course "search engines and information retrieval" in approx. 2020.
			RAGs aren't named verbatim but the same idea is used there. The key part being embedding a
			document and a quey into a shared semantic space and then performing a search and ranking.
			Topics such as HNSW were also discussed.
		</Paragraph>
		<Paragraph>
			There has been a lot of hype surrounding GenAI for the past couple of years. As a machine
			learning engineer it's become a must-have skill. The point of the project is to prove to
			myself (and others) that building these kinds of applications are not difficult, they're an
			extension of what I already knew. <b>The end-to-end implementation took just one week</b> and that
			is with me only having time in select evenings and the weekend.
		</Paragraph>
	</section>

	<section class="grid grid-cols-1 gap-y-5">
		<Heading tag="h2" class="mb-8">The tech stack</Heading>
		<Paragraph>
			The summary of the tech stack is that it's a full-stack application built with Python in the
			backend and SvelteKit (Typescript) in the frontend. The backend is built using FastAPI. Two
			databases are used, a vector database for storing the embeddings (Qdrant) and a regular
			database for storing the metadata (Postgres or sqlite). The app is hosted on a VPS running
			Ubuntu and is deployed using Docker and Docker Compose. The deployment is done using Ansible
			and GitHub Actions. All the code is available on GitHub.
		</Paragraph>
		<section>
			<Heading tag="h3" class="mb-8">The ETL: Python</Heading>
			<Paragraph>
				The ETL (extract, transform, load) process is done in Python. The code is available in the
				<InlineCode>data pipelines</InlineCode>
				folder. The code is simple and does the following:
				<List tag="ol" class="my-2">
					<Li>Extracts the data from the GitHub API</Li>
					<Li>Extract some of the data from the response</Li>
					<Li>Store in the database</Li>
				</List>
				After the data is stored in the database, the data is embedded.
			</Paragraph>
			<Paragraph>
				The entire process is orchestrated using a simple Python script that runs the ETL every
				night. The metrics are stored inside my observability stack, consisting of Loki, Tempo,
				Prometheus, and Grafana.
			</Paragraph>
		</section>
		<section>
			<Heading tag="h3" class="mb-8">The database: Qdrant and Postgres</Heading>
			<Paragraph>
				Vector databases are a hot topic right now. The idea is to store the data in a way that
				makes it easy to search and rank. Qdrant is used for this purpose. The database is simple to
				use and has a great Python client. The database is used for storing the embeddings of the
				data. Qdrant was chosen in particular because it can run with a client-server architecture
				as well as locally with the same ease as sqlite.
			</Paragraph>
			<Paragraph>
				The metadata for the ingestion process as well as the tokens spent are stored in a
				relational database. The database is either Postgres or sqlite. Postgres is used for
				production and sqlite is used for development. The database is accessed using SQLAlchemy.
			</Paragraph>
		</section>
		<section>
			<Heading tag="h3" class="mb-8">The backend: FastAPI</Heading>
			<Paragraph>
				The API is built using FastAPI. The main endpoint is
				<InlineCode>/rag/chat</InlineCode>, which streams AI responses using chunked transfer
				encoding. FastAPI was also a conscious choice. The reason being that it has great
				asynchronous programming support. This is important because the RAG model can take a long
				time to generate an answer and I don't want to block the server while that happens. The
				answers are also streamed to the client as they're generated.
			</Paragraph>
		</section>
		<section>
			<Heading tag="h3" class="mb-8">The frontend: SvelteKit</Heading>
			<div class="grid grid-cols-1 gap-y-3">
				<Paragraph>
					The frontend is built using SvelteKit. The frontend keeps it simple. The root page is
					already used for the conversation. Aside from that there's this page, the about page, and
					the "host-it-yourself" page. The frontend uses server-side rendering which means that
					static pages are generated at build time and transparently served by the server. The rest
					is done client-side. The frontend is styled using TailwindCSS.
				</Paragraph>
				<Paragraph>
					I prefer making static sites because they're simple to make and simple to host. I chose
					SvelteKit because it's a great framework for building static sites. The framework comes
					with a lot of batteries included. The routing is simple and the API is easy to use. HTMX
					could also be used but I chose SvelteKit because I'm more familiar with it.
				</Paragraph>
			</div>
		</section>
	</section>
	<section>
		<Heading tag="h2" class="mb-8">The deployment and hosting</Heading>
		<Paragraph>
			The app is hosted on my own server. The server is a simple VPS running Ubuntu. The app is
			deployed using Docker and Docker Compose and is served using Caddy. The app is deployed using
			Ansible for all the configuration management. Each subsequent deployment is done using GitHub
			Actions. The app is deployed to the server using an SSH connection. The backend and the ETL
			are different services and are deployed separately.
		</Paragraph>
		<Paragraph>
			I run other tools to make my life easier such as my observability stack, to keep track of
			logs, metrics and traces. On top of that, I also run Infisical as a secrets vault, this
			simplifies the handling of secrets and environment variables. Infisical in particular makes it
			so that I can reuse the same CI/CD pipeline for all my projects.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">The future</Heading>
		<div class="grid grid-cols-1 gap-y-3">
			<Paragraph>
				I have a number of ideas for what can come next. They're all listed on GitHub as issues as
				well as on the projects board. The main idea is to improve the retrieval as well as the
				generation. The retrieval can be improved by using agents or by doing things such as
				rewriting the query. The generation can be used by providing more useful context and
				metadata. Before I go into that I want to make sure I have the ability to quantify the
				improvements and measure the impact of any changes made to the system.
			</Paragraph>
		</div>
	</section>
</article>
