from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Advanced Project Economics Model API",
    description="API for chemical plant economics analysis with customizable parameters",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    "Feed_Price": 88.5,
    "Fuel_Price": 88.5,
    "Elect_Price": 16.92,
    "CarbonTAX_value": 56.34,
    "credit_value": 0.10,
    "CAPEX": 1020000000,
    "OPEX": 19600000,
    "PRIcoef": 0.3,
    "CONcoef": 0.7,
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
    Cap: Optional[float] = None
    Yld: Optional[float] = None
    feedEcontnt: Optional[float] = None
    feedCcontnt: Optional[float] = None
    Heat_req: Optional[float] = None
    Elect_req: Optional[float] = None

# Mock Analytics Model if import fails
try:
    from originalmodel import Analytics_Model2
    logger.info("Successfully imported Analytics_Model2")
except ImportError as e:
    logger.warning(f"Could not import originalmodel: {str(e)} - Using mock implementation")
    def Analytics_Model2(*args, **kwargs):
        mock_data = {
            "Metric": ["NPV", "IRR", "Payback"],
            "Value": [1000000, 0.15, 5.2]
        }
        return pd.DataFrame(mock_data)

@app.on_event("startup")
async def startup_event():
    """Load required data files as fallbacks"""
    global project_datas, multipliers
    try:
        project_datas = pd.read_csv("project_data.csv")
        logger.info("Successfully loaded project_data.csv")
    except Exception as e:
        logger.warning(f"Could not load project_data.csv: {str(e)}")
        project_datas = pd.DataFrame({
            "Country": ["USA", "Germany", "China"],
            "Main_Prod": ["Ethylene", "Propylene", "Methanol"]
        })

    try:
        multipliers = pd.read_csv("sectorwise_multipliers.csv")
        logger.info("Successfully loaded sectorwise_multipliers.csv")
    except Exception as e:
        logger.warning(f"Could not load sectorwise_multipliers.csv: {str(e)}")
        multipliers = pd.DataFrame({
            "Sector": ["Chemicals", "Energy"],
            "Multiplier": [1.2, 1.5]
        })

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Advanced Project Economics Model API",
        "endpoints": {
            "/test": {"method": "GET", "description": "Test endpoint"},
            "/analyze": {"method": "POST", "description": "Run economic analysis"},
            "/defaults": {"method": "GET", "description": "View default parameters"},
            "/locations": {"method": "GET", "description": "List available countries"},
            "/products": {"method": "GET", "description": "List available products"}
        },
        "status": "active"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "API is functioning correctly",
        "data": {"sample_value": 42}
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
    except Exception as e:
        logger.error(f"Error getting locations: {str(e)}")
        return {"locations": [], "error": str(e)}

@app.get("/products")
async def get_products():
    """Get list of available products"""
    try:
        products = project_datas['Main_Prod'].unique().tolist()
        return {"products": products}
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        return {"products": [], "error": str(e)}

@app.post("/analyze")
async def run_analysis(request: AnalysisRequest):
    """
    Run economic analysis with customizable parameters.
    
    Any parameters not provided will use default values.
    """
    # Merge request parameters with defaults
    config = DEFAULT_CONFIG.copy()
    provided_params = request.dict(exclude_unset=True)
    config.update(provided_params)
    
    # Log missing parameters
    log_missing_parameters(provided_params, config)
    
    # Validate parameters
    try:
        validate_parameters(config)
    except HTTPException as e:
        logger.error(f"Parameter validation failed: {e.detail}")
        raise
    
    # Create a data row with the custom parameters
    try:
        custom_data = create_custom_data_row(config, provided_params)
        logger.info("Successfully created custom data row")
    except Exception as e:
        logger.error(f"Error creating custom data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating input data: {str(e)}")
    
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
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

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
                    if config["location"] in project_datas['Country'].unique() and \
                       config["product"] in project_datas['Main_Prod'].unique():
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
                raise HTTPException(status_code=400, detail=f"Invalid location: {config['location']}")
            
            if "product" in config and config["product"] not in project_datas['Main_Prod'].unique():
                raise HTTPException(status_code=400, detail=f"Invalid product: {config['product']}")
        except Exception as e:
            if not all(k in config for k in required_tech_params):
                missing = [k for k in required_tech_params if k not in config]
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required parameters: {', '.join(missing)}. Either provide these or ensure location/product exist in project data"
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
    
    if "capex_spread" in config and abs(sum(config["capex_spread"]) - 1.0) > 0.001:  # Allow for floating point precision
        raise HTTPException(status_code=400, detail="capex_spread values must sum to 1.0")

def create_custom_data_row(config: dict, provided_params: dict) -> pd.DataFrame:
    """Create a custom data row from the configuration"""
    # Start with default values from CSV if available
    try:
        if "location" in config and "product" in config:
            base_data = project_datas[
                (project_datas['Country'] == config["location"]) & 
                (project_datas['Main_Prod'] == config["product"])
            ].iloc[0].to_dict()
            logger.debug(f"Found base data for {config['location']}/{config['product']}")
        else:
            base_data = {}
    except Exception as e:
        logger.warning(f"Could not find base data: {str(e)}")
        base_data = {}
    
    # Create the data structure
    data = {
        "Country": str(config.get("location", DEFAULT_CONFIG["location"])),
        "Main_Prod": str(config.get("product", DEFAULT_CONFIG["product"])),
        "Plant_Size": str(config.get("plant_size", DEFAULT_CONFIG["plant_size"])),
        "Plant_Effy": str(config.get("plant_effy", DEFAULT_CONFIG["plant_effy"])),
        "ProcTech": "Custom",
        "Base_Yr": int(config.get("baseYear", DEFAULT_CONFIG["baseYear"])),
        "Cap": float(config.get("Cap", DEFAULT_CONFIG["Cap"])),
        "Yld": float(config.get("Yld", DEFAULT_CONFIG["Yld"])),
        "feedEcontnt": float(config.get("feedEcontnt", base_data.get("feedEcontnt", DEFAULT_CONFIG["feedEcontnt"]))),
        "feedCcontnt": float(config.get("feedCcontnt", base_data.get("feedCcontnt", DEFAULT_CONFIG["feedCcontnt"]))),
        "Heat_req": float(config.get("Heat_req", base_data.get("Heat_req", DEFAULT_CONFIG["Heat_req"]))),
        "Elect_req": float(config.get("Elect_req", base_data.get("Elect_req", DEFAULT_CONFIG["Elect_req"]))),
        "Feed_Price": float(config.get("Feed_Price", DEFAULT_CONFIG["Feed_Price"])),
        "Fuel_Price": float(config.get("Fuel_Price", DEFAULT_CONFIG["Fuel_Price"])),
        "Elect_Price": float(config.get("Elect_Price", DEFAULT_CONFIG["Elect_Price"])),
        "CO2price": float(config.get("CarbonTAX_value", DEFAULT_CONFIG["CarbonTAX_value"])),
        "corpTAX": float(config.get("corpTAX_value", DEFAULT_CONFIG["corpTAX_value"])),
        "CAPEX": float(config.get("CAPEX", DEFAULT_CONFIG["CAPEX"])),
        "OPEX": float(config.get("OPEX", DEFAULT_CONFIG["OPEX"])),
    }
    
    return pd.DataFrame([data])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
