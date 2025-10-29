import json
import time

import boto3
from botocore.exceptions import ClientError

from aws_config import load_aws_config

config = load_aws_config()

apigateway_client = boto3.client("apigateway", **config)


def create_rest_api(api_name):
    """Create a new REST API."""
    try:
        response = apigateway_client.create_rest_api(
            name=api_name,
            description="A test API created with LocalStack and Boto3",
            endpointConfiguration={
                "types": ["REGIONAL"]  # Use REGIONAL for LocalStack compatibility
            },
        )
        api_id = response["id"]
        print(f"Created REST API: {api_name} (ID: {api_id})")
        return api_id
    except ClientError as e:
        print(f"Error creating API: {e}")
        return None


def get_root_resource_id(api_id):
    """Get the root resource ID for the API."""
    response = apigateway_client.get_resources(restApiId=api_id)
    root_resource_id = next(
        item["id"] for item in response["items"] if item["path"] == "/"
    )
    print(f"Root resource ID: {root_resource_id}")
    return root_resource_id


def create_child_resource(api_id, parent_resource_id, path_part):
    """Create a child resource (e.g., /test)."""
    try:
        response = apigateway_client.create_resource(
            restApiId=api_id, parentId=parent_resource_id, pathPart=path_part
        )
        child_resource_id = response["id"]
        print(f"Created child resource /{path_part} (ID: {child_resource_id})")
        return child_resource_id
    except ClientError as e:
        print(f"Error creating child resource: {e}")
        return None


def create_method(api_id, resource_id, http_method="GET"):
    """Create a method on the resource."""
    try:
        response = apigateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType="NONE",  # No auth for simplicity
        )
        print(f"Created {http_method} method on resource {resource_id}")
        return response
    except ClientError as e:
        print(f"Error creating method: {e}")
        return None


def create_method_response(api_id, resource_id, http_method="GET"):
    """Define allowed method response (status 200)."""
    try:
        apigateway_client.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode="200",
            responseModels={"application/json": "Empty"},
        )
        print(
            f"Created method response (200) for {http_method} on resource {resource_id}"
        )
    except ClientError as e:
        print(f"Error creating method response: {e}")


def set_mock_integration(
    api_id, resource_id, http_method="GET", response_body="Mock response"
):
    """Set up a mock integration for the method."""
    try:
        # Integration request template: Tells mock to return status 200
        request_template = json.dumps({"statusCode": 200})
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type="MOCK",
            requestTemplates={"application/json": request_template},
        )
        print(f"Set mock integration for {http_method} on resource {resource_id}")
    except ClientError as e:
        print(f"Error setting integration: {e}")


def set_mock_integration_response(
    api_id, resource_id, http_method="GET", response_body="Mock response"
):
    """Map the mock status to a response body."""
    try:
        response_template = json.dumps({"statusCode": 200, "body": response_body})
        apigateway_client.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode="200",
            responseTemplates={"application/json": response_template},
        )
        print(
            f"Set mock integration response for {http_method} on resource {resource_id}"
        )
    except ClientError as e:
        print(f"Error setting integration response: {e}")


def print_resources(api_id):
    """Print all resources for verification."""
    response = apigateway_client.get_resources(restApiId=api_id)
    print("\nCurrent Resources:")
    for item in response["items"]:
        print(f"  Path: {item['path']}, ID: {item['id']}")


def create_deployment(api_id, stage_name="prod"):
    """Deploy the API to a stage."""
    try:
        # Longer delay for full propagation
        time.sleep(10)
        response = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=f"Deployment with full mock setup",
        )
        print(f"Deployed API to stage '{stage_name}'. Deployment ID: {response['id']}")
        return response["id"]
    except ClientError as e:
        print(f"Error deploying API: {e}")
        return None


def get_invoke_url(api_id):
    """Get the invoke URL for the deployed API (LocalStack format)."""
    base_url = f"http://{api_id}.execute-api.localhost.localstack.cloud:4566/prod"
    print(f"\nBase Invoke URL: {base_url}")
    print("Test root: curl -X GET '{base_url}/'")
    print("Test /test: curl -X GET '{base_url}/test'")
    print(
        "Alternative (if DNS issues): http://localhost:4566/_aws/execute-api/{api_id}/prod/"
    )
    return base_url


def setup_rest_api_gateway(api_name: str, http_method: str):
    """Sets up an API gateway."""
    # Step 1: Create the REST API
    api_id = create_rest_api(api_name)
    if not api_id:
        exit(1)

    # Step 2: Get root resource
    root_resource_id = get_root_resource_id(api_id)

    # Step 3: Setup root GET (full mock)
    create_method(api_id, root_resource_id, http_method)
    create_method_response(api_id, root_resource_id, http_method)
    set_mock_integration(api_id, root_resource_id, http_method, "Hello from root!")
    set_mock_integration_response(
        api_id, root_resource_id, http_method, "Hello from root!"
    )

    # Step 4: Create /test child resource
    test_resource_id = create_child_resource(api_id, root_resource_id, "test")
    if test_resource_id:
        # Step 5: Setup /test GET (full mock)
        create_method(api_id, test_resource_id, http_method)
        create_method_response(api_id, test_resource_id, http_method)
        set_mock_integration(api_id, test_resource_id, http_method, "Hello from /test!")
        set_mock_integration_response(
            api_id, test_resource_id, http_method, "Hello from /test!"
        )

        # Step 6: Print resources for verification
        print_resources(api_id)

        # Step 7: Deploy
        deployment_id = create_deployment(api_id)
        if deployment_id:
            # Step 8: Print invoke URLs
            get_invoke_url(api_id)
    else:
        print("Failed to create /test resource; skipping.")
