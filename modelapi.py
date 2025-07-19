from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import numpy as np
import uvicorn
import logging
from originalmodel import Analytics_Model2

# Set up logging at module level
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_logs.log'),
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="Project Economics Model API",
    description="API for chemical plant economics analysis - Strict Payload Only",
    version="2.0.0"
)

class AnalysisRequest(BaseModel):
    # Required parameters with no defaults
    location: str
    plant_effy: str
    plant_size: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
    
    # Optional parameters
    product: Optional[str] = None
    
    # Optional technical parameters
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
    except Exception as e:
        logger.error(f"Error loading data files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading data files: {str(e)}")

@app.post("/analyze", response_model=List[dict])
async def run_analysis(request: AnalysisRequest):
    """
    Run economic analysis using ONLY the provided payload values.
    Product parameter is optional - all other parameters are required.
    """
    try:
        # Convert request to dict and log everything
        config = request.dict()
        logger.info("\n=== PAYLOAD VALUES RECEIVED ===")
        for key, value in config.items():
            logger.info(f"{key}: {value}")
        
        # Validate parameters
        validate_parameters(config)
        
        # Create data row from payload only
        custom_data = create_custom_data_row(config)
        
        logger.info("Starting analysis with payload values only...")
        results = Analytics_Model2(
            multiplier=multipliers,
            project_data=custom_data,
            location=config["location"],
            product=config.get("product", ""),  # Use empty string if product not provided
            plant_mode=config["plant_mode"],
            fund_mode=config["fund_mode"],
            opex_mode=config["opex_mode"],
            plant_size=config["plant_size"],
            plant_effy=config["plant_effy"],
            carbon_value=config["carbon_value"]
        )
        
        logger.info("Analysis completed successfully")
        return results.to_dict(orient='records')
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error running analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running analysis: {str(e)}")

def validate_parameters(config: dict):
    """Validate all payload parameters"""
    try:
        if config["location"] not in project_datas['Country'].unique():
            logger.error(f"Invalid location: {config['location']}")
            raise HTTPException(status_code=400, detail="Invalid location")
        
        # Only validate product if it's provided
        if config.get("product") and config["product"] not in project_datas['Main_Prod'].unique():
            logger.error(f"Invalid product: {config['product']}")
            raise HTTPException(status_code=400, detail="Invalid product")
        
        if config["plant_mode"] not in ["Green", "Brown"]:
            raise HTTPException(status_code=400, detail="plant_mode must be 'Green' or 'Brown'")
        
        if config["fund_mode"] not in ["Debt", "Equity", "Mixed"]:
            raise HTTPException(status_code=400, detail="fund_mode must be 'Debt', 'Equity', or 'Mixed'")
        
        if config["opex_mode"] not in ["Inflated", "Uninflated"]:
            raise HTTPException(status_code=400, detail="opex_mode must be 'Inflated' or 'Uninflated'")
        
        if config["carbon_value"] not in ["Yes", "No"]:
            raise HTTPException(status_code=400, detail="carbon_value must be 'Yes' or 'No'")
        
        if config["plant_size"] not in ["Large", "Small"]:
            raise HTTPException(status_code=400, detail="plant_size must be 'Large' or 'Small'")
        
        if config["plant_effy"] not in ["High", "Low"]:
            raise HTTPException(status_code=400, detail="plant_effy must be 'High' or 'Low'")
        
        if config.get("capex_spread") and sum(config["capex_spread"]) != 1.0:
            raise HTTPException(status_code=400, detail="capex_spread values must sum to 1.0")
        
        if config.get("eEFF") and (config["eEFF"] <= 0 or config["eEFF"] > 1):
            raise HTTPException(status_code=400, detail="Electrical efficiency must be between 0 and 1")
        
        if config.get("hEFF") and (config["hEFF"] <= 0 or config["hEFF"] > 1):
            raise HTTPException(status_code=400, detail="Heat efficiency must be between 0 and 1")
    
    except KeyError as e:
        logger.error(f"Missing required parameter: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {str(e)}")

def create_custom_data_row(config: dict) -> pd.DataFrame:
    """Create data row from payload values only"""
    try:
        data = {
            "Country": config["location"],
            "Main_Prod": config.get("product", ""),  # Use empty string if product not provided
            "Plant_Size": config["plant_size"],
            "Plant_Effy": config["plant_effy"],
            "ProcTech": "Custom",
            "Base_Yr": config.get("baseYear", 2023),
            "Cap": config.get("Cap", 0),
            "Yld": config.get("Yld", 0),
            "feedEcontnt": config.get("feedEcontnt", 0),
            "feedCcontnt": config.get("feedCcontnt", 0),
            "Heat_req": config.get("Heat_req", 0),
            "Elect_req": config.get("Elect_req", 0),
            "Feed_Price": config.get("Feed_Price", 0),
            "Fuel_Price": config.get("Fuel_Price", 0),
            "Elect_Price": config.get("Elect_Price", 0),
            "CO2price": config.get("CarbonTAX_value", 0),
            "corpTAX": config.get("corpTAX_value", 0),
            "CAPEX": config.get("CAPEX", 0),
            "OPEX": config.get("OPEX", 0),
            "EcNatGas": config.get("EcNatGas", 0),
            "ngCcontnt": config.get("ngCcontnt", 0),
            "eEFF": config.get("eEFF", 0),
            "hEFF": config.get("hEFF", 0)
        }
        
        logger.info("\nCustom Data Row Created From Payload:")
        for key, value in data.items():
            logger.info(f"{key}: {value}")
        
        return pd.DataFrame([data])
    
    except Exception as e:
        logger.error(f"Error creating custom data row: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating custom data row: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
