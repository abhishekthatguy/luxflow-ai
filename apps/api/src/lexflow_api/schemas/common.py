from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PaginationMeta(CamelModel):
    page: int
    page_size: int = Field(alias="pageSize")
    total_items: int = Field(alias="totalItems")
    total_pages: int = Field(alias="totalPages")


class ResponseMeta(CamelModel):
    request_id: str = Field(alias="requestId")
    timestamp: str
    pagination: PaginationMeta | None = None


class Envelope[T](CamelModel):
    data: T
    meta: ResponseMeta


def build_meta(
    request_id: str | None = None,
    pagination: PaginationMeta | None = None,
) -> ResponseMeta:
    return ResponseMeta(
        requestId=request_id or str(uuid4()),
        timestamp=datetime.now(UTC).isoformat(),
        pagination=pagination,
    )


def envelope[T](
    data: T,
    request_id: str | None = None,
    pagination: PaginationMeta | None = None,
) -> Envelope[T]:
    return Envelope(data=data, meta=build_meta(request_id, pagination))


def pagination_meta(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = max(1, (total_items + page_size - 1) // page_size) if page_size else 1
    return PaginationMeta(
        page=page,
        pageSize=page_size,
        totalItems=total_items,
        totalPages=total_pages,
    )
