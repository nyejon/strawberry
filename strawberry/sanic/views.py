import json
from typing import Any

from sanic.exceptions import ServerError, abort
from sanic.request import Request
from sanic.response import HTTPResponse, html
from sanic.views import HTTPMethodView
from strawberry.file_uploads.data import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionContext, ExecutionResult

from ..schema import BaseSchema
from .context import StrawberrySanicContext
from .graphiql import render_graphiql_page
from .utils import convert_request_to_files_dict


class GraphQLView(HTTPMethodView):
    """
    Class based view to handle GraphQL HTTP Requests

    Args:
        schema: strawberry.Schema
        graphiql: bool, default is True

    Returns:
        None

    Example:
        app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=True),
            "/graphql"
        )
    """

    methods = ["GET", "POST"]

    def __init__(self, schema: BaseSchema, graphiql: bool = True):
        self.graphiql = graphiql
        self.schema = schema

    def get_root_value(self):
        return None

    async def get_context(self, request: Request) -> Any:
        return StrawberrySanicContext(request)

    def render_template(self, template=None):
        return html(template)

    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    async def dispatch_request(self, request: Request):  # type: ignore
        request_method = request.method.lower()
        if not self.graphiql and request_method == "get":
            abort(404)

        show_graphiql = request_method == "get" and self.should_display_graphiql(
            request
        )

        if show_graphiql:
            template = render_graphiql_page()
            return self.render_template(template=template)

        operation_context = self.get_execution_context(request)
        context = await self.get_context(request)
        root_value = self.get_root_value()

        result = await self.schema.execute(
            query=operation_context.query,
            variable_values=operation_context.variables,
            context_value=context,
            root_value=root_value,
            operation_name=operation_context.operation_name,
        )
        response_data = self.process_result(result)

        return HTTPResponse(
            json.dumps(response_data), status=200, content_type="application/json"
        )

    def get_execution_context(self, request: Request) -> ExecutionContext:
        try:
            data = self.parse_body(request)
        except json.JSONDecodeError:
            raise ServerError("Unable to parse request body as JSON", status_code=400)

        try:
            query = data["query"]
        except KeyError:
            raise ServerError("No GraphQL query found in the request", status_code=400)

        variables = data.get("variables")
        operation_name = data.get("operationName")

        return ExecutionContext(
            query=query, variables=variables, operation_name=operation_name
        )

    def parse_body(self, request: Request) -> dict:
        if request.content_type.startswith("multipart/form-data"):
            files = convert_request_to_files_dict(request)
            operations = json.loads(request.form.get("operations", "{}"))
            files_map = json.loads(request.form.get("map", "{}"))
            try:
                return replace_placeholders_with_files(operations, files_map, files)
            except KeyError:
                abort(400, "File(s) missing in form data")
        return request.json

    def should_display_graphiql(self, request):
        if not self.graphiql:
            return False
        return self.request_wants_html(request)

    @staticmethod
    def request_wants_html(request: Request):
        accept = request.headers.get("accept", {})
        return "text/html" in accept or "*/*" in accept
