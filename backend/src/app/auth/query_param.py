from typing import Annotated

from fastapi import Query


TokenQueryParam = Annotated[
    str, 
    Query(..., description="Токен полученный по почте."),
]
