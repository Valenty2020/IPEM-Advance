from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
import logging
from originalmodel import Analytics_Model2

# Configure logging
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
    title="Standalone Economics Model API",
    description="API that requires no external data references",
    version="4.0.0"
)

class AnalysisRequest(BaseModel):
    # Plant configuration (required)
    plant_effy: str
    plant_size: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
    
    # Economic parameters (required)
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
    
    # Prices (required)
    Feed_Price: float
    Fuel_Price: float
    Elect_Price: float
    CarbonTAX_value: float
    credit_value: float
    
    # Capital/Operating (required)
    CAPEX: float
    OPEX: float
    PRIcoef: float
    CONcoef: float
    
    # Technical parameters (required)
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

@app.post("/analyze", response_model=List[dict])
async def run_analysis(request: AnalysisRequest):
    """Run analysis using ONLY payload values"""
    config = request.dict()
    logger.info("Starting analysis with payload-only configuration")
    
    # Create complete data row
    data = {
        "Country": "Custom",
        "Main_Prod": "Custom",
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

    try:
        # Modified Analytics_Model2 that doesn't need multipliers
        results = standalone_analysis(
            project_data=pd.DataFrame([data]),
            plant_mode=config["plant_mode"],
            fund_mode=config["fund_mode"],
            opex_mode=config["opex_mode"],
            carbon_value=config["carbon_value"]
        )
        return results.to_dict(orient='records')
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Analysis error: {str(e)}")

def standalone_analysis(project_data: pd.DataFrame, **kwargs):
    """
    Simplified analysis function that works without any external data
    """
    # Your core calculations here using only project_data
    # Example:
    results = project_data.copy()
    
    # Add calculated fields
    results['Total_Cost'] = results['CAPEX'] + results['OPEX']
    results['ROI'] = results['CAPEX'] / results['OPEX']
    
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
