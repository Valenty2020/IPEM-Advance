from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import uvicorn
import logging
from originalmodel import Analytics_Model2

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pure Payload Economics Model API",
    description="API for chemical plant analysis using ONLY payload values",
    version="3.0.0"
)

class AnalysisRequest(BaseModel):
    # Previously required fields now optional
    location: Optional[str] = None
    product: Optional[str] = None
    
    # Plant configuration
    plant_effy: str
    plant_size: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
    
    # Economic parameters
    operating_prd: int
    util_operating_first: float
    util_operating_second: float
    util_operating_third: float
    infl: float
    RR: float
    IRR: float
    construction_prd: int
    capex_spread: List[float]
    shrDebt_value: float
    baseYear: int
    ownerCost: float
    corpTAX_value: float
    
    # Prices
    Feed_Price: float
    Fuel_Price: float
    Elect_Price: float
    CarbonTAX_value: float
    credit_value: float
    
    # Capital/Operating
    CAPEX: float
    OPEX: float
    PRIcoef: float
    CONcoef: float
    
    # Technical parameters
    EcNatGas: float
    ngCcontnt: float
    eEFF: float
    hEFF: float
    Cap: float
    Yld: float
    feedEcontnt: float
    Heat_req: float
    Elect_req: float
    feedCcontnt: float

@app.on_event("startup")
async def startup_event():
    """Load multiplier data (if still needed for non-payload calculations)"""
    global multipliers
    try:
        multipliers = pd.read_csv("./sectorwise_multipliers.csv")
    except FileNotFoundError:
        logger.warning("Multipliers file not found - running in pure payload mode")
        multipliers = pd.DataFrame()

@app.post("/analyze", response_model=List[dict])
async def run_analysis(request: AnalysisRequest):
    """Run analysis using ONLY payload values"""
    config = request.dict()
    logger.info("Received payload:\n" + "\n".join([f"{k}: {v}" for k,v in config.items()]))
    
    # Validate only if provided
    if config.get("location"):
        if not multipliers.empty and config["location"] not in multipliers['Country'].unique():
            raise HTTPException(400, "Invalid location specified in multipliers data")
    
    if config.get("product"):
        if not multipliers.empty and config["product"] not in multipliers['Sector'].unique():
            raise HTTPException(400, "Invalid product specified in multipliers data")

    # Create data row - all values from payload
    data = {
        "Country": config.get("location", "Custom"),
        "Main_Prod": config.get("product", "Custom"),
        "Plant_Size": config["plant_size"],
        "Plant_Effy": config["plant_effy"],
        "ProcTech": "Custom",
        "Base_Yr": config["baseYear"],
        "Cap": config["Cap"],
        "Yld": config["Yld"],
        "feedEcontnt": config["feedEcontnt"],
        "feedCcontnt": config["feedCcontnt"],
        "Heat_req": config["Heat_req"],
        "Elect_req": config["Elect_req"],
        "Feed_Price": config["Feed_Price"],
        "Fuel_Price": config["Fuel_Price"],
        "Elect_Price": config["Elect_Price"],
        "CO2price": config["CarbonTAX_value"],
        "corpTAX": config["corpTAX_value"],
        "CAPEX": config["CAPEX"],
        "OPEX": config["OPEX"],
        "EcNatGas": config["EcNatGas"],
        "ngCcontnt": config["ngCcontnt"],
        "eEFF": config["eEFF"],
        "hEFF": config["hEFF"]
    }

    # Run analysis
    try:
        results = Analytics_Model2(
            multiplier=multipliers,
            project_data=pd.DataFrame([data]),
            location=config.get("location"),
            product=config.get("product"),
            plant_mode=config["plant_mode"],
            fund_mode=config["fund_mode"],
            opex_mode=config["opex_mode"],
            plant_size=config["plant_size"],
            plant_effy=config["plant_effy"],
            carbon_value=config["carbon_value"]
        )
        return results.to_dict(orient='records')
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Analysis error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
