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
    title="Direct Payload Economics API",
    description="API that bypasses all external data dependencies",
    version="4.1.0"
)

class AnalysisRequest(BaseModel):
    # All parameters now required (no optional fields)
    plant_effy: str
    plant_size: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
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
    Feed_Price: float
    Fuel_Price: float
    Elect_Price: float
    CarbonTAX_value: float
    credit_value: float
    CAPEX: float
    OPEX: float
    PRIcoef: float
    CONcoef: float
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
    """Run analysis using ONLY the provided payload values"""
    config = request.dict()
    logger.info("Starting direct payload analysis")
    
    # Create the complete analysis input
    analysis_data = {
        "CAPEX": config["CAPEX"],
        "OPEX": config["OPEX"],
        "Yld": config["Yld"],
        "Cap": config["Cap"],
        "Feed_Price": config["Feed_Price"],
        "Fuel_Price": config["Fuel_Price"],
        "Elect_Price": config["Elect_Price"],
        "Heat_req": config["Heat_req"],
        "Elect_req": config["Elect_req"],
        "corpTAX": config["corpTAX_value"],
        "CO2price": config["CarbonTAX_value"],
        "operating_prd": config["operating_prd"],
        "utilization": [
            config["util_operating_first"],
            config["util_operating_second"],
            config["util_operating_third"]
        ],
        "infl": config["infl"],
        "RR": config["RR"],
        "IRR": config["IRR"],
        "construction_prd": config["construction_prd"],
        "capex_spread": config["capex_spread"],
        "shrDebt": config["shrDebt_value"],
        "credit": config["credit_value"],
        "plant_mode": config["plant_mode"],
        "fund_mode": config["fund_mode"],
        "opex_mode": config["opex_mode"],
        "carbon_value": config["carbon_value"]
    }

    try:
        # Direct calculations without DataFrame concatenation
        results = calculate_economics(analysis_data)
        return [results]  # Return as list to match response_model
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Analysis error: {str(e)}")

def calculate_economics(data: dict) -> dict:
    """Core calculation logic without DataFrame dependencies"""
    # Example calculations - replace with your actual formulas
    annual_production = data["Cap"] * data["Yld"] * 365  # Tons/year
    annual_opex = data["OPEX"] * (1 + data["infl"])**data["operating_prd"]
    
    return {
        "annual_production": annual_production,
        "annual_opex": annual_opex,
        "capex_breakdown": {
            "year1": data["CAPEX"] * data["capex_spread"][0],
            "year2": data["CAPEX"] * data["capex_spread"][1],
            "year3": data["CAPEX"] * data["capex_spread"][2]
        },
        "npv": calculate_npv(data),  # Implement your NPV calculation
        "irr": data["IRR"],
        "plant_config": {
            "mode": data["plant_mode"],
            "funding": data["fund_mode"],
            "carbon_policy": data["carbon_value"]
        }
    }

def calculate_npv(data: dict) -> float:
    """Example NPV calculation - replace with your actual formula"""
    # Dummy implementation
    return data["CAPEX"] * 0.8  # Replace with real NPV calculation

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
