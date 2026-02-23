import sys

from tf import runner

from .provider import TerribleProvider


def main(argv=None):
    p = TerribleProvider()
    runner.run_provider(p, argv=argv or sys.argv)


if __name__ == "__main__":
    main()
