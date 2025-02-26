import strawberry


def test_defining_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    definition = Node._type_definition

    assert definition.name == "Node"
    assert len(definition.fields) == 1

    assert definition.fields[0].graphql_name == "id"
    assert definition.fields[0].type == strawberry.ID

    assert definition.is_interface


def test_implementing_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    definition = User._type_definition

    assert definition.name == "User"
    assert len(definition.fields) == 2

    assert definition.fields[0].graphql_name == "id"
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].graphql_name == "name"
    assert definition.fields[1].type == str

    assert definition.is_interface is False
    assert definition.interfaces == [Node._type_definition]


def test_implementing_interface_twice():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    @strawberry.type
    class Person(Node):
        name: str

    definition = User._type_definition

    assert definition.name == "User"
    assert len(definition.fields) == 2

    assert definition.fields[0].graphql_name == "id"
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].graphql_name == "name"
    assert definition.fields[1].type == str

    assert definition.is_interface is False
    assert definition.interfaces == [Node._type_definition]

    definition = Person._type_definition

    assert definition.name == "Person"
    assert len(definition.fields) == 2

    assert definition.fields[0].graphql_name == "id"
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].graphql_name == "name"
    assert definition.fields[1].type == str

    assert definition.is_interface is False
    assert definition.interfaces == [Node._type_definition]


def test_interfaces_can_implement_other_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.interface
    class UserNodeInterface(Node):
        id: strawberry.ID
        name: str

    @strawberry.type
    class Person(UserNodeInterface):
        id: strawberry.ID
        name: str

    assert UserNodeInterface._type_definition.is_interface is True
    assert UserNodeInterface._type_definition.interfaces == [Node._type_definition]

    definition = Person._type_definition
    assert definition.is_interface is False
    assert definition.interfaces == [
        UserNodeInterface._type_definition,
        Node._type_definition,
    ]
