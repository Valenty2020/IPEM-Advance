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

# Default configuration
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
    "CONcoef": 0.7
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

@app.get("/")
async def root():
    return {
        "message": "Advanced Project Economics Model API",
        "endpoints": {
            "/analyze": "POST - Run economic analysis with customizable parameters",
            "/defaults": "GET - View default parameter values",
            "/locations": "GET - List available countries",
            "/products": "GET - List available products"
        }
    }

@app.get("/defaults")
async def get_defaults():
    """Get default parameter values"""
    logger.info("Default configuration requested")
    return DEFAULT_CONFIG

@app.get("/locations")
async def get_locations():
    """Get list of available countries/locations"""
    locations = project_datas['Country'].unique().tolist()
    logger.info(f"Available locations requested. Found {len(locations)} locations.")
    return {"locations": locations}

@app.get("/products")
async def get_products():
    """Get list of available products"""
    products = project_datas['Main_Prod'].unique().tolist()
    logger.info(f"Available products requested. Found {len(products)} products.")
    return {"products": products}

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
    
    # Log the final configuration after merging with defaults
    logger.info("Final configuration values:")
    for key, value in config.items():
        logger.info(f"{key}: {value}")
    
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
    if config["location"] not in project_datas['Country'].unique():
        logger.error(f"Invalid location: {config['location']}")
        raise HTTPException(status_code=400, detail="Invalid location")
    
    if config["product"] not in project_datas['Main_Prod'].unique():
        logger.error(f"Invalid product: {config['product']}")
        raise HTTPException(status_code=400, detail="Invalid product")
    
    if config["plant_mode"] not in ["Green", "Brown"]:
        logger.error(f"Invalid plant_mode: {config['plant_mode']}")
        raise HTTPException(status_code=400, detail="plant_mode must be 'Green' or 'Brown'")
    
    if config["fund_mode"] not in ["Debt", "Equity", "Mixed"]:
        logger.error(f"Invalid fund_mode: {config['fund_mode']}")
        raise HTTPException(status_code=400, detail="fund_mode must be 'Debt', 'Equity', or 'Mixed'")
    
    if config["opex_mode"] not in ["Inflated", "Uninflated"]:
        logger.error(f"Invalid opex_mode: {config['opex_mode']}")
        raise HTTPException(status_code=400, detail="opex_mode must be 'Inflated' or 'Uninflated'")
    
    if config["carbon_value"] not in ["Yes", "No"]:
        logger.error(f"Invalid carbon_value: {config['carbon_value']}")
        raise HTTPException(status_code=400, detail="carbon_value must be 'Yes' or 'No'")
    
    if config["plant_size"] not in ["Large", "Small", None]:
        logger.error(f"Invalid plant_size: {config['plant_size']}")
        raise HTTPException(status_code=400, detail="plant_size must be 'Large' or 'Small'")
    
    if config["plant_effy"] not in ["High", "Low", None]:
        logger.error(f"Invalid plant_effy: {config['plant_effy']}")
        raise HTTPException(status_code=400, detail="plant_effy must be 'High' or 'Low'")
    
    if sum(config["capex_spread"]) != 1.0:
        logger.error(f"Invalid capex_spread: {config['capex_spread']} (sum is {sum(config['capex_spread'])})")
        raise HTTPException(status_code=400, detail="capex_spread values must sum to 1.0")

def create_custom_data_row(config: dict) -> pd.DataFrame:
    """Create a custom data row from the configuration"""
    data = {
        "Country": config["location"],
        "Main_Prod": config["product"],
        "Plant_Size": config["plant_size"],
        "Plant_Effy": config["plant_effy"],
        "ProcTech": "Custom",  # Mark as custom configuration
        "Base_Yr": config["baseYear"],
        "Cap": 1,  # Capacity - will be scaled by CAPEX
        "Yld": 1,  # Yield - adjust based on efficiency
        "feedEcontnt": 0,  # Will be calculated
        "feedCcontnt": 0,  # Will be calculated
        "Heat_req": 0,  # Will be calculated
        "Elect_req": 0,  # Will be calculated
        "Feed_Price": config["Feed_Price"],
        "Fuel_Price": config["Fuel_Price"],
        "Elect_Price": config["Elect_Price"],
        "CO2price": config["CarbonTAX_value"],
        "corpTAX": config["corpTAX_value"],
        "CAPEX": config["CAPEX"],
        "OPEX": config["OPEX"],
        # Additional calculated fields would go here
    }
    
    # Adjust yield based on efficiency
    if config["plant_effy"] == "High":
        data["Yld"] = 0.9  # 90% yield for high efficiency
    else:
        data["Yld"] = 0.7  # 70% yield for low efficiency
    
    logger.info(f"Created custom data row with CAPEX: {data['CAPEX']}, OPEX: {data['OPEX']}")
    return pd.DataFrame([data])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
