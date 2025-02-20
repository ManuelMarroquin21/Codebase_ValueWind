from PyWakeModel import PyWakeModel

class FarmSurrogateQuery:
    def __init__(self, metEnv, wind_farm_data):
        self.surrogate_data = wind_farm_data
        self.metEnv = metEnv
        self.surrogate_model = PyWakeModel()
        # here the surrogate model should be initialized depending on provided flags. PyWake, FLORIS, etc.
        #if self.surrogate_data.PyWake == True:



        # inputs: ambient flow conditions (V, TI, WD)
        # outputs: Turbine inflow conditions (V, TI, WD)

    def get_windFarm_response_timestep(self, control_output):


        # get the inputs from the metEnv
        ws= self.metEnv.get_wind_speed()
        wd = self.metEnv.get_wind_direction()
        ti = self.metEnv.get_TI()


        sim_res = self.surrogate_model.get_windFarm_response_timestep(ws, wd, ti, control_output)
        return sim_res


    def get_windFarm_response_global(self, control_output):

        sim_res = self.surrogate_model.get_windFarm_response_global()
        return sim_res

    def get_turbine_inflow(self, turbine, control_output):
        v_ambient = self.metEnv.get_wind_speed()
        ti_ambient = self.metEnv.get_TI()
        #wd_ambient = self.metEnv.get_wind_direction()
    
        # here the surrogate model would be called to get the turbine inflow conditions
        # for now, we just return the ambient conditions
        return {'Vreq': v_ambient, 'TIreq': ti_ambient}
    
