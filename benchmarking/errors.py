RESULT_TIMEOUT = {"score": float("nan")}


class StageError(Exception):
    def __init__(self, stage: str, original: Exception):
        super().__init__(f"{stage} failed: {original}")
        self.stage = stage
        self.original = original
