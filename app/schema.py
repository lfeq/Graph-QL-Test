from ariadne import QueryType, MutationType, EnumType, make_executable_schema, gql, ScalarType
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from graphql import GraphQLError
from .db import get_db_session  # Importar el generador de sesión
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
        hasBeenViewed: Boolean!
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

    type Query {
        futureViewings(page: Int = 1, pageSize: Int = 20): [FutureViewing!]!
        recentFutureViewings(page: Int = 1, pageSize: Int = 20): [FutureViewing!]!
    }

    type Mutation {
        addFutureViewing(input: AddFutureViewingInput!): AddFutureViewingPayload!
    }
""")

# Tipos de Query

datetime_scalar = ScalarType("DateTime")

@datetime_scalar.serializer
def serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None # Or raise an error if the type is unexpected

@datetime_scalar.value_parser
def parse_datetime_value(value):
    # This is called when the value is part of the input variables
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise GraphQLError(f"'{value}' is not a valid ISO 8601 datetime string.")

@datetime_scalar.literal_parser
def parse_datetime_literal(ast, variables=None):
    # This is called when the value is an inline argument in the query
    from graphql import StringValueNode
    if not isinstance(ast, StringValueNode):
        raise GraphQLError(f"DateTime scalar expects a string literal, got {type(ast)}")
    try:
        return datetime.fromisoformat(ast.value)
    except (ValueError, TypeError):
        raise GraphQLError(f"'{ast.value}' is not a valid ISO 8601 datetime string.")

query = QueryType()


@query.field("futureViewings")
async def resolve_future_viewings(_, info, page=1, pageSize=20):
    db: AsyncSession = info.context["db"]  # Obtener sesión de BD del contexto
    viewings = await crud.get_future_viewings_paginated(db, page=page, page_size=pageSize)
    return [v.to_dict() for v in viewings]


@query.field("recentFutureViewings")
async def resolve_recent_future_viewings(_, info, page=1, pageSize=20):
    db: AsyncSession = info.context["db"]
    viewings = await crud.get_recent_future_viewings_and_mark_viewed(db, page=page, page_size=pageSize)
    return [v.to_dict() for v in viewings]


# Tipos de Mutation
mutation = MutationType()


@mutation.field("addFutureViewing")
async def resolve_add_future_viewing(_, info, input):
    db: AsyncSession = info.context["db"]
    name = input["name"]
    age = input["age"]
    content = input["content"]

    # Validation for name
    if not name or name.isspace():
        raise GraphQLError("Name cannot be empty.")
    if len(name) > 100:
        raise GraphQLError("Name must be 100 characters or less.")

    # Validation for age
    if not isinstance(age, int):
        raise GraphQLError("Age must be an integer.") # Should be caught by GraphQL scalar type usually
    if not (1 <= age <= 120):
        raise GraphQLError("Age must be between 1 and 120.")

    # Validation for content
    if not content or content.isspace():
        raise GraphQLError("Content cannot be empty.")
    if len(content) > 4000:
        raise GraphQLError("Content must be 4000 characters or less.")

    fv = await crud.create_future_viewing(db, name=name, age=age, content=content)

    # Encolar la tarea de generación de imagen
    # Pasa el ID como string porque es más fácil de serializar si fuera necesario para colas externas
    await enqueue_image_generation(str(fv.id), fv.name, fv.age, fv.content)

    return {"futureViewing": fv.to_dict()}


# EnumType para mapear el enum de Python al de GraphQL
# El nombre 'ProcessingStatus' debe coincidir con el nombre del enum en tu `type_defs`
processing_status_enum = EnumType("ProcessingStatus", PyProcessingStatus)

# Crear el esquema ejecutable
# Asegúrate de incluir todos los QueryType, MutationType, y EnumType que definas.
schema = make_executable_schema(type_defs, query, mutation, processing_status_enum, datetime_scalar)