# scripts/deploy_fabric.py
import os
from fabric_cicd import deploy_with_config
from azure.identity import ClientSecretCredential


def main() -> None:
    credential = ClientSecretCredential(
        tenant_id=os.environ["FABRIC_TENANT_ID"],
        client_id=os.environ["FABRIC_CLIENT_ID"],
        client_secret=os.environ["FABRIC_CLIENT_SECRET"],
    )

    result = deploy_with_config(
        config_file_path=os.environ["CONFIG_PATH"],
        token_credential=credential,
        environment=os.environ["ENVIRONMENT"],
    )

    print(f"Deployment status: {result.status}")
    print(f"Message: {result.message}")

    responses = getattr(result, "responses", None)
    if responses:
        print("Collected responses:", responses)


if __name__ == "__main__":
    main()