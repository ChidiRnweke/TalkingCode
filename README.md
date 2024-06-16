* chatGITpt

The idea behind this project is to create a retrieval augmented generation (RAG) based chatbot that has access to all of your public GitHub code. The project exists of three main components:

1. An ETL pipeline that extracts, transforms and loads the data from the GitHub API to a database. Afterwards, the data is embedded and stored in postgres using the `pgVector` extension.
2. A backend that is capable of taking questions, finding the most relevant code snippets and giving those to chatgpt to generate a response.
3. A frontend that allows you to interact with the chatbot.

The first two components are implemented in Python using respectively Dagster and FastAPI. The frontend is implemented using Sveltekit. The project is currently deployed on my VPS and can be accessed [here](https:/chat.chidinweke.be). 

The project is dockerized and the relevant images are pushed to my github container registry. 


In case you want to run the project locally, you can follow the instructions instructions listed here [here](https://chat.chidinweke.be/host-it-yourself).