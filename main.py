import sys
from ProcessingManager import ProcessingManager


def main():
    ProcessingManager(year=sys.argv[1], month=sys.argv[2])


if __name__ == "__main__":
    main()
