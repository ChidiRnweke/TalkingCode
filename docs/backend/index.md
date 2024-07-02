# Overview

## Introduction

This documentation is focused on the backend of the ChatGITpt project. The backend is a FastAPI application that serves the endpoints for the frontend. The backend is responsible for handling the requests from the frontend, processing the requests, and returning the responses. The backend is also responsible for interacting with the database and the external APIs.


## Structure

The [architecture](architecture.md) offers an overview of the backend. On a high level, the backend is divided into the following components:

- [Main](reference/main.md): The main module that starts the FastAPI application.
- [Config](reference/config.md): The configuration module that loads the configuration from the environment variables.
- [Errors](reference/errors.md): The errors module that defines the custom exceptions that are used in the backend.
- [Services](reference/retrieve.md): The services module that contains the services that interact with the database and the external APIs.
  
Most of the logic of the backend is in the services. The project makes use of dependency injection to facilitate testing. The services are designed to be testable. The services are tested using a combination of unit and integration tests. The tests are written using the `pytest` framework. The tests are located in the `tests` directory. You can read more about the testing strategy [here](testing.md).

## Endpoints

The backend exposes the following endpoints:

* `/chat`: The endpoint that handles the chat requests. The endpoint accepts a JSON payload with the user's message and returns a JSON payload with the bot's response. The endpoint uses the `RetrievalAugmentedGeneration` service to generate the bot's response.
* `/remaining-space`: The endpoint that handles the remaining space requests. The endpoint returns the remaining space in the database. The endpoint uses the `SQLRetrievalService` to retrieve the remaining space in the database.

You can read more about them in the OpenAPI documentation [here](openapi.json).

## Reference

You should start by reading the [main](reference/main.md) module. The main module is the entry point of the FastAPI application. It contains the configuration of the FastAPI application and the routes that are exposed by the FastAPI application. From there on you can read the other modules in any order. 

## Extras

Make sure to check out my personal website's [dedicated page](https://chat.chidinweke.be/host-it-yourself/) for instructions on how to host the project yourself. The instructions are detailed and should be easy to follow. If you have any questions, feel free to reach out to me.

You should also check out the source code of the project on [GitHub](https://github.com/ChidiRnweke/chatGITpt).

Enjoy the documentation!