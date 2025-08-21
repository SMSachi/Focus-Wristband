class BaselineEMA:
    def __init__(self, alpha=0.05):
        self.alpha = alpha
        self.ema = None

    def update(self, new_value):
        if self.ema is None:
            self.ema = new_value
        else:
            self.ema = self.alpha * new_value + (1 - self.alpha) * self.ema
        return self.ema
