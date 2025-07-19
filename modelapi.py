from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
import logging
from originalmodel import Analytics_Model2

app = FastAPI(
    title="Advanced Project Economics Model API",
    description="API for chemical plant economics analysis with customizable parameters",
    version="2.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Updated default configuration with specific values
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
    "Feed_Price": 88.5,
    "Fuel_Price": 88.5,
    "Elect_Price": 16.92,
    "CarbonTAX_value": 56.34,
    "credit_value": 0.10,
    "CAPEX": 1020000000,
    "OPEX": 19600000,
    "PRIcoef": 0.3,
    "CONcoef": 0.7,
    # Additional technical defaults
    "Cap": 1600000,
    "Yld": 0.875,
    "feedEcontnt": 53.6,
    "feedCcontnt": 50,
    "Heat_req": 11.6,
    "Elect_req": 0.3
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
    # Technical parameters
    Cap: Optional[float] = None
    Yld: Optional[float] = None
    feedEcontnt: Optional[float] = None
    feedCcontnt: Optional[float] = None
    Heat_req: Optional[float] = None
    Elect_req: Optional[float] = None

@app.on_event("startup")
async def startup_event():
    """Load required data files as fallbacks"""
    global project_datas, multipliers
    try:
        project_datas = pd.read_csv("./project_data.csv")
        multipliers = pd.read_csv("./sectorwise_multipliers.csv")
        logger.info("Successfully loaded project data and multipliers CSV files")
    except FileNotFoundError as e:
        logger.warning(f"Could not load data files - using empty DataFrames as fallback: {str(e)}")
        project_datas = pd.DataFrame()
        multipliers = pd.DataFrame()

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
    return DEFAULT_CONFIG

@app.get("/locations")
async def get_locations():
    """Get list of available countries/locations"""
    try:
        locations = project_datas['Country'].unique().tolist()
        return {"locations": locations}
    except:
        logger.warning("Could not retrieve locations from project data - using empty list")
        return {"locations": []}

@app.get("/products")
async def get_products():
    """Get list of available products"""
    try:
        products = project_datas['Main_Prod'].unique().tolist()
        return {"products": products}
    except:
        logger.warning("Could not retrieve products from project data - using empty list")
        return {"products": []}

@app.post("/analyze", response_model=List[dict])
async def run_analysis(request: AnalysisRequest):
    """
    Run economic analysis with customizable parameters.
    
    Any parameters not provided will use default values. Custom data in the payload
    will override any values from the CSV files.
    """
    # Merge request parameters with defaults
    config = DEFAULT_CONFIG.copy()
    provided_params = request.dict(exclude_unset=True)
    config.update(provided_params)
    
    # Log missing parameters
    log_missing_parameters(provided_params, config)
    
    # Validate parameters
    validate_parameters(config)
    
    # Create a data row with the custom parameters
    custom_data = create_custom_data_row(config, provided_params)
    
    # Run analysis
    try:
        logger.info("Starting economic analysis with configuration: %s", {k: v for k, v in config.items() if k not in ['capex_spread']})
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
        
        logger.info("Successfully completed economic analysis")
        return results.to_dict(orient='records')
    
    except Exception as e:
        logger.error(f"Error running analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running analysis: {str(e)}")

def log_missing_parameters(provided_params: dict, config: dict):
    """Log which parameters are missing and what fallback was used"""
    required_fields = [
        'Cap', 'Yld', 'Base_Yr', 'CAPEX', 'OPEX', 'Feed_Price', 
        'Heat_req', 'Elect_req', 'Fuel_Price', 'Elect_Price', 
        'feedEcontnt', 'feedCcontnt', 'corpTAX', 'CO2price'
    ]
    
    for field in required_fields:
        if field not in provided_params:
            source = "DEFAULT_CONFIG"
            if field in ['feedEcontnt', 'feedCcontnt', 'Heat_req', 'Elect_req']:
                try:
                    if config["location"] in project_datas['Country'].unique() and config["product"] in project_datas['Main_Prod'].unique():
                        source = "project_data.csv"
                except:
                    pass
            
            logger.info(f"Parameter '{field}' not provided - using value from {source}: {config[field]}")

def validate_parameters(config: dict):
    """Validate all configuration parameters"""
    # Only validate location/product if we're not providing all custom data
    required_tech_params = ['feedEcontnt', 'feedCcontnt', 'Heat_req', 'Elect_req']
    if not all(k in config for k in required_tech_params):
        try:
            if "location" in config and config["location"] not in project_datas['Country'].unique():
                raise HTTPException(status_code=400, detail="Invalid location")
            
            if "product" in config and config["product"] not in project_datas['Main_Prod'].unique():
                raise HTTPException(status_code=400, detail="Invalid product")
        except:
            # If CSV data isn't loaded, we'll rely on custom data
            if not all(k in config for k in required_tech_params):
                missing = [k for k in required_tech_params if k not in config]
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required technical parameters: {', '.join(missing)}. Either provide these or ensure location/product exist in project data"
                )
    
    if "plant_mode" in config and config["plant_mode"] not in ["Green", "Brown"]:
        raise HTTPException(status_code=400, detail="plant_mode must be 'Green' or 'Brown'")
    
    if "fund_mode" in config and config["fund_mode"] not in ["Debt", "Equity", "Mixed"]:
        raise HTTPException(status_code=400, detail="fund_mode must be 'Debt', 'Equity', or 'Mixed'")
    
    if "opex_mode" in config and config["opex_mode"] not in ["Inflated", "Uninflated"]:
        raise HTTPException(status_code=400, detail="opex_mode must be 'Inflated' or 'Uninflated'")
    
    if "carbon_value" in config and config["carbon_value"] not in ["Yes", "No"]:
        raise HTTPException(status_code=400, detail="carbon_value must be 'Yes' or 'No'")
    
    if "plant_size" in config and config["plant_size"] not in ["Large", "Small", None]:
        raise HTTPException(status_code=400, detail="plant_size must be 'Large' or 'Small'")
    
    if "plant_effy" in config and config["plant_effy"] not in ["High", "Low", None]:
        raise HTTPException(status_code=400, detail="plant_effy must be 'High' or 'Low'")
    
    if "capex_spread" in config and sum(config["capex_spread"]) != 1.0:
        raise HTTPException(status_code=400, detail="capex_spread values must sum to 1.0")

def create_custom_data_row(config: dict, provided_params: dict) -> pd.DataFrame:
    """Create a custom data row from the configuration, using provided params first"""
    # Start with default values from CSV if available
    try:
        if "location" in config and "product" in config:
            base_data = project_datas[
                (project_datas['Country'] == config["location"]) & 
                (project_datas['Main_Prod'] == config["product"])
            ].iloc[0].to_dict()
            logger.info(f"Found matching project data for {config['location']}/{config['product']}")
        else:
            base_data = {}
    except Exception as e:
        logger.warning(f"Could not find matching project data: {str(e)}")
        base_data = {}
    
    # Base data structure with all possible fields
    data = {
        "Country": config.get("location", DEFAULT_CONFIG["location"]),
        "Main_Prod": config.get("product", DEFAULT_CONFIG["product"]),
        "Plant_Size": config.get("plant_size", DEFAULT_CONFIG["plant_size"]),
        "Plant_Effy": config.get("plant_effy", DEFAULT_CONFIG["plant_effy"]),
        "ProcTech": "Custom",
        "Base_Yr": config.get("baseYear", DEFAULT_CONFIG["baseYear"]),
        "Cap": config.get("Cap", DEFAULT_CONFIG["Cap"]),
        "Yld": config.get("Yld", DEFAULT_CONFIG["Yld"]),
        "feedEcontnt": config.get("feedEcontnt", base_data.get("feedEcontnt", DEFAULT_CONFIG["feedEcontnt"])),
        "feedCcontnt": config.get("feedCcontnt", base_data.get("feedCcontnt", DEFAULT_CONFIG["feedCcontnt"])),
        "Heat_req": config.get("Heat_req", base_data.get("Heat_req", DEFAULT_CONFIG["Heat_req"])),
        "Elect_req": config.get("Elect_req", base_data.get("Elect_req", DEFAULT_CONFIG["Elect_req"])),
        "Feed_Price": config.get("Feed_Price", DEFAULT_CONFIG["Feed_Price"]),
        "Fuel_Price": config.get("Fuel_Price", DEFAULT_CONFIG["Fuel_Price"]),
        "Elect_Price": config.get("Elect_Price", DEFAULT_CONFIG["Elect_Price"]),
        "CO2price": config.get("CarbonTAX_value", DEFAULT_CONFIG["CarbonTAX_value"]),
        "corpTAX": config.get("corpTAX_value", DEFAULT_CONFIG["corpTAX_value"]),
        "CAPEX": config.get("CAPEX", DEFAULT_CONFIG["CAPEX"]),
        "OPEX": config.get("OPEX", DEFAULT_CONFIG["OPEX"]),
    }
    
    # Log the source of each parameter
    for field in data:
        if field in provided_params:
            source = "provided in request"
        elif field in base_data:
            source = "project_data.csv"
        else:
            source = "DEFAULT_CONFIG"
        logger.debug(f"Parameter '{field}' sourced from {source}")
    
    return pd.DataFrame([data])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
