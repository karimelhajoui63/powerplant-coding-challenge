class PowerPlant():
    wind_percent = 0

    def __init__(self, name, type, efficiency, pmin, pmax):
        self.name = name
        self.type = type
        self.efficiency = efficiency
        self.pmin = pmin
        self.pmax = pmax
        # Effective power
        self.epmin = round(self.pmin * efficiency, 1)
        self.epmax = round(self.pmax * efficiency, 1)
        # Power output
        self.p_output = 0

    def compute_cost_per_MWh(self, prices_per_MWh):
        self.cost_per_MWh = round(prices_per_MWh[self.type] / self.efficiency, 1)

    def get_cost(self):
        """ Get cost of the actual power currently delivered """
        return self.cost_per_MWh * self.p_output

    @staticmethod
    def create_pp(**kwargs):
        """ Allow to create a child-class instance at run-time """
        pp_type = kwargs["type"]
        if pp_type == "windturbine":
            return WindTurbine(**kwargs)
        elif pp_type == "gasfired":
            return GasFired(**kwargs)
        elif pp_type == "turbojet":
            return TurboJet(**kwargs)

    def __repr__(self):
        return f"{'-'*50}\n{self.name} ({self.type}):\n"\
               f"efficiency = {self.efficiency}\n"\
               f"cost_per_MWh = {self.cost_per_MWh if hasattr(self, 'cost_per_MWh') else None}\n"\
               f"pmin = {self.pmin}, pmax = {self.pmax}\n"\
               f"epmin = {self.epmin}, epmax = {self.epmax}\n{'-'*50}\n"


class WindTurbine(PowerPlant):
    def __init__(self, name, type, efficiency, pmin, pmax):
        super().__init__(name, type, super().wind_percent/100, pmax, pmax)

    def compute_cost_per_MWh(self, prices_per_MWh):
        self.cost_per_MWh = 0


class GasFired(PowerPlant):
    pass


class TurboJet(PowerPlant):
    pass
