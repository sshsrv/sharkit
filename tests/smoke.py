import sharkit
from sharkit.modules.testing.demo.echo import EchoModule
from sharkit.modules.testing.http.metadata import HttpMetadataModule


def main() -> None:
    assert sharkit.__version__
    assert EchoModule is not None
    assert HttpMetadataModule is not None
    print("smoke test OK")


if __name__ == "__main__":
    main()
