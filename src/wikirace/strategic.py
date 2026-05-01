class StrategicModel:
    def __init__(self, impl): self.impl=impl
    def plan(self, payload): return self.impl.plan(payload)
