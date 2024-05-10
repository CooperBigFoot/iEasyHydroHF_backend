class DailyPrecipitationCodeMapper:
    def __init__(self, code: int):
        self.code = code
        self._code_description_map = self._generate_map()

    @staticmethod
    def _generate_map() -> dict[int, str]:
        return {0: "< 1h", 1: "1h - 3h", 2: "3h - 6h", 3: "6h - 12h", 4: "> 12h"}

    def get_description(self) -> str:
        return self._code_description_map.get(self.code, "-")
