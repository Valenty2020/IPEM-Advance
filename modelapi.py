from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
from originalmodel import Analytics_Model2

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
    # Add custom data fields that might override CSV data
    feedEcontnt: Optional[float] = None
    feedCcontnt: Optional[float] = None
    Heat_req: Optional[float] = None
    Elect_req: Optional[float] = None
    Yld: Optional[float] = None
    Cap: Optional[float] = None

@app.on_event("startup")
async def startup_event():
    """Load required data files as fallbacks"""
    global project_datas, multipliers
    try:
        project_datas = pd.read_csv("./project_data.csv")
        multipliers = pd.read_csv("./sectorwise_multipliers.csv")
    except FileNotFoundError as e:
        print(f"Warning: Could not load data files - using empty DataFrames as fallback: {str(e)}")
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
        return {"locations": []}

@app.get("/products")
async def get_products():
    """Get list of available products"""
    try:
        products = project_datas['Main_Prod'].unique().tolist()
        return {"products": products}
    except:
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
    
    # Validate parameters
    validate_parameters(config)
    
    # Create a data row with the custom parameters
    custom_data = create_custom_data_row(config, provided_params)
    
    # Run analysis
    try:
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
        
        return results.to_dict(orient='records')
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running analysis: {str(e)}")

def validate_parameters(config: dict):
    """Validate all configuration parameters"""
    # Only validate location/product if we're not providing all custom data
    if not all(k in config for k in ['feedEcontnt', 'feedCcontnt', 'Heat_req', 'Elect_req']):
        try:
            if "location" in config and config["location"] not in project_datas['Country'].unique():
                raise HTTPException(status_code=400, detail="Invalid location")
            
            if "product" in config and config["product"] not in project_datas['Main_Prod'].unique():
                raise HTTPException(status_code=400, detail="Invalid product")
        except:
            # If CSV data isn't loaded, we'll rely on custom data
            if not all(k in config for k in ['feedEcontnt', 'feedCcontnt', 'Heat_req', 'Elect_req']):
                raise HTTPException(status_code=400, detail="Either provide complete custom data or ensure location/product exist in project data")
    
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
        else:
            base_data = {}
    except:
        base_data = {}
    
    # Base data structure with all possible fields
    data = {
        "Country": config.get("location", "USA"),
        "Main_Prod": config.get("product", "Ethylene"),
        "Plant_Size": config.get("plant_size", "Large"),
        "Plant_Effy": config.get("plant_effy", "High"),
        "ProcTech": "Custom",
        "Base_Yr": config.get("baseYear", 2025),
        "Cap": config.get("Cap", 1),  # Capacity
        "Yld": config.get("Yld", 0.9 if config.get("plant_effy", "High") == "High" else 0.7),
        "feedEcontnt": config.get("feedEcontnt", base_data.get("feedEcontnt", 0)),
        "feedCcontnt": config.get("feedCcontnt", base_data.get("feedCcontnt", 0)),
        "Heat_req": config.get("Heat_req", base_data.get("Heat_req", 0)),
        "Elect_req": config.get("Elect_req", base_data.get("Elect_req", 0)),
        "Feed_Price": config.get("Feed_Price", 712.9),
        "Fuel_Price": config.get("Fuel_Price", 712.9),
        "Elect_Price": config.get("Elect_Price", 16.92),
        "CO2price": config.get("CarbonTAX_value", 0),
        "corpTAX": config.get("corpTAX_value", 0.27),
        "CAPEX": config.get("CAPEX", 1080000000),
        "OPEX": config.get("OPEX", 33678301.89),
    }
    
    # Update with any additional provided parameters that match our data fields
    for field in ['feedEcontnt', 'feedCcontnt', 'Heat_req', 'Elect_req', 'Yld', 'Cap']:
        if field in provided_params:
            data[field] = provided_params[field]
    
    return pd.DataFrame([data])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
