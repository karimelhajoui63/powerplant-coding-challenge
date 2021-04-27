from itertools import combinations

class Algo():
    """  
        Contains algorithms to calculate which powerplants to activate in order 
        to obtain the desired load at minimum cost
    """

    def __init__(self, powerplants, load):
        self.powerplants = powerplants
        self.load = load
        self.unit_commitment = []


    def calc_unit_commitment(self):
        """
            Calculate the powerplants to be activated in order to have an optimal yield.

            Algorithm used :
            ----------------
                * Sort of powerplants by cost per MWh
                * Generate all possible combinations of wind-turbine use
                * For every combination:
                    * Generate all possible combinations of gas-fired powerplant use
                    * For every combination:
                        * Try to add each gas-fired powerplant one by one.
                          Two ways to add it:
                            1) directly: case where min power > remaining load
                            2) by resizing: case where it is only possible to 
                               add it by decreasing the power supplied by the 
                               previous gas-fired powerplant
                        * If it could be added, check if this configuration is possible
                        * If it is a possible configuration, save it if it is the cheapest 
            
            Return a list of dict {"name": pp_name, "p": power} (see the 
            template of the response expected in 'example_response.json').
        """
        # Sort of powerplants by cost per MWh
        merit_order = sorted(
            [pp for pp in self.powerplants],
            key=lambda pp: pp.cost_per_MWh
        )
        self.wind_merit_order  = [pp for pp in merit_order if pp.type == "windturbine"]
        self.gas_merit_order   = [pp for pp in merit_order if pp.type == "gasfired"]
        self.turbo_merit_order = [pp for pp in merit_order if pp.type == "turbojet"]
        # Calculate the maximum power that can be delivered by the turbojets
        self.p_turbo_max = sum([pp.epmax for pp in self.turbo_merit_order])

        # For all possible combinations of wind-turbine use
        for self.wind_config in self.generate_wind_config():
            if self.wind_config:
                # Calculate the power delivered by this combination
                p_wind = sum([pp.epmax for pp in self.wind_config])
            else:
                # Case where no wind-turbine is used
                p_wind = 0
            
            # For all possible combinations of gas-fired powerplant use
            for self.gas_config in self.generate_gas_config():
                self.load_left = self.load - p_wind
                self.p_min, self.p_max = 0, 0
                # If not gas-fired powerplant is used, check the configuration
                if not self.gas_config:
                    self.check_config(p_wind)
                # Reset the powers (p_output) used for the previous configuration
                self.reset_config(self.gas_config)

                # Try to use each powerplant in the configuration in the merit-order
                for i, gas_pp in enumerate(self.gas_config):
                    # Case where the powerplant can fit in directly
                    if gas_pp.epmin <= self.load_left:
                        self.fit_gas_pp_directly(p_wind, gas_pp)
                    # Case where the powerplant can fit in only if we resize the other powerplants
                    elif self.load_left != 0 and \
                    gas_pp.epmin <= self.load_left + (self.p_max - self.p_min):
                        self.fit_gas_pp_by_resizing(p_wind, gas_pp, i)
        return self.unit_commitment


    def generate_wind_config(self):
        """ 
            Return every possible combinations of wind-turbine use.

            If a wind-turbine is not present in a combination, it must be 
            considered as switched off.
        """
        # Initialized with empty brackets if no wind-turbine is used
        possible_wind_p = [()] 
        for n in range(len(self.wind_merit_order)):
            for config in combinations(self.wind_merit_order, n+1):
                possible_wind_p.append(config)
        return possible_wind_p


    def generate_gas_config(self):
        """ 
            Return every possible combinations of gas-fired powerplant use.

            If a gas-fired powerplant is not present in a combination, 
            it must be considered as switched off.
        """
        # Initialized with empty brackets if no gas-fired powerplant is used
        possible_gas_p = [()] 
        for n in range(len(self.gas_merit_order)):
            for config in combinations(self.gas_merit_order, n+1):
                possible_gas_p.append(config)
        return possible_gas_p


    def compute_turbo_config(self, p_needed):
        """ 
            Save in the 'turbo_config' class attribute the cheapest 
            configuration to provide the power entered as a parameter. 

            Every turbojet is present in the 'turbo_config'.
            (as opposed to 'wind_config' and 'gas_config')
        """
        self.turbo_config = []
        # Browse the whole list to reset to 0 the turbojet powerplants not used
        for turbo_pp in self.turbo_merit_order:
            turbo_pp.p_output = min(turbo_pp.epmax, p_needed)
            p_needed -= turbo_pp.p_output
            self.turbo_config.append(turbo_pp)


    def reset_config(self, config):
        """ 
            Reset all power outputs in the configuration provided in parameter 
        """
        for pp in config:
            pp.p_output = 0


    def fit_gas_pp_directly(self, p_wind, gas_pp):
        """
            Try to add the gas-fired powerplant provided in parameter directely.
            (case where min power > remaining load)
        """
        gas_pp.p_output = min(gas_pp.epmax, self.load_left)
        self.p_max += gas_pp.p_output
        self.load_left -= gas_pp.p_output
        self.p_min += gas_pp.epmin
        # check if it's a possible configuration, and save if it's the best (so far)
        self.check_config(p_wind)


    def fit_gas_pp_by_resizing(self, p_wind, gas_pp, gas_pp_idx):
        """
            Try to add the gas-fired powerplant provided in parameter by 
            resizing. (case where it is only possible to add it by decreasing 
            the power supplied by the previous gas-fired powerplant)
        """
        # Browse previous gas-fired powerplants to remove power
        for j in range(gas_pp_idx-1, -1, -1):
            p_needed = gas_pp.epmin - self.load_left
            p_taken = min(self.gas_config[j].p_output, p_needed)
            # Update previous gas-fired powerplant output power
            self.gas_config[j].p_output -= p_taken
            self.p_max -= p_taken
            p_needed -= p_taken
            if p_needed == 0:
                self.p_max += gas_pp.epmin
                self.p_min += gas_pp.epmin
                # The gas-fired powerplant has been added, we can stop
                break
        # check if it's a possible configuration, and save if it's the best (so far)
        self.check_config(p_wind)


    def check_config(self, p_wind):
        """ 
            Check if there is a turbojet configuration that can be used to 
            have the load needed and try to save it if it's the case.
        """
        if self.is_possible_config(p_wind, p_gas=self.p_max):
            p_turbo = self.load - self.p_max - p_wind
            self.compute_turbo_config(p_turbo)
            self.keep_config_if_better()

            
    def is_possible_config(self, p_wind, p_gas):
        """ 
            Return 'True' if there is a turbojet configuration that can be used 
            to have the load needed, 'False' else.
        """
        if self.load - self.p_turbo_max <= p_wind + p_gas <= self.load:
            return True
        return False


    def keep_config_if_better(self):
        """
            Save the configuration in 'unit_commitment' if there is no
            better (cheaper) configuration.
        """
        current_cost = self.get_total_cost()
        if not hasattr(self, "best_cost") or current_cost < self.best_cost:
            self.best_cost = current_cost

            unit_commitment_dict = self.init_unit_commitment_dict()
            # Update the powers of the powerplants according to the configurations
            for pp in self.wind_config:
                # The wind-turbine can only be switched ON or OFF
                unit_commitment_dict[pp.name] = pp.epmax
            for pp in self.gas_config:
                unit_commitment_dict[pp.name] = pp.p_output
            for pp in self.turbo_config:
                unit_commitment_dict[pp.name] = pp.p_output

            self.unit_commitment = self.convert_into_list(unit_commitment_dict)


    def init_unit_commitment_dict(self):
        """
            Initializes et return the unit-commitment to the dict format in 
            order to facilitate the modification of the powers of each powerplant.
            
            This unit-commitment will be converted into a list after modifications.
        """
        unit_commitment_dict = {}
        for pp in self.powerplants:
            unit_commitment_dict[pp.name] = 0
        return unit_commitment_dict

        
    def print_config(self):
        """ 
            Print the current configuration 
        """
        print('*'*100)
        for pp in self.wind_config:
            print(f"{pp.name} -> {pp.get_cost():.2f}€ for {pp.epmax:.1f} MWh")
        for pp in self.gas_config:
            print(f"{pp.name} -> {pp.get_cost():.2f}€ for {pp.p_output:.1f} MWh")
        for pp in self.turbo_config:
            print(f"{pp.name} -> {pp.get_cost():.2f}€ for {pp.p_output:.1f} MWh")
        print()
        current_cost = self.get_total_cost()
        print(f"TOTAL COST = {current_cost:.2f}€")
        print('*'*100)

        
    def convert_into_list(self, unit_commitment_dict):
        """
            Convert the unit-commitment from a dictionary format to a list format.

            The dictionary is used to facilitate le update of powers.
            The list is used to create the good output format expected 
            (see 'example_response.json').
        """
        unit_commitment = []
        for name, p in unit_commitment_dict.items():
            unit_commitment.append({
                "name": name,
                "p": round(p, 4)
            })
        return unit_commitment
        


    def get_total_cost(self):
        """ 
            Return the cost of the currect configuration 
        """
        cost = 0
        for pp in self.gas_config:
            cost += pp.get_cost()
        for pp in self.turbo_config:
            cost += pp.get_cost()
        return cost
