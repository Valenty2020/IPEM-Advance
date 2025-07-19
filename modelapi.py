from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
import logging
from datetime import datetime

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
    title="Project Economics Model API",
    description="API for chemical plant economics analysis - Full Custom Mode",
    version="3.0.0"
)

class AnalysisRequest(BaseModel):
    # Core parameters (all optional)
    location: Optional[str] = None
    product: Optional[str] = None
    
    # Plant configuration
    plant_effy: str
    plant_size: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
    
    # Technical parameters
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
    ProcTech: Optional[str] = "Custom"

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
    Run economic analysis using ONLY the provided payload values.
    Both location and product are optional - pure custom mode.
    """
    config = request.dict()
    logger.info("\n=== FULL PAYLOAD VALUES ===")
    for key, value in config.items():
        logger.info(f"{key}: {value}")
    
    # Validate parameters
    validate_parameters(config)
    
    # Create data row from payload
    custom_data = create_custom_data_row(config)
    
    # Run analysis
    try:
        logger.info("Starting custom analysis...")
        results = Analytics_Model2(
            multiplier=multipliers,
            project_data=custom_data,
            location=config.get("location"),  # Can be None
            product=config.get("product"),    # Can be None
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
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def validate_parameters(config: dict):
    """Validate all parameters"""
    if config.get("location") and config["location"] not in project_datas['Country'].unique():
        raise HTTPException(400, "Invalid location specified")
    
    if config.get("product") and config["product"] not in project_datas['Main_Prod'].unique():
        raise HTTPException(400, "Invalid product specified")
    
    # Validate plant modes
    if config["plant_mode"] not in ["Green", "Brown"]:
        raise HTTPException(400, "plant_mode must be 'Green' or 'Brown'")
    
    if config["fund_mode"] not in ["Debt", "Equity", "Mixed"]:
        raise HTTPException(400, "fund_mode must be 'Debt', 'Equity', or 'Mixed'")
    
    # Validate technical parameters
    if config["eEFF"] <= 0 or config["eEFF"] > 1:
        raise HTTPException(400, "Electrical efficiency must be between 0 and 1")
    
    if abs(sum(config["capex_spread"]) - 1.0) > 0.001:  # Allow for floating point precision
        raise HTTPException(400, "capex_spread values must sum to 1.0")

def create_custom_data_row(config: dict) -> pd.DataFrame:
    """Create complete data row from payload"""
    data = {
        "Country": config.get("location", "Custom"),
        "Main_Prod": config.get("product", "Custom"),
        "Plant_Size": config["plant_size"],
        "Plant_Effy": config["plant_effy"],
        "ProcTech": config.get("ProcTech", "Custom"),
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
        "hEFF": config["hEFF"],
        # Additional calculated fields
        "operating_prd": config["operating_prd"],
        "util_operating_first": config["util_operating_first"],
        "util_operating_second": config["util_operating_second"],
        "util_operating_third": config["util_operating_third"]
    }
    
    logger.info("\nCustom Data Row Created:")
    for key, value in data.items():
        logger.info(f"{key}: {value}")
    
    return pd.DataFrame([data])
