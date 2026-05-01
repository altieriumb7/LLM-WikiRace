class TacticalModel:
    def __init__(self, impl): self.impl=impl
    def rank(self, payload): return self.impl.rank(payload)
