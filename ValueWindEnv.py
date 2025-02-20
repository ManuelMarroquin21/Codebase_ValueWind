import simpy
from CAPEX import CAPEX
from FINEX import FINEX
from MetEnvironment import MetEnvironment
from WindFarm import WindFarm
from Valuation import Valuation
from MarketEnvironment import MarketEnv

class ValueWindEnv(simpy.Environment):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.metEnv= MetEnvironment(self)
        self.windFarm = WindFarm(self)
        self.capex = CAPEX(self)
        self.finex = FINEX(self, self.capex)
        self.valuation = Valuation(self)
        self.MarketEnv = MarketEnv(self)

    def run_simulation(self, until=None):
        # Start the CAPEX process in the environment
        self.capex.start()

        # Start the wind farm process in the environment
        self.windFarm.start()

        # Run the simulation up to the specified time or the Project_Duration
        self.run(until=until or self.config.Project_Duration_h)

        # Call the Fatigue Analysis process after the simulation ends
        #self.windFarm.get_FatigueAnalysis() # This should only trigger post simulation fatigue analysis. Damage calculation should be done in the simulation step.

        # Perform DCF calculation after CAPEX has been processed
        #self.total_discounted_cost = self.finex.discount_cost()

        