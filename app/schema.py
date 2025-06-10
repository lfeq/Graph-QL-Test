import uuid  # Added for screenId conversion
from ariadne import QueryType, MutationType, EnumType, make_executable_schema, gql
from graphql import GraphQLError
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db_session, AsyncSessionLocal  # Importar el generador de sesión
from . import crud
from .models import ProcessingStatus as PyProcessingStatus, FutureViewing as ModelFutureViewing
from .background import enqueue_image_generation

# Cargar la definición del esquema desde un string
# (Podrías también cargarlo desde un archivo .graphql)
type_defs = gql("""
    scalar DateTime

    enum ProcessingStatus {
        PENDING
        COMPLETED
        FAILED
    }

    type FutureViewing {
        id: ID!
        name: String!
        age: Int!
        content: String!
        createdAt: DateTime!
        imageUrl: String
        status: ProcessingStatus!
    }

    input AddFutureViewingInput {
        name: String!
        age: Int!
        content: String!
    }

    type AddFutureViewingPayload {
        futureViewing: FutureViewing
        # Puedes añadir userErrors aquí si implementas validación más compleja
    }

    # Input type for registering a new screen.
    input RegisterScreenInput {
        # Optional friendly name for the screen.
        name: String
    }

    # Represents a display screen.
    type Screen {
        # Unique identifier for the screen.
        id: ID!
        # Optional friendly name of the screen.
        name: String
        # Timestamp of when the screen was registered.
        createdAt: DateTime!
    }

    # Payload type for the registerScreen mutation.
    type RegisterScreenPayload {
        # The newly registered screen, if successful.
        screen: Screen
        # userErrors: [UserError!] # Placeholder for future error handling.
    }

    type Query {
        futureViewings(page: Int = 1, pageSize: Int = 20): [FutureViewing!]!
        # Fetches recent FutureViewings that have not yet been displayed on a specific screen.
        # Marks fetched viewings as displayed on the given screen.
        recentFutureViewings(
            # The ID of the screen making the request. This is mandatory to ensure
            # viewings are correctly tracked per screen.
            screenId: ID!,
            page: Int = 1,
            pageSize: Int = 20
        ): [FutureViewing!]!
    }

    type Mutation {
        addFutureViewing(input: AddFutureViewingInput!): AddFutureViewingPayload!
        # Mutation to register a new screen.
        registerScreen(input: RegisterScreenInput!): RegisterScreenPayload!
    }
""")

# Tipos de Query
query = QueryType()


@query.field("futureViewings")
async def resolve_future_viewings(_, info, page=1, pageSize=20):
    async with AsyncSessionLocal() as db:
        viewings = await crud.get_future_viewings_paginated(db, page=page, page_size=pageSize)
        return [v.to_dict() for v in viewings]


@query.field("recentFutureViewings")
async def resolve_recent_future_viewings(_, info, screenId, page=1, pageSize=20):
    """
    Resolves the `recentFutureViewings` GraphQL query.

    Fetches FutureViewing items that are completed, created in the last 24 hours,
    and not yet viewed on the specified screen. It then marks these items as viewed
    on that screen by creating ScreenViewings entries.
    Handles potential ValueError if screenId is not a valid UUID, raising GraphQLError.

    Args:
        _ : The parent object, typically not used in root resolvers.
        info: GraphQL resolve info, contains context like the db session.
        screenId (str): The ID of the screen (as a string from GraphQL) requesting viewings.
        page (int): The page number for pagination.
        pageSize (int): The number of items per page.

    Returns:
        list[dict]: A list of FutureViewing objects (as dictionaries via to_dict())
                    to be displayed on the screen.
    Raises:
        GraphQLError: If the provided screenId is not a valid UUID.
    """
    async with AsyncSessionLocal() as db:
        try:
            screen_id_uuid = uuid.UUID(screenId)
        except ValueError:
            raise GraphQLError("Invalid screenId format. Please provide a valid UUID.")

        viewings = await crud.get_recent_future_viewings_and_mark_viewed(
            db, screen_id=screen_id_uuid, page=page, page_size=pageSize
        )
        return [v.to_dict() for v in viewings]


# Tipos de Mutation
mutation = MutationType()


@mutation.field("addFutureViewing")
async def resolve_add_future_viewing(_, info, input):
    """
    Resolves the `addFutureViewing` GraphQL mutation.

    Creates a new FutureViewing record based on the provided input,
    and enqueues a background task for image generation.

    Args:
        _ : The parent object, typically not used in root resolvers.
        info: GraphQL resolve info, contains context like the db session.
        input (dict): A dictionary containing the input fields for the new
                      FutureViewing (name, age, content).

    Returns:
        dict: A payload containing the newly created FutureViewing object
              (as a dictionary via to_dict()).
    """
    async with AsyncSessionLocal() as db:
        name = input["name"]
        age = input["age"]
        content = input["content"]

        fv = await crud.create_future_viewing(db, name=name, age=age, content=content)

        # Encolar la tarea de generación de imagen
        # Pasa el ID como string porque es más fácil de serializar si fuera necesario para colas externas
        await enqueue_image_generation(str(fv.id), fv.name, fv.age, fv.content)

        return {"futureViewing": fv.to_dict()}


@mutation.field("registerScreen")
async def resolve_register_screen(_, info, input):
    """
    Resolves the `registerScreen` GraphQL mutation.

    Registers a new screen, optionally with a name.

    Args:
        _ : The parent object, typically not used in root resolvers.
        info: GraphQL resolve info, contains context like the db session.
        input (dict): A dictionary containing the input fields for screen registration.
                      May contain an optional 'name' for the screen.

    Returns:
        dict: A payload containing the newly registered Screen object
              (as a dictionary via to_dict()).
    """
    async with AsyncSessionLocal() as db:
        name = input.get("name")  # Optional name

        registered_screen = await crud.register_screen(db, screen_name=name)
        return {"screen": registered_screen.to_dict()}


# EnumType para mapear el enum de Python al de GraphQL
# El nombre 'ProcessingStatus' debe coincidir con el nombre del enum en tu `type_defs`
processing_status_enum = EnumType("ProcessingStatus", PyProcessingStatus)

# Crear el esquema ejecutable
# Asegúrate de incluir todos los QueryType, MutationType, y EnumType que definas.
schema = make_executable_schema(type_defs, query, mutation, processing_status_enum)