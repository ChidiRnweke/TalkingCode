# Architecture

The architecture of the backend isn't following any specific pattern but is rather a loose collection of what I consider to be best practices for any backend system. 

## API layer

The API layer is responsible for handling incoming requests and dealing with possible errors. It is built with FastAPI. There is no business logic in the API layer. It is solely responsible for serializing, deserializing, and routing requests to the right service.

## Error handling

The error handling is done using custom exceptions and the "app error" pattern. I encourage you to read the [errors](reference/errors.md) module for more information as well as the [relevant handler](reference/main.md/#backend.main.handle_app_errors) defined in the API layer. 

The summary is that custom exceptions are defined in the `errors` module. These exceptions are easily created (ang logged) using the `map_errors` context manager. The exceptions are caught in the API layer and converted to a JSON response. A fixed set of errors is defined in the `errors` module. The errors are defined in a way that they can be easily extended.

In the future I will integrate a solution like Sentry to log the errors.

## Services

The main "service" is the `RetrievalAugmentedGeneration` service. This service is responsible for generating the bot's response. It carries a number of dependencies that are injected into it. The dependencies are the `EmbeddingService`,`GenerationService` and `RetrievalService`. The `EmbeddingService` is responsible for converting the user's message into an embedding. The `GenerationService` is responsible for generating a response from an embedding. The `RetrievalService` is responsible for retrieving the most similar embeddings from the database.

Using dependency injection makes the service testable. The dependencies can be easily stubbed out. This service is tested using a combination of unit and integration tests. The tests are written using the `pytest` framework. You can read more about the testing strategy [here](testing.md).

## Database

The database used is PostgresSQL with the `pgVector` extension. This turns the database into a two-in-one database. It can store regular data as well as vectors. The vectors are used to store the embeddings of the user's messages. The database is accessed using the `SQLRetrievalService`. The `SQLRetrievalService` is responsible for retrieving the most similar embeddings from the database. The database is spun up using `Testcontainers` in the integration tests.


## Configuration

The configuration is loaded from the environment variables. The configuration is loaded in the `config` module. The configuration is loaded in the `main` module and passed to the FastAPI application. The configuration is used to configure the services among other things. A full list of the configuration options can be found [here](https://chat.chidinweke.be/host-it-yourself/).