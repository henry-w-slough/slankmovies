

class InvalidM3U8Exception(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

        print("Th")