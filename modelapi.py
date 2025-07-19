from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
import logging
from datetime import datetime
from originalmodel import Analytics_Model2

# Set up logging
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
    title="Advanced Project Economics Model API",
    description="API for chemical plant economics analysis with customizable parameters",
    version="2.0.0"
)

# Default configuration with additional parameters
DEFAULT_CONFIG = {
    "location": "USA",
    "product": "Ethylene",
    "plant_effy": "High",
    "plant_size": "Large",
    "plant_mode": "Green",
    "fund_mode": "Equity",
    "opex_mode": "Inflated",
    "carbon_value": "No",
    "operating_prd": 27,
    "util_operating_first": 0.70,
    "util_operating_second": 0.80,
    "util_operating_third": 0.95,
    "infl": 0.02,
    "RR": 0.035,
    "IRR": 0.10,
    "construction_prd": 3,
    "capex_spread": [0.2, 0.5, 0.3],
    "shrDebt_value": 0.60,
    "baseYear": 2025,
    "ownerCost": 0.10,
    "corpTAX_value": 0.27,
    "Feed_Price": 712.9,
    "Fuel_Price": 712.9,
    "Elect_Price": 16.92,
    "CarbonTAX_value": 0,
    "credit_value": 0.10,
    "CAPEX": 1080000000,
    "OPEX": 33678301.89,
    "PRIcoef": 0.3,
    "CONcoef": 0.7,
    # Additional technical parameters
    "EcNatGas": 53.6,
    "ngCcontnt": 50.3,
    "eEFF": 0.50,
    "hEFF": 0.80,
    "Cap": 250000,
    "Yld": 0.771,
    "feedEcontnt": 48.1,
    "Heat_req": 13.1,
    "Elect_req": 0.3,
    "feedCcontnt": 64
}

class AnalysisRequest(BaseModel):
    location: Optional[str] = None
    product: Optional[str] = None
    plant_effy: Optional[str] = None
    plant_size: Optional[str] = None
    plant_mode: Optional[str] = None
    fund_mode: Optional[str] = None
    opex_mode: Optional[str] = None
    carbon_value: Optional[str] = None
    operating_prd: Optional[int] = None
    util_operating_first: Optional[float] = None
    util_operating_second: Optional[float] = None
    util_operating_third: Optional[float] = None
    infl: Optional[float] = None
    RR: Optional[float] = None
    IRR: Optional[float] = None
    construction_prd: Optional[int] = None
    capex_spread: Optional[List[float]] = None
    shrDebt_value: Optional[float] = None
    baseYear: Optional[int] = None
    ownerCost: Optional[float] = None
    corpTAX_value: Optional[float] = None
    Feed_Price: Optional[float] = None
    Fuel_Price: Optional[float] = None
    Elect_Price: Optional[float] = None
    CarbonTAX_value: Optional[float] = None
    credit_value: Optional[float] = None
    CAPEX: Optional[float] = None
    OPEX: Optional[float] = None
    PRIcoef: Optional[float] = None
    CONcoef: Optional[float] = None
    # Additional technical parameters
    EcNatGas: Optional[float] = None
    ngCcontnt: Optional[float] = None
    eEFF: Optional[float] = None
    hEFF: Optional[float] = None
    Cap: Optional[float] = None
    Yld: Optional[float] = None
    feedEcontnt: Optional[float] = None
    Heat_req: Optional[float] = None
    Elect_req: Optional[float] = None
    feedCcontnt: Optional[float] = None

@app.on_event("startup")
async def startup_event():
    """Load required data files"""
    global project_datas, multipliers
    try:
        project_datas = pd.read_csv("./project_data.csv")
        multipliers = pd.read_csv("./sectorwise_multipliers.csv")
        logger.info("Data files loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"Required data files not found: {str(e)}")
        raise Exception(f"Required data files not found: {str(e)}")

@app.post("/analyze", response_model=List[dict])
async def run_analysis(request: AnalysisRequest):
    """
    Run economic analysis with customizable parameters.
    
    Any parameters not provided will use default values.
    """
    # Log the incoming request
    request_data = request.dict(exclude_unset=True)
    logger.info(f"Incoming request payload: {request_data}")
    
    # Merge request parameters with defaults
    config = DEFAULT_CONFIG.copy()
    provided_params = request.dict(exclude_unset=True)
    config.update(provided_params)
    
    # Log all configuration parameters in categories
    logger.info("\n=== FINAL CONFIGURATION VALUES ===")
    logger.info("\nLocation and Product:")
    logger.info(f"Location: {config['location']}")
    logger.info(f"Product: {config['product']}")
    
    logger.info("\nPlant Characteristics:")
    logger.info(f"Plant Efficiency: {config['plant_effy']}")
    logger.info(f"Plant Size: {config['plant_size']}")
    logger.info(f"Plant Mode: {config['plant_mode']}")
    logger.info(f"Capacity: {config['Cap']}")
    logger.info(f"Yield: {config['Yld']}")
    
    logger.info("\nFinancial Parameters:")
    logger.info(f"Funding Mode: {config['fund_mode']}")
    logger.info(f"OPEX Mode: {config['opex_mode']}")
    logger.info(f"CAPEX: {config['CAPEX']}")
    logger.info(f"OPEX: {config['OPEX']}")
    logger.info(f"Debt Share: {config['shrDebt_value']}")
    
    logger.info("\nTechnical Parameters:")
    logger.info(f"EcNatGas: {config['EcNatGas']}")
    logger.info(f"Natural Gas Carbon Content: {config['ngCcontnt']}")
    logger.info(f"Electrical Efficiency: {config['eEFF']}")
    logger.info(f"Heat Efficiency: {config['hEFF']}")
    logger.info(f"Feed Energy Content: {config['feedEcontnt']}")
    logger.info(f"Feed Carbon Content: {config['feedCcontnt']}")
    logger.info(f"Heat Requirement: {config['Heat_req']}")
    logger.info(f"Electricity Requirement: {config['Elect_req']}")
    
    logger.info("\nEconomic Parameters:")
    logger.info(f"Inflation Rate: {config['infl']}")
    logger.info(f"Risk Rate: {config['RR']}")
    logger.info(f"IRR Target: {config['IRR']}")
    
    # Validate parameters
    validate_parameters(config)
    
    # Create a data row with the custom parameters
    custom_data = create_custom_data_row(config)
    
    # Run analysis
    try:
        logger.info("Starting analysis...")
        results = Analytics_Model2(
            multiplier=multipliers,
            project_data=custom_data,
            location=config["location"],
            product=config["product"],
            plant_mode=config["plant_mode"],
            fund_mode=config["fund_mode"],
            opex_mode=config["opex_mode"],
            plant_size=config["plant_size"],
            plant_effy=config["plant_effy"],
            carbon_value=config["carbon_value"]
        )
        
        logger.info("Analysis completed successfully")
        return results.to_dict(orient='records')
    
    except Exception as e:
        logger.error(f"Error running analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running analysis: {str(e)}")

def validate_parameters(config: dict):
    """Validate all configuration parameters"""
    # Existing validation checks...
    # Add validation for technical parameters if needed
    if config["eEFF"] <= 0 or config["eEFF"] > 1:
        logger.error(f"Invalid electrical efficiency: {config['eEFF']}")
        raise HTTPException(status_code=400, detail="Electrical efficiency must be between 0 and 1")
    
    if config["hEFF"] <= 0 or config["hEFF"] > 1:
        logger.error(f"Invalid heat efficiency: {config['hEFF']}")
        raise HTTPException(status_code=400, detail="Heat efficiency must be between 0 and 1")

def create_custom_data_row(config: dict) -> pd.DataFrame:
    """Create a custom data row from the configuration"""
    data = {
        "Country": config["location"],
        "Main_Prod": config["product"],
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
    
    logger.info("\nCustom Data Row Created:")
    for key, value in data.items():
        logger.info(f"{key}: {value}")
    
    return pd.DataFrame([data])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
