from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from SmartApi import SmartConnect
import pyotp
from logzero import logger

# Initialize FastAPI app
app = FastAPI()

# SmartAPI credentials (replace with your actual credentials)
API_KEY = 'SkNAfLZR'
USERNAME = 'AAAA386357'
PASSWORD = 9973
TOKEN = 'FX4QYOPX4FIMVR2PYJUOQ5X6OY'  # Used to generate TOTP

# Initialize SmartAPI client
smartApi = SmartConnect(api_key=API_KEY)

try:
    # Generate TOTP based on token
    totp = pyotp.TOTP(TOKEN).now()
except Exception as e:
    logger.error("Invalid Token: The provided token is not valid.")
    raise e

# Models for various request data
class OrderRequest(BaseModel):
    tradingsymbol: str
    symboltoken: str
    transactiontype: str  # "BUY" or "SELL"
    ordertype: str  # "MARKET", "LIMIT", etc.
    producttype: str  # "INTRADAY" or "DELIVERY"
    price: float
    quantity: int


class GTTRequest(BaseModel):
    tradingsymbol: str
    symboltoken: str
    producttype: str  # "MARGIN"
    transactiontype: str  # "BUY" or "SELL"
    price: float
    qty: int
    triggerprice: float
    timeperiod: int  # e.g., 365


@app.get("/")
async def root():
    return {"message": "Welcome to Algo Trading using SmartAPI!"}


@app.post("/login")
async def login():
    """Login to SmartAPI and generate tokens"""
    try:
        data = smartApi.generateSession(USERNAME, PASSWORD, totp)

        if data['status'] == False:
            logger.error(data)
            raise HTTPException(status_code=401, detail="Login failed")
        
        # Store auth tokens globally (in memory for simplicity)
        global authToken, refreshToken, feedToken
        authToken = data['data']['jwtToken']
        refreshToken = data['data']['refreshToken']
        feedToken = smartApi.getfeedToken()

        return {"status": "success", "message": "Login successful", "authToken": authToken}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/place-order")
async def place_order(order: OrderRequest):
    """Place an order using SmartAPI"""
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": order.tradingsymbol,
            "symboltoken": order.symboltoken,
            "transactiontype": order.transactiontype,
            "exchange": "NSE",  # or "BSE" based on the stock
            "ordertype": order.ordertype,
            "producttype": order.producttype,
            "duration": "DAY",
            "price": order.price,
            "quantity": order.quantity,
        }
        response = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {response}")

        return {"status": "success", "message": "Order placed successfully", "order_id": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {e}")


@app.post("/gtt-rule")
async def create_gtt_rule(gtt: GTTRequest):
    """Create a GTT rule"""
    try:
        gttCreateParams = {
            "tradingsymbol": gtt.tradingsymbol,
            "symboltoken": gtt.symboltoken,
            "exchange": "NSE",  # or "BSE"
            "producttype": gtt.producttype,
            "transactiontype": gtt.transactiontype,
            "price": gtt.price,
            "qty": gtt.qty,
            "disclosedqty": gtt.qty,
            "triggerprice": gtt.triggerprice,
            "timeperiod": gtt.timeperiod
        }
        rule_id = smartApi.gttCreateRule(gttCreateParams)
        return {"status": "success", "message": "GTT rule created", "rule_id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GTT Rule creation failed: {e}")


@app.get("/gtt-list")
async def get_gtt_list():
    """Fetch GTT rule list"""
    try:
        status = ["FORALL"]  # Should be a list
        page = 1
        count = 10
        gtt_list = smartApi.gttLists(status, page, count)
        return {"status": "success", "gtt_list": gtt_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GTT Rule List fetch failed: {e}")


@app.get("/historical-data")
async def get_historical_data():
    """Fetch historical data"""
    try:
        historicParam = {
            "exchange": "NSE",
            "symboltoken": "3045",
            "interval": "ONE_MINUTE",
            "fromdate": "2021-02-08 09:00",  # Example date
            "todate": "2021-02-08 09:16"
        }
        data = smartApi.getCandleData(historicParam)
        return {"status": "success", "historical_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Historical data fetch failed: {e}")


@app.post("/logout")
async def logout():
    """Logout from SmartAPI"""
    try:
        logout_response = smartApi.terminateSession(USERNAME)
        return {"status": "success", "message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {e}")


# Running the FastAPI app:
# You can start the server with the command:
# uvicorn filename:app --reload
