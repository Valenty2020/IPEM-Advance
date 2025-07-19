from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import uvicorn
from originalmodel import Analytics_Model2

app = FastAPI(
    title="Project Economics Model API",
    description="API for chemical plant economics analysis - Strict Payload Only",
    version="2.0.0"
)

class AnalysisRequest(BaseModel):
    # Required parameters
    location: str
    plant_effy: str
    plant_size: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
    
    # Optional parameters
    product: Optional[str] = None
    
    # Technical parameters with defaults
    operating_prd: int = 20
    util_operating_first: float = 0.75
    util_operating_second: float = 0.90
    util_operating_third: float = 0.90
    infl: float = 0.02
    RR: float = 0.10
    IRR: float = 0.10
    construction_prd: int = 3
    capex_spread: List[float] = [0.4, 0.3, 0.3]
    shrDebt_value: float = 0.60
    baseYear: int = 2023
    ownerCost: float = 0.0
    corpTAX_value: float = 0.25
    Feed_Price: float = 0.0
    Fuel_Price: float = 0.0
    Elect_Price: float = 0.0
    CarbonTAX_value: float = 0.0
    credit_value: float = 0.0
    CAPEX: float = 0.0
    OPEX: float = 0.0
    PRIcoef: float = 1.0
    CONcoef: float = 1.0
    EcNatGas: float = 0.0
    ngCcontnt: float = 0.0
    eEFF: float = 0.0
    hEFF: float = 0.0
    Cap: float = 0.0
    Yld: float = 0.0
    feedEcontnt: float = 0.0
    Heat_req: float = 0.0
    Elect_req: float = 0.0
    feedCcontnt: float = 0.0

# Global variables for data
project_datas = None
multipliers = None

@app.on_event("startup")
async def startup_event():
    """Load required data files"""
    global project_datas, multipliers
    try:
        project_datas = pd.read_csv("./project_data.csv")
        multipliers = pd.read_csv("./sectorwise_multipliers.csv")
        print("Data files loaded successfully")
    except Exception as e:
        print(f"Error loading data files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading data files: {str(e)}")

@app.post("/analyze", response_model=List[dict])
async def run_analysis(request: AnalysisRequest):
    """Run economic analysis using the provided payload values"""
    try:
        config = request.dict()
        print("\n=== PAYLOAD VALUES RECEIVED ===")
        for key, value in config.items():
            print(f"{key}: {value}")
        
        validate_parameters(config)
        custom_data = create_custom_data_row(config)
        
        print("Starting analysis...")
        results = Analytics_Model2(
            multiplier=multipliers,
            project_data=custom_data,
            location=config["location"],
            product=config.get("product", ""),
            plant_mode=config["plant_mode"],
            fund_mode=config["fund_mode"],
            opex_mode=config["opex_mode"],
            plant_size=config["plant_size"],
            plant_effy=config["plant_effy"],
            carbon_value=config["carbon_value"]
        )
        
        print("Analysis completed successfully")
        return results.to_dict(orient='records')
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error running analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

def validate_parameters(config: dict):
    """Validate payload parameters"""
    if config["location"] not in project_datas['Country'].unique():
        raise HTTPException(status_code=400, detail="Invalid location")
    
    if config.get("product") and config["product"] not in project_datas['Main_Prod'].unique():
        raise HTTPException(status_code=400, detail="Invalid product")
    
    if config["plant_mode"] not in ["Green", "Brown"]:
        raise HTTPException(status_code=400, detail="plant_mode must be 'Green' or 'Brown'")
    
    if config["fund_mode"] not in ["Debt", "Equity", "Mixed"]:
        raise HTTPException(status_code=400, detail="Invalid fund_mode")
    
    if config["opex_mode"] not in ["Inflated", "Uninflated"]:
        raise HTTPException(status_code=400, detail="Invalid opex_mode")
    
    if config["carbon_value"] not in ["Yes", "No"]:
        raise HTTPException(status_code=400, detail="Invalid carbon_value")
    
    if config["plant_size"] not in ["Large", "Small"]:
        raise HTTPException(status_code=400, detail="Invalid plant_size")
    
    if config["plant_effy"] not in ["High", "Low"]:
        raise HTTPException(status_code=400, detail="Invalid plant_effy")

def create_custom_data_row(config: dict) -> pd.DataFrame:
    """Create data row from payload values"""
    data = {
        "Country": config["location"],
        "Main_Prod": config.get("product", ""),
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
    
    print("\nCustom Data Row Created:")
    for key, value in data.items():
        print(f"{key}: {value}")
    
    return pd.DataFrame([data])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
