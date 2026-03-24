import sys

from tf.runner import run_provider

from .provider import TerribleProvider


def main(argv=None):
    run_provider(TerribleProvider(), argv or sys.argv)


if __name__ == "__main__":
    main()
