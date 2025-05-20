from ariadne import QueryType, MutationType, EnumType, make_executable_schema, gql
from sqlalchemy.ext.asyncio import AsyncSession
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
schema = make_executable_schema(type_defs, query, mutation, processing_status_enum)