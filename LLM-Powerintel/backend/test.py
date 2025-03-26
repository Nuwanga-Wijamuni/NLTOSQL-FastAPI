import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import pandas as pd
from sqlalchemy import create_engine
from fastapi.middleware.cors import CORSMiddleware
import re
from typing import Optional

app = FastAPI(
    title="Energy Analytics Chatbot",
    description="Friendly AI Assistant for Energy Data Analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-001')

# Database configuration
DATABASE_SERVER = 'DESKTOP-CPE1NTJ'
DATABASE_NAME = 'SANDBOX_1107_CLONED_1BT'

class QueryRequest(BaseModel):
    user_query: str

schema_desc = """
               Database Schema:  
1. **MODEL_DATA.PORTFOLIO_ANALYTICS_MAP_CDPC_AND_CF_YEARLY_MV** ({', '.join(dataframes['PORTFOLIO_ANALYTICS_MAP_CDPC_AND_CF_YEARLY_MV'].columns)})  
2. **MODEL_DATA.POWER_PLANT_SUMMARY_MV** ({', '.join(dataframes['POWER_PLANT_SUMMARY_MV'].columns)})  
3. **MODEL_DATA.PORTFOLIO_ANALYTICS_MAP_DETAILS_GEMC_YEARLY_MV** ({', '.join(dataframes['PORTFOLIO_ANALYTICS_MAP_DETAILS_GEMC_YEARLY_MV'].columns)})  
4. **MODEL_DATA.OPERATION_EMISSION_ZONAL_DISPATCH_HOURLY** ({', '.join(dataframes['OPERATION_EMISSION_ZONAL_DISPATCH_HOURLY'].columns)})
5. **MODEL_DATA.Operation_Emision_Powerplant_Dispatch_hourly** ({', '.join(dataframes['Operation_Emision_Powerplant_Dispatch_hourly'].columns)})
6. **MODEL_DATA.PORTFOLIO_POWERPLANT_MAP** ({', '.join(dataframes['MODEL_DATA.PORTFOLIO_POWERPLANT_MAP'].columns)})
7. **MODEL_DATA.POWER_PLANT_DISPATCH_DAILY_FINANCIAL_GEM_MV** ({', '.join(dataframes['POWER_PLANT_DISPATCH_DAILY_FINANCIAL_GEM_MV'].columns)})
8. **MODEL_DATA.POWER_PLANT_FINANCIAL_MONTHLY_PIVOT** ({', '.join(dataframes['POWER_PLANT_FINANCIAL_MONTHLY_PIVOT'].columns)})

---  
### Tables Description (Data Types + Relationships):  

1. **MODEL_DATA.POWER_PLANT_SUMMARY_MV**(

  - **POWER_PLANT_ID** (PK,BIGINT,not null):integer identifier for power plant
  - **ISO_REGION** (VARCHAR(50),null) :Name of the ISO region associated with the power plant
  - **ISO_REGION_ID** (BIGINT,null): Numeric identifier for the ISO region.
  - **POWER_PLANT** (VARCHAR(50),null): power plant name 
  - **OWNER** (VARCHAR(10),null) :Name of ownership entity
  - **ULTIMATE_PARENT**(VARCHAR(100),null) : Name of ultimate parent
  - **ENERGY_AREA** (VARCHAR(50),null) : Designation of the energy area or region.
  - **REPORTING_TYPE** (VARCHAR(50),null): reporting type (unit type from results)
  - **SUMMER_CAPACITY** (FLOAT,null) : Seasonal capacity of the power plant during summer (in MW).
  - **WINTER_CAPACITY** (FLOAT,null) : Seasonal capacity of the power plant during winter (in MW).
  - **FUEL_TYPE** (VARCHAR(50),null) : Type of fuel used by the power plant.
  - **ONLINE_DATE**(DATE,null) : online date of generator
  - **RETIRE_DATE**(DATE,null) : retirement date of generator
 )

 2. **MODEL_DATA.PORTFOLIO_ANALYTICS_MAP_CDPC_AND_CF_YEARLY_MV**(
  -  **YEAR** (DATETIME2,null): Represents the calendar or reporting year for which the data is recorded.
  -  **DATA_TAG_ID** (BIGINT,null):Numeric identifier for the data tag, often tied to the scenario.
  -  **SCENARIO** (VARCHAR(50),null):Describes the operational or market scenario under which the data is generated.
  -  **CARBON_DISPLACEMENT_PER_CAPACITY** (FLOAT,null): Measures the amount of carbon emissions displaced per unit of capacity (e.g., per MW).
  -  **AVERAGE_ANNUAL_CAPACITY_FACTOR ** (FLOAT,null) : indicates the average ratio of actual energy generated versus the potential maximum output over a year.
  -  **POWER_PLANT_NAME ** (VARCHAR(100),null): power plant name
  -  **POWER_PLANT_ID** (BIGINT,null):integer identifier for power plant
  -  **CAPACITY_SUMMER** (FLOAT,null):The available generation capacity during the summer season (typically in MW).
  - **LONGITUDE** (FLOAT,null) :generator location in LATITUDE
  -  **LATITUDE** (FLOAT,null): generator location in LATITUDE
  -  **UNIT_TYPE** (VARCHAR(50),null): Specifies the type of generating unit employed by the power plant.
  -  **PRIMARY_FUEL_TYPE** (VARCHAR(50),null):Indicates the primary fuel source used by the power plant.
 )

 3. **MODEL_DATA.PORTFOLIO_ANALYTICS_MAP_DETAILS_GEMC_YEARLY_MV**(
  -  **LATITUDE** (FLOAT,null): generator location in LATITUDE
  -  **LONGITUDE**(FLOAT,null): generator location in LONGITUDE
  -  **SCENARIO** (VARCHAR(50),null): Describes the operating or market scenario under which the data was generated.
  -  **POWER_PLANT_NAME** (VARCHAR(100),null):power plant name
  -  **UNIT_TYPE** (VARCHAR(50),null): Specifies the type of generating unit used at the power plant.
  -  **PRIMARY_FUEL_TYPE** (VARCHAR(50),null) : Indicates the primary fuel used by the power plant.
  -  **YEAR** (DATE,null): Represents the reporting or calendar year for which the data applies.
  -  **POWER_PLANT_ID** (BIGINT,null) : A unique numeric identifier for each power plant.
  -  **CAPACITY_WINTER** (FLOAT,null): seasonal capacity (MW)
  -  **CAPACITY_SUMMER** (FLOAT,null): seasonal capacity (MW)
  -  **TOTAL_GROSS_ENERGY** (FLOAT,null): The total gross energy output produced by the power plant over the year.
  -  **GEMC_YEARLY** (FLOAT,null): A performance or environmental metric calculated on a yearly basis.
 
)

4. **MODEL_DATA.Operation_Emision_Powerplant_Dispatch_hourly** (
   - **DATA_TAG_ID** (VARCHAR(50),null):A tag that identifies the scenario type associated with the dispatch data.
   - **SCENARIO** (VARCHAR(50),null): Specifies the market or operational scenario under which the dispatch data is generated.
   - **CYCLE** (VARCHAR(50),null): Indicates the market cycle or dispatch timeframe.
   - **ZONE_ID** (VARCHAR(50),null): Represents the unique identifier for the geographical or market zone in which the power plant operates.
   - **CAPACITY_WINTER** (FLOAT,null): The rated generation capacity of the power plant during winter (in MW).
   - **POWER_PLANT_ID** (BIGINT,null): A unique numeric identifier for the power plant.
   - **POWER_PLANT_NAME** (VARCHAR(100),null): The human-readable name of the power plant.
   - **PERIOD** (VARCHAR(50),null):Designates the dispatch period classification.
   - **GENERATION_SUM** (FLOAT,null): The total amount of energy generated during the dispatch period.
   - **CAPACITY_FACTOR** (FLOAT,null): The ratio of actual generation to the maximum possible generation over the period.
   - **CARBON_DISPLACEMENT_SUM** (FLOAT,null): The sum of carbon emissions displaced during the dispatch period.
   - **MER_WAVERAGE** (FLOAT,null): The weighted average of the Market Emission Rate (MER) or a similar environmental/market metric.
   - **LMP_WAVERAGE** (FLOAT,null): The weighted average Locational Marginal Price (LMP) during the dispatch period.
   - **EMS_CO2_SUM** (FLOAT,null): The total CO₂ emissions (or equivalent) recorded by the Energy Management System (EMS) for the period.
   - **DT_TIMESTAMP** (DATETIME2,null) : The exact date and time stamp for the dispatch record.
   - **DATE_TIME_KEY (NUMERIC(38,0),null) : A derived numeric key based on DT_TIMESTAMP, formatted as YYYYMMDDHH.
)

5. **MODEL_DATA.OPERATION_EMISSION_ZONAL_DISPATCH_HOURLY**(
   -  **DATA_TAG_ID** (BIGINT, null):A tag that identifies the scenario type associated with the dispatch data.
   -  **SCENARIO** (VARCHAR(50), null):Specifies the market or operational scenario under which the dispatch data is generated.
   -  **POWER_PLANT_ID** (BIGINT, null):A unique numeric identifier for the power plant.
   -  **POWER_PLANT_NAME** (VARCHAR(100),null):The human-readable name of the power plant.
   -  **ZONE_ID**(BIGINT,null):
   -  **DT_TIMESTAMP**(datetime2(7),null):The exact date and time stamp for the dispatch record.
   -  **CYCLE**(VARCHAR(50),null):Indicates the market or operational cycle relevant to the dispatch data.
   -  **PERIOD**(VARCHAR(50),null):Designates the dispatch period classification.
   -  **LMP**(FLOAT,null):Locational Marginal Price, representing the cost of supplying the next unit of electricity at a specific location.
   -  **MER**(FLOAT,null):Market Emission Rate or a similar market-based environmental metric.
   -  **DATE_TIME_KEY**(FLOAT,null):A derived numeric key that compactly represents the date and time of the record.

)

6. **MODEL_DATA.PORTFOLIO_POWERPLANT_MAP**(
   - **PORTFOLIO_ID**(INT):represents a unique identifier assigned to a specific portfolio
   - **POWER_PLANT_ID**(INT):A unique numeric identifier for each power plant.
   - **IS_DELETED**(VARCHAR(10)): Deleted status 
)

7. **MODEL_DATA.POWER_PLANT_DISPATCH_DAILY_FINANCIAL_GEM_MV**
(
   - **DATA_TAG_ID** (BIGINT, null): A tag that identifies the scenario type associated with the dispatch data.
   - **SCENARIO** (VARCHAR(50), null): Specifies the market or operational scenario under which the dispatch data is generated.
   - **POWER_PLANT_ID** (BIGINT, null): A unique numeric identifier for the power plant.
   - **POWER_PLANT_NAME** (VARCHAR(100), null): The human-readable name of the power plant.
   - **DT_TIMESTAMP** (DATE, null): The exact date for the dispatch record, representing daily financial performance.
   - **GROSS_ENERGY_MARGIN_SUM** (FLOAT, null): The total gross energy margin calculated for the power plant on the given date.
   - **DATE_TIME_KEY** (BIGINT, null): A derived numeric key that compactly represents the date of the record in YYYYMMDD format.
)

8. **MODEL_DATA.POWER_PLANT_FINANCIAL_MONTHLY_PIVOT**(
   - **DATE_TIME_KEY** (INT, NOT NULL): A numeric key representing the month or date in YYYYMMDD format, used to compactly identify the record’s time period.
   - **DT_TIMESTAMP** (DATE, NULL): The specific date (or representative date) for the monthly financial record, typically set to the first day of the month or any relevant day within that month.
   - **METRIC_TYPE** (VARCHAR(50), NULL): Indicates the type of financial or performance metric being recorded (e.g., Revenue, Cost, Profit).
   - **POWER_PLANT_ID** (INT, NULL): A unique numeric identifier for the power plant associated with the financial data.
   - **POWER_PLANT_NAME** (VARCHAR(100), NULL): The human-readable name of the power plant (e.g., Plant A, Plant B).
   - **POWER_PLANT_TYPE** (VARCHAR(50), NULL): Categorizes the plant by its generation technology or type (e.g., Thermal, Nuclear, Solar).
   - **PRODUCT_TYPE**  (VARCHAR(50), NULL): Specifies the type of product or market segment for which the financial metric is calculated (e.g., Energy, Capacity, Ancillary).
   - **SCENARIO** (VARCHAR(50), NULL): Describes the market or operational scenario under which these monthly financials were generated (e.g., Base Case, High Gas Price).
   - **TRANSACTION_CATEGORY** (VARCHAR(50), NULL): Identifies whether the transaction is a Sale, Purchase, or another relevant financial category.
   - **TRANSACTION_TYPE** (VARCHAR(50), NULL): Provides more detail on the nature of the transaction (e.g., Wholesale, Retail, Spot Market).
   - **VALUE** (FLOAT, NULL): The numerical value of the specified financial metric (e.g., total monthly revenue, cost, or profit) for the given power plant and date.

)

- **STRICTLY** return "out of context question" if:
  - The question requires columns/tables not listed in the schema.
  - The question cannot be answered with the provided tables/relationships.
  - Return "out of context question" if columns/tables are missing in the schema.
  - Return "Your Data type is wrong" for invalid values (e.g., non-numeric years like "XY"; valid examples: 1998, 2000, 2025).


### Choosing Tables:  

 - **Carbon Displacement per Capacity and Capacity Factor:**  
  Use the table **MODEL_DATA.PORTFOLIO_ANALYTICS_MAP_CDPC_AND_CF_YEARLY_MV**.

- **Power Plant Summary (Portfolio & Individual):**  
  Use the table **MODEL_DATA.POWER_PLANT_SUMMARY_MV**.

- **Gross Energy Margin per Capacity:**  
  Use the table **MODEL_DATA.PORTFOLIO_ANALYTICS_MAP_DETAILS_GEMC_YEARLY_MV**.

- **Hourly Power Plant Dispatch & Emissions:**
  Use the table **MODEL_DATA.OPERATION_EMISSION_POWERPLANT_DISPATCH_HOURLY**, which includes key fields such as 
  DATA_TAG_ID, SCENARIO, CYCLE, ZONE_ID, POWER_PLANT_ID, POWER_PLANT_NAME, PERIOD, GENERATION_SUM, CAPACITY_FACTOR, 
  CARBON_DISPLACEMENT_SUM, LMP_WAVERAGE, MER_WAVERAGE, EMS_CO2_SUM, and DT_TIMESTAMP.

- **Zonal Dispatch & Emissions:**
  Use the table **MODEL_DATA.OPERATION_EMISSION_ZONAL_DISPATCH_HOURLY**, which provides zonal-level dispatch metrics, including DATA_TAG_ID, SCENARIO, 
  POWER_PLANT_ID, POWER_PLANT_NAME, ZONE_ID, DT_TIMESTAMP, CYCLE, PERIOD, LMP, MER, and DATE_TIME_KEY.

- *Portfolio and Power Plant**
  Use table **MODEL_DATA.PORTFOLIO_POWERPLANT_MAP** which user provides about portfolio

- **Finacial and Gross Energy Margin**
  Use table **POWER_PLANT_DISPATCH_DAILY_FINANCIAL_GEM_MV** which user provides about Finacial

- **Finacial and Portfolio Transaction **
  Use table **POWER_PLANT_FINANCIAL_MONTHLY_PIVOT** which user provides about Finacial
  
###Instructions:
- Your task is to **only generate the SQL query** for the user's question **without any explanation**.
- Carefully validate column names and table relationships using the schema above.
- Genarate sql queries for  Microsoft SQL Server
- There is no **PAMDG YEAR** there is a **YEAR** Column



Input: "Display the complete information for the power plant with POWER_PLANT_ID equal to 1073"
  Output: ```sql
SELECT
    PPSM.POWER_PLANT_ID,
    PPSM.ISO_REGION,
    PPSM.ISO_REGION_ID,
    PPSM.POWER_PLANT,
    PPSM.OWNER,
    PPSM.ULTIMATE_PARENT,
    PPSM.ENERGY_AREA,
    PPSM.REPORTING_TYPE,
    PPSM.SUMMER_CAPACITY,
    PPSM.WINTER_CAPACITY,
    PPSM.FUEL_TYPE,
    PPSM.ONLINE_DATE,
    PPSM.RETIRE_DATE
FROM
    MODEL_DATA.POWER_PLANT_SUMMARY_MV PPSM
WHERE
    PPSM.POWER_PLANT_ID = 1073;

Input: "i need to see all dATA from Emision_Powerplant_Dispatch_hourly"
  Output: ```sql
SELECT OEPDH.DATA_TAG_ID, 
OEPDH.SCENARIO, 
OEPDH.CYCLE, 
OEPDH.ZONE_ID, 
OEPDH.CAPACITY_WINTER, 
OEPDH.POWER_PLANT_ID, 
OEPDH.POWER_PLANT_NAME, 
OEPDH.PERIOD, 
OEPDH.GENERATION_SUM, 
OEPDH.CAPACITY_FACTOR, 
OEPDH.CARBON_DISPLACEMENT_SUM, 
OEPDH.MER_WAVERAGE, OEPDH.LMP_WAVERAGE, 
OEPDH.EMS_CO2_SUM, OEPDH.DT_TIMESTAMP, 
OEPDH.DATE_TIME_KEY 
FROM MODEL_DATA.Operation_Emision_Powerplant_Dispatch_hourly OEPDH;
"""
def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame"""
    conn_str = f'mssql+pyodbc://{DATABASE_SERVER}/{DATABASE_NAME}?driver=ODBC+Driver+17+for+SQL+Server'
    engine = create_engine(conn_str)
    try:
        return pd.read_sql(sql_query, engine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        engine.dispose()

def get_df_behavior(df: pd.DataFrame) -> dict:
    """Generate comprehensive DataFrame analysis"""
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "unique_values": {col: df[col].nunique() 
                        for col in df.select_dtypes(include=['object'])},
        "sample_data": df.head(10).to_dict(orient='records')
    }

def detect_conversational_intent(query: str) -> Optional[str]:
    """Detect non-analytical user intents with expanded patterns"""
    query = query.lower().strip()
    
    greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon']
    gratitude_keywords = ['thanks', 'thank you', 'appreciate']
    help_keywords = ['help', 'what can you do', 'support', 'assist']
    farewell_keywords = ['bye', 'goodbye', 'see you', 'exit']
    
    if any(keyword in query for keyword in greeting_keywords):
        return "greeting"
    if any(keyword in query for keyword in gratitude_keywords):
        return "gratitude"
    if any(keyword in query for keyword in help_keywords):
        return "help"
    if any(keyword in query for keyword in farewell_keywords):
        return "farewell"
    
    return None

def create_friendly_response(intent: str) -> dict:
    """Create engaging responses for different intents"""
    responses = {
        "greeting": {
            "response": "🌞 Hi there! I'm your Energy Data Assistant. "
                       "I can help you analyze power plant operations, emissions, and financial data. "
                       "How can I assist you today?",
            "suggestions": [
                "Show me carbon displacement trends",
                "Compare summer capacities",
                "What's the latest financial data?"
            ]
        },
        "gratitude": {
            "response": "🤝 You're welcome! Let me know if you need any other analyses or visualizations.",
            "suggestions": [
                "Generate a monthly report",
                "Analyze capacity factors",
                "Compare fuel type efficiencies"
            ]
        },
        "help": {
            "response": "🔍 I specialize in energy data analysis. Here's what I can help with:",
            "suggestions": [
                "Power plant performance metrics",
                "Emissions analysis by region",
                "Financial performance trends",
                "Capacity factor calculations",
                "Scenario comparisons"
            ]
        },
        "farewell": {
            "response": "👋 Goodbye! Feel free to reach out if you have more data questions later.",
            "suggestions": []
        }
    }
    return responses.get(intent, {"response": "", "suggestions": []})

def format_data_preview(df: pd.DataFrame) -> str:
    """Create user-friendly data preview"""
    preview = f"📊 Found {len(df)} rows:\n"
    preview += "\n".join([f"- {col}: {df[col].dtype}" for col in df.columns[:3]])
    if len(df.columns) > 3:
        preview += "\n- ...and {} more columns".format(len(df.columns)-3)
    return preview

@app.post("/chat") #this is the endpoint
async def chat_endpoint(request: QueryRequest):
    try:
        # Check for conversational intents first
        intent = detect_conversational_intent(request.user_query)
        if intent:
            response_data = create_friendly_response(intent)
            response_data.update({
                "sql_query": None,
                "results": None,
                "error": None
            })
            return response_data

        # Proceed with SQL generation for analytical queries
        full_prompt = f"{schema_desc}\n\nUser Query: {request.user_query}"
        
        # Generate SQL using Gemini
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.0, "max_output_tokens": 1024}
        )
        
        sql_response = response.text

        # Handle out of context questions
        if "out of context question" in sql_response.lower():
            return {
                "response": "❌ I'm sorry, I can only answer questions about energy data. "
                           "My expertise includes:\n- Power plant operations\n- Emissions analysis\n- Financial metrics\n"
                           "Could you rephrase your question?",
                "sql_query": None,
                "results": None,
                "error": "Out of context question",
                "suggestions": [
                    "Show top performing plants",
                    "Compare summer/winter capacities",
                    "Analyze recent emissions trends"
                ]
            }

        # Clean SQL response
        sql_query = sql_response.strip().strip('```').lstrip('sql').strip()
        
        # Execute and analyze results
        df = execute_sql_query(sql_query)
        df_analysis = get_df_behavior(df)
        
        # Create user-friendly summary
        result_summary = (
            f"✅ Success! Analyzed {len(df)} records\n"
            f"🔑 Main columns: {', '.join(df.columns[:3])}" + 
            ("..." if len(df.columns)>3 else "")
        )

        return {
            "response": result_summary,
            "sql_query": sql_response,
            "results": df.head(20).to_dict(orient='records'),
            "df_behavior": df_analysis,
            "error": None,
            "suggestions": [
                "Visualize this data",
                "Compare with previous period",
                "Calculate derived metrics"
            ]
        }

    except HTTPException as he:
        return {
            "response": "⚠️ Oops! There was an issue processing your query",
            "sql_query": sql_response if 'sql_response' in locals() else None,
            "results": None,
            "error": he.detail,
            "suggestions": [
                "Check power plant IDs",
                "Verify date formats",
                "Review scenario names"
            ]
        }
    except Exception as e:
        return {
            "response": "❌ Unexpected error occurred. Our team has been notified",
            "sql_query": None,
            "results": None,
            "error": str(e),
            "suggestions": [
                "Try a different question",
                "Simplify your query",
                "Check connection settings"
            ]
        }

# Keep execute_sql_query and get_df_behavior functions same as original

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)